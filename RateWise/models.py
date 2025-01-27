from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count, StdDev


class Document(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    average_score = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    standard_deviation = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    number_of_ratings = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_rating_statistics(self):
        stats = self.ratings.aggregate(
            avg_score=Avg('score'),
            std_dev=StdDev('score'),
            count=Count('id'),
        )
        self.average_score = stats['avg_score'] or 0.0
        self.standard_deviation = stats['std_dev'] or 0.0
        self.number_of_ratings = stats['count'] or 0
        self.save()

    def __str__(self):
        return self.title


class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
