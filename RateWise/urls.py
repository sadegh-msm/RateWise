from django.urls import path

from .views import DocumentListView, DocumentCreateView, RateDocumentView, UserCreateView

urlpatterns = [
    path('docs/', DocumentListView.as_view(), name='document-list'),
    path('docs/create/', DocumentCreateView.as_view(), name='document-create'),
    path('ratedoc/', RateDocumentView.as_view(), name='rate-document'),
    path('user/', UserCreateView.as_view(), name='create_user'),
]
