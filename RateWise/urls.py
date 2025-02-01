from django.urls import path
from .views import DocumentListView, DocumentCreateView, RateDocumentView, UserCreateView, DocumentStatsView

urlpatterns = [
    path('docs/', DocumentListView.as_view(), name='document-list'),
    path('docs/create/', DocumentCreateView.as_view(), name='document-create'),
    path('ratedoc/', RateDocumentView.as_view(), name='rate-document'),
    path('docs/<int:document_id>/stats/', DocumentStatsView.as_view(), name='document-stats'),
    path('user/', UserCreateView.as_view(), name='create_user'),
]
