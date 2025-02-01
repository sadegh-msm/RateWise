# Flow of Applying Ratings, Outlier Detection, and Reprocessing

This system manages user-submitted ratings for documents, detects outliers, and reprocesses them after a certain period. It uses **Celery tasks**, **Redis caching**, and **RabbitMQ** for asynchronous task execution and efficient processing.

## Rating Submission and Initial Processing

### Receiving a Rating
- When a user submits a rating for a document, it gets stored in the Rating model.
- The rating’s score is checked against the document’s historical ratings using the detect_outlier method.

#### Outlier Detection Logic
- The system considers a rating as an outlier if it significantly deviates from the document’s historical rating distribution. The exact logic is handled by document.detect_outlier(rating.score), which its based on standard deviation calculations.
#### Two possible cases:
1. Not an outlier:
- The document updates its cached statistics to reflect the new rating.
- The document ID is stored for batch updating of statistics.
2. Outlier detected:
- The rating is stored in Redis cache as a potential outlier using store_outlier(doc_id, rating_id).
- This prevents immediate deletion or rejection and allows re-evaluation later.
- A log entry is created to indicate an outlier has been found.

### Batch Processing of Ratings Using RabbitMQ

#### RabbitMQ Message Queue (process_doc Task)
- Ratings are temporarily stored in a RabbitMQ queue (document_ratings) to enable batch processing.
- The process_doc Celery task:
- Connects to RabbitMQ.
- Fetches up to BATCH_SIZE messages.
- Iterates through each rating and determines whether it’s an outlier.
- Calls store_outlier() if necessary.
- Otherwise, updates the document’s cached rating statistics.
- Triggers update_doc_stats(doc_id) asynchronously for recalculating statistics.

### Periodic Reprocessing of Outliers

#### process_outliers Task
- Runs periodically (based on Celery’s schedule).
- Retrieves outliers stored in Redis cache (outlier_ratings key).
- Processes them only if a threshold time (OUTLIER_PROCESS_THRESHOLD) has passed.
- Outlier processing logic:
- If enough time has passed (time.time() - outlier["timestamp"] >= OUTLIER_PROCESS_THRESHOLD):
- The rating is marked as an outlier in the database (rating.is_outlier = True).
- The associated document’s statistics are recalculated via update_doc_stats(doc_id).
- Otherwise, the rating remains in Redis for future re-evaluation.

### Updating Document Statistics (update_doc_stats)
- Triggered whenever ratings are processed or reprocessed.
- Retrieves the document and recalculates:
- Average Score (calculate_average_score())
- Standard Deviation (calculate_standard_deviation())
- Total Ratings Count (number_of_ratings())
- Updates the document’s database entry and clears cached data.

## Summary of Flow
1. User submits a rating.
2. RabbitMQ stores the rating for batch processing.
3. The process_doc task runs:
- Determines if the rating is an outlier.
- If not, updates document statistics.
- If it is, stores it in Redis for later re-evaluation.
4. After a delay (OUTLIER_PROCESS_THRESHOLD), the process_outliers task runs:
- If enough time has passed, the rating is marked as an outlier and stored permanently.
- Otherwise, it remains in Redis.
5. Document statistics are periodically updated via update_doc_stats.
