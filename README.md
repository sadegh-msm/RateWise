# RateWise
Document rating application

## Overview
This application provides a document management system with user authentication, document creation, listing, rating, and rating analysis using outlier detection. Users can create and rate documents, and the system applies statistical techniques to detect anomalies in the ratings.

## Features
- User authentication and token-based authorization
- Document creation and retrieval
- Rating system with outlier detection
- Statistical analysis of document ratings

## Authentication
The application uses token-based authentication. Users must authenticate to perform actions like creating documents, rating documents, and retrieving certain data. Tokens are generated upon user registration and are required for API requests.

## Document Management
Users can create, update, and retrieve documents. Each document contains a title and text content. Documents are accessible to authenticated users.

## Rating System
Users can submit ratings for documents. The rating system ensures fairness and prevents anomalies through outlier detection. Each rating consists of:
- A numerical score submitted by a user.
- Validation to ensure scores fall within a defined range.

### Outlier Detection in Ratings
To maintain rating integrity, the system applies statistical techniques to detect and mitigate outliers. The process involves:
1. **Collecting Ratings**: All ratings for a document are stored.
2. **Computing Statistical Metrics**: The system calculates the mean and standard deviation of ratings.
3. **Identifying Outliers**: Ratings that significantly deviate (e.g., beyond a defined threshold such as 2 standard deviations) are flagged as potential outliers.
4. **Handling Outliers**: Outliers will marked for review and will be applied after a short period of time.

This approach ensures that extreme ratings (whether excessively high or low) do not disproportionately affect the overall document score.

## Deployment
The application is containerized using Docker and managed with Docker Compose. To deploy:
1. Ensure Docker and Docker Compose are installed.
2. Use the provided `docker-compose.yml` file to set up the necessary services, including the application and database.
```
   docker compose up -d 
```
3. Start the application using Docker Compose, which handles container orchestration.
4. Access application UI with dajngo-admin in [localhost:8000/admin/](http://localhost:8000/admin/) and access rabbit UI in [localhost:15672](http://localhost:15672)
5. For testing you can access swagger in [localhost:8000/swagger/](http://localhost:8000/swagger/)


## Running Tests
Automated tests are included to validate core functionalities:
- Authentication and user creation
- Document creation and retrieval
- Rating system, including outlier detection
- Statistical analysis of ratings

Tests can be run by this command:
```
python manage.py test RateWise
```

