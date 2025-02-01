from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Document, Rating
from rest_framework.authtoken.models import Token


class DocumentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_list_documents(self):
        url = "/api/docs/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_document(self):
        data = {"title": "Test Document", "text": "This is a sample document"}
        url = "/api/docs/create/"
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_rate_document(self):
        document = Document.objects.create(title="Test Document", text="Sample text")
        url = "/api/ratedoc/"
        data = {'document': document.id, 'score': 4}
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Rating.objects.count(), 1)

    def test_rate_document_invalid_score(self):
        document = Document.objects.create(title="Test Document", text="Sample text")
        url = "/api/ratedoc/"
        data = {'document': document.id, 'score': 10}  # Invalid score
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_rating(self):
        document = Document.objects.create(title="Test Document", text="Sample text")
        rating = Rating.objects.create(user=self.user, document=document, score=3)
        url = "/api/ratedoc/"
        data = {'document': document.id, 'score': 5}  # Update score
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data)
        rating.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(rating.score, 5)

    def test_rate_document_unauthenticated(self):
        self.client.force_authenticate(user=None)
        document = Document.objects.create(title="Test Document", text="Sample text")
        url = "/api/ratedoc/"
        data = {'document': document.id, 'score': 4}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_document_stats(self):
        document = Document.objects.create(title="Test Document", text="Sample text")
        url = f"/api/docs/{document.id}/stats/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_document_stats_no_ratings(self):
        document = Document.objects.create(title="Test Document", text="Sample text")
        url = f"/api/docs/{document.id}/stats/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["average_score"], 0.0)
        self.assertEqual(response.data["number_of_ratings"], 0)

    def test_user_creation(self):
        url = "/api/user/"
        data = {'username': 'newuser', 'password': 'newpass'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)

    def test_delete_rating(self):
        document = Document.objects.create(title="Test Document", text="Sample text")
        rating = Rating.objects.create(user=self.user, document=document, score=3)
        rating_id = rating.id
        rating.delete()
        self.assertFalse(Rating.objects.filter(id=rating_id).exists())
