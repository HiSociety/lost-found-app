# Lost and Found Application - API Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)

## Introduction
This document provides detailed information about the Lost and Found application's REST API. The API allows developers to interact with the application programmatically.

### Base URL
```
https://api.lostandfound.com/v1
```

### Response Format
All API responses are in JSON format.

## Authentication

### API Key Authentication
To authenticate your requests, include your API key in the request header:

```
Authorization: Bearer your_api_key_here
```

### JWT Authentication
For user-specific endpoints, use JWT authentication:

```
Authorization: Bearer your_jwt_token_here
```

## API Endpoints

### Users

#### Register a New User
```
POST /users/register
```

Request Body:
```json
{
    "name": "string",
    "email": "string",
    "phone": "string",
    "password": "string"
}
```

Response:
```json
{
    "id": "integer",
    "name": "string",
    "email": "string",
    "phone": "string",
    "created_at": "datetime"
}
```

#### Login
```
POST /users/login
```

Request Body:
```json
{
    "email": "string",
    "password": "string"
}
```

Response:
```json
{
    "token": "string",
    "user": {
        "id": "integer",
        "name": "string",
        "email": "string",
        "phone": "string"
    }
}
```

### Documents

#### Search Documents
```
GET /documents/search
```

Query Parameters:
- `document_type`: string (optional)
- `search_query`: string
- `page`: integer (optional, default: 1)
- `per_page`: integer (optional, default: 10)

Response:
```json
{
    "items": [
        {
            "id": "integer",
            "document_type": "string",
            "unique_id": "string",
            "name": "string",
            "description": "string",
            "images": ["string"],
            "created_at": "datetime"
        }
    ],
    "total": "integer",
    "pages": "integer",
    "current_page": "integer"
}
```

#### Post a Document
```
POST /documents
```

Request Body:
```json
{
    "document_type": "string",
    "unique_id": "string",
    "name": "string",
    "description": "string",
    "images": ["string"] (optional)
}
```

Response:
```json
{
    "id": "integer",
    "document_type": "string",
    "unique_id": "string",
    "name": "string",
    "description": "string",
    "images": ["string"],
    "created_at": "datetime"
}
```

#### Claim a Document
```
POST /documents/{document_id}/claim
```

Response:
```json
{
    "success": "boolean",
    "message": "string",
    "contact_details": "string"
}
```

## Error Handling

### Error Response Format
```json
{
    "error": {
        "code": "integer",
        "message": "string",
        "details": "object" (optional)
    }
}
```

### Common Error Codes
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

## Rate Limiting
- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1625097600
``` 