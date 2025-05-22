from fastapi import FastAPI
from datetime import datetime
import uvicorn

from app.core.config import engine, Base
from app.api.v1 import routes as api_v1_routes
from app import models # Ensure models are imported so Base knows about them

# Create all database tables defined in models
# This should ideally be handled by migrations (e.g. Alembic) in a production app
# For this example, we create them on startup if they don't exist.
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables checked/created successfully.")
except Exception as e:
    print(f"Error creating database tables: {e}")
    # Depending on the error, you might want to exit or handle it differently
    # For now, we'll let the app try to start, but it might fail if DB is essential

app = FastAPI(
    title="CRM AI Query System",
    version="1.0.0",
    description="A FastAPI application to query CRM data using natural language through AI.",
)

# Include API routers
app.include_router(api_v1_routes.router, prefix="/api/v1", tags=["v1"])

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the CRM AI Query System!"}

@app.get("/api/v1/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Example usage and test queries from the original file (for reference):
"""
Test the API with these natural language queries:
1. "Show me all unpaid invoices after July 2025" -> (original date 2024, updated to 2025 for sample data consistency)
2. "Which clients have overdue payments?"
3. "What's the total amount of pending invoices?"
4. "Show me payment history for ABC Corp"
5. "List all invoices with amounts greater than 2000"

Example curl commands:
# Create sample data (run this first if DB is empty)
curl -X POST "http://localhost:8000/api/v1/sample-data"

# Query with natural language
curl -X POST "http://localhost:8000/api/v1/query/natural-language" \
     -H "Content-Type: application/json" \
     -d '{"query": "Show me all unpaid invoices with due date after July 2025"}'

# Health check
curl "http://localhost:8000/api/v1/health"
"""

if __name__ == "__main__":
    # It's generally recommended to run Uvicorn from the command line:
    # uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    # However, this allows running directly with `python app/main.py` for simplicity here.
    uvicorn.run(app, host="0.0.0.0", port=8000)