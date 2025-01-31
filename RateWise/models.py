import logging
from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count, StdDev
from django.contrib.auth.models import User
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger('django')
cache_timeout = getattr(settings, "CACHE_TIMEOUT", 300)


class Document(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_average_score(self):
        cache_key = f"document_{self.id}_average_score"
        avg_score = cache.get(cache_key)
        if avg_score is None:
            avg_score = self.rating_set.aggregate(average=Avg('score'))['average'] or 0.0
            logger.info(f"caching average score for {self.id} by value {avg_score}")
            cache.set(cache_key, avg_score, timeout=cache_timeout)

        return avg_score

    def calculate_standard_deviation(self):
        cache_key = f"document_{self.id}_std_dev"
        std_dev = cache.get(cache_key)
        if std_dev is None:
            std_dev = self.rating_set.aggregate(std_dev=StdDev('score'))['std_dev'] or 0.0
            logger.info(f"caching std deviation score for {self.id} by value {std_dev}")
            cache.set(cache_key, std_dev, timeout=cache_timeout)

        return std_dev

    def number_of_ratings(self):
        cache_key = f"document_{self.id}_num_ratings"
        num_ratings = cache.get(cache_key)

        if num_ratings is None:
            num_ratings = self.rating_set.aggregate(count=Count('id'))['count'] or 0
            logger.info(f"Caching number of ratings for {self.id}: {num_ratings}")
            cache.set(cache_key, num_ratings, timeout=cache_timeout)

        return num_ratings

    def update_cache_on_rating_change(self, new_score=None, old_score=None, is_delete=False):
        avg_cache_key = f"document_{self.id}_average_score"
        std_dev_cache_key = f"document_{self.id}_std_dev"
        num_ratings_cache_key = f"document_{self.id}_num_ratings"

        avg_score = cache.get(avg_cache_key)
        num_ratings = cache.get(num_ratings_cache_key)

        if avg_score is None or num_ratings is None:
            self.clear_cache()
            return

        if is_delete:
            if num_ratings > 1:
                new_avg_score = ((avg_score * num_ratings) - old_score) / (num_ratings - 1)
            else:
                new_avg_score = 0.0
            num_ratings -= 1
        elif old_score is not None:
            new_avg_score = ((avg_score * num_ratings) - old_score + new_score) / num_ratings
        else:
            new_avg_score = ((avg_score * num_ratings) + new_score) / (num_ratings + 1)
            num_ratings += 1

        logger.info(f"Updating cache for Document {self.id}: New Avg Score: {new_avg_score}, Num Ratings: {num_ratings}")
        cache.set(avg_cache_key, new_avg_score, timeout=cache_timeout)
        cache.set(num_ratings_cache_key, num_ratings, timeout=cache_timeout)

        cache.delete(std_dev_cache_key)

    def clear_cache(self):
        logger.info("Document stat cache has been deleted")
        cache.delete(f"document_{self.id}_average_score")
        cache.delete(f"document_{self.id}_std_dev")
        cache.delete(f"document_{self.id}_num_ratings")

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

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk:
                old_rating = Rating.objects.get(pk=self.pk)
                super().save(*args, **kwargs)
                # update someones rating
                self.document.update_cache_on_rating_change(new_score=self.score, old_score=old_rating.score)
            else:
                super().save(*args, **kwargs)
                self.document.update_cache_on_rating_change(new_score=self.score)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            old_score = self.score
            super().delete(*args, **kwargs)
            self.document.update_cache_on_rating_change(old_score=old_score, is_delete=True)

    def __str__(self):
        return f"{self.user} rated {self.document} - {self.score}/5"
