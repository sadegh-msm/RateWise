from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count, StdDev
from django.contrib.auth.models import User


class Document(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_average_score(self):
        return self.rating_set.aggregate(average=Avg('score'))['average'] or 0.0

    def calculate_standard_deviation(self):
        return self.rating_set.aggregate(std_dev=StdDev('score'))['std_dev'] or 0.0

    def number_of_ratings(self):
        return self.rating_set.aggregate(count=Count('id'))['count'] or 0

    def __str__(self):
        return self.title


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'document')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['document']),
        ]

    def __str__(self):
        return f"{self.user} rated {self.document} - {self.score}/5"
