from celery import shared_task
from .models import Document, Rating
from django.conf import settings
from django.core.cache import cache
import logging
import amqp
import json
import time

logger = logging.getLogger("django")
cache_timeout = getattr(settings, "CACHE_TIMEOUT", 300)
batch_size = getattr(settings, "BATCH_SIZE", 1000)
outlier_process_treshold = getattr(settings, "OUTLIER_PROCESS_THRESHOLD", 600)
outlier_cache_key = "outlier_ratings"
rabbit_host = getattr(settings, "RABBIT_HOST", "rabbitmq")
batch_limit_outlier = getattr(settings, "BATCH_LIMIT_OUTLIER", 10)


def store_outlier(doc_id, rating_id):
    outliers = cache.get(outlier_cache_key, [])
    outliers.append({
        "document_id": doc_id,
        "rating_id": rating_id,
        "timestamp": time.time()
    })
    cache.set(outlier_cache_key, outliers, timeout=cache_timeout)
    logger.info(f"Stored rating {rating_id} as potential outlier for document {doc_id}")


@shared_task
def process_outliers():
    logger.info("Processing stored outliers")

    outliers = cache.get(outlier_cache_key, [])
    remainig_outliers = []
    processed_count = 0

    for outlier in outliers:
        try:
            time_in_cache = time.time() - outlier["timestamp"]

            if time_in_cache >= outlier_process_treshold and processed_count < batch_limit_outlier:
                rating = Rating.objects.get(pk=outlier["rating_id"])
                document = Document.objects.get(pk=outlier["document_id"])

                rating.is_outlier = True
                rating.save()
                update_doc_stats.apply_async(args=(document.id,))
                processed_count += 1
                logger.info(f"Processed outlier {outlier['rating_id']} for document {outlier['document_id']}")
            else:
                remainig_outliers.append(outlier)  # Keep it in Redis if time not reached
                logger.info(f"Outlier rating cant be processed due time left  by id: {outlier['rating_id']}")

        except (Rating.DoesNotExist, Document.DoesNotExist):
            pass

    cache.set(outlier_cache_key, remainig_outliers, timeout=cache_timeout)


@shared_task
def process_doc():
    logger.info("starting processing documents")
    connection = amqp.Connection(host=rabbit_host)
    channel = connection.channel()

    channel.queue_declare(queue='document_ratings', durable=True)

    messages = []
    for _ in range(batch_size):
        msg = channel.basic_get(queue='document_ratings', no_ack=True)
        if msg:
            messages.append(json.loads(msg.body))
        else:
            break

    connection.close()

    doc_ids_to_update = set()

    for msg in messages:
        doc_id = msg["document_id"]
        rating_id = msg["rating_id"]

        try:
            rating = Rating.objects.get(pk=rating_id)
            document = Document.objects.get(pk=doc_id)

            if document.detect_outlier(rating.score):
                logger.info(f'Put rating in outlier with id {rating_id}')
                store_outlier(doc_id, rating_id)
            else:
                logger.info(f'This rating is not outlier with id {rating_id}')
                document.update_cache_on_rating_change(new_score=rating.score)
                doc_ids_to_update.add(doc_id)

        except (Rating.DoesNotExist, Document.DoesNotExist):
            logger.error(f"Invalid document {doc_id} or rating {rating_id}")

    for doc_id in doc_ids_to_update:
        update_doc_stats.apply_async(args=(doc_id,))


@shared_task
def update_doc_stats(doc_id):
    logger.info(f"Updating document stats for {doc_id}")
    try:
        document = Document.objects.get(pk=doc_id)
        avg_score = document.calculate_average_score()
        std_dev = document.calculate_standard_deviation()
        num_ratings = document.number_of_ratings()

        document.average_score = avg_score
        document.standard_deviation = std_dev
        document.number_of_ratings = num_ratings

        document.save()

        document.clear_cache()

        logger.info(f"Updated stats for Document {doc_id}: Avg={avg_score}, StdDev={std_dev}, Count={num_ratings}")
        return f"Successfully updated stats for Document {doc_id}"

    except Document.DoesNotExist:
        logger.error(f"Document {doc_id} not found")
        return f"Document {doc_id} not found"
