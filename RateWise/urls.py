from django.urls import path
from .views import ArticleListView, ArticleCreateView, RateArticleView

urlpatterns = [
    path('docs/', ArticleListView.as_view(), name='document-list'),
    path('docs/create/', ArticleCreateView.as_view(), name='document-create'),
    path('ratedoc/', RateArticleView.as_view(), name='rate-document'),
]

