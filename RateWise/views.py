from .models import Document, Rating
from .serializers import DocumentSerializer, RatingSerializer, DocumentCreateSerializer, UserSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics, status
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.http import JsonResponse
from django.db import connection
import logging
import amqp
import json

logger = logging.getLogger('django')
cache_timeout = getattr(settings, "CACHE_TIMEOUT", 300)
rabbit_host = getattr(settings, "RABBIT_HOST", "rabbitmq")


class DocumentListView(generics.ListAPIView):
    queryset = Document.objects.all().order_by('id')
    serializer_class = DocumentSerializer

    def get_queryset(self):
        cached_documents = cache.get('documents')
        if not cached_documents:
            logger.info("did not hit cache")
            documents = Document.objects.all().order_by('id')
            cached_documents = DocumentSerializer(documents, many=True).data
            cache.set('documents', cached_documents, timeout=cache_timeout)

        return cached_documents


class DocumentCreateView(generics.CreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentCreateSerializer


class RateDocumentView(generics.CreateAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        document_id = request.data.get('document')
        score = request.data.get('score')

        if not 1 <= int(score) <= 5:
            return Response({'error': 'Score must be between 1 and 5'}, status=status.HTTP_400_BAD_REQUEST)

        document = get_object_or_404(Document, pk=document_id)

        with transaction.atomic():
            rating, _ = Rating.objects.update_or_create(
                user=user,
                document=document,
                defaults={'score': int(score)}
            )

        self.enqueue_rating(user.id, document.id, int(score), rating.id)
        return Response({'message': 'Rated successfully'}, status=status.HTTP_200_OK)

    def enqueue_rating(self, user_id, document_id, score, rating_id):
        connection = amqp.Connection(host=rabbit_host)
        channel = connection.channel()

        channel.queue_declare(queue='document_ratings', durable=True)

        message = json.dumps({'user_id': user_id, 'document_id': document_id, 'score': score, 'rating_id': rating_id})
        channel.basic_publish(amqp.Message(message, delivery_mode=2), routing_key='document_ratings')

        connection.close()


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class DocumentStatsView(generics.CreateAPIView):
    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id)

        data = {
            "document": document.title,
            "average_score": document.calculate_average_score(),
            "standard_deviation": document.calculate_standard_deviation(),
            "number_of_ratings": document.number_of_ratings(),
        }

        return Response(data, status=status.HTTP_200_OK)


def liveness_check(request):
    return JsonResponse({"status": "alive"}, status=200)


def readiness_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")  # Simple DB check
        return JsonResponse({"status": "ready"}, status=200)
    except Exception:
        return JsonResponse({"status": "unhealthy"}, status=500)
