from .models import Document, Rating
from .serializers import DocumentSerializer, RatingSerializer, DocumentCreateSerializer, UserSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics, status
from django.core.cache import cache
from django.db import transaction
# from articles.redis_queue import enqueue_article_id
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
import logging

logger = logging.getLogger('django')


class DocumentListView(generics.ListAPIView):
    queryset = Document.objects.all().order_by('id')
    serializer_class = DocumentSerializer

    def get_queryset(self):
        cached_documents = cache.get('documents')
        if not cached_documents:
            logger.info("did not hit cache")
            documents = Document.objects.all().order_by('id')
            cached_documents = DocumentSerializer(documents, many=True).data
            cache.set('documents', cached_documents, timeout=60)

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

        # enqueue_article_id(article.id)

        return Response({'message': 'Rated successfully'}, status=status.HTTP_200_OK)


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
