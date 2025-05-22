# Gemini Powered CRM AI Query System

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
  - [Health Check](#health-check)
  - [Natural Language Query](#natural-language-query)
  - [Create Sample Data](#create-sample-data)
- [Security Considerations](#security-considerations)
- [Future Improvements](#future-improvements)

## Overview
The Gemini Powered CRM AI Query System is a FastAPI application that allows users to query a CRM database using natural language. It leverages Google's Gemini Large Language Model to translate natural language questions into SQL queries, execute them against a PostgreSQL database, and then generate a user-friendly natural language response based on the query results.

## Features
- **Natural Language Querying**: Ask questions about your CRM data in plain English.
- **AI-Powered SQL Generation**: Uses Google Gemini to convert natural language to SQL.
- **AI-Powered Response Generation**: Summarizes SQL query results into natural language.
- **Database Interaction**: Connects to a PostgreSQL database to retrieve CRM data (Clients, Invoices, Payments).
- **SQL Safety Validation**: Basic checks to prevent harmful SQL queries.
- **RESTful API**: Exposes endpoints for querying and managing sample data.
- **Sample Data Generation**: Populates database with sample data for testing.
- **Asynchronous Operations**: Uses async and await for non-blocking API calls.

## How It Works
1. **User Query**: A natural language query is sent to the API.
2. **SQL Generation**: Gemini generates SQL using schema constraints.
3. **SQL Validation**: SQL is checked for safety (e.g., only SELECT, no system tables).
4. **SQL Execution**: Executes query against PostgreSQL.
5. **Response Generation**: Gemini generates a summary of results.
6. **API Response**: Returns JSON with query, SQL, results, and summary.

## Tech Stack
- **Backend Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **AI Model**: Google Gemini (via `google-generativeai` SDK)
- **Data Validation**: Pydantic
- **Environment Management**: python-dotenv
- **Web Server**: Uvicorn
- **Database Driver**: psycopg2-binary

## Project Structure
```
gemini_crm_ai_project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── models.py
│   ├── schemas.py
│   ├── ai_processor.py
│   └── api/
│       └── v1/
│           └── routes.py
├── .env
└── requirements.txt
```

## Prerequisites
- Python 3.8+
- PostgreSQL
- Google API Key with Gemini access

## Setup and Installation
```bash
git clone <repository-url>
cd gemini_crm_ai_project
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Add a `.env` file:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/crm_db
GOOGLE_API_KEY=your_google_api_key_here
```

## Running the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
**GET** `/api/v1/health`  
**Response**
```json
{
  "status": "healthy",
  "timestamp": "YYYY-MM-DDTHH:MM:SS.ffffff"
}
```

### Natural Language Query
**POST** `/api/v1/query/natural-language`  
**Request**
```json
{ "query": "Show me all unpaid invoices for Alpha Corp" }
```

**Response**
```json
{
  "success": true,
  "query": "...",
  "results": [...],
  "sql_query": "...",
  "response_text": "...",
  "execution_time": 1.234
}
```

### Create Sample Data
**POST** `/api/v1/sample-data`  
**Response**
```json
{ "message": "Sample data created successfully" }
```

## Security Considerations
- SQL safety validation: `_is_safe_sql` restricts access to app tables only.
- Minimal DB user permissions.
- Validate Gemini outputs.
- Keep API keys secure.
- Add authentication in production.

## Future Improvements
- Database migrations (Alembic)
- Advanced SQL parsing
- Intent detection
- Auth & AuthZ
- Streaming response
- Contextual conversations
- Rate limiting
- Structured logging
- Comprehensive testing
