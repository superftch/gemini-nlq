from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime # For sample data

from app.schemas import QueryRequest, QueryResponse
from app.ai_processor import CRMQueryProcessor
from app.core.config import get_db
from app.models import Client, Invoice, Payment # For sample data

router = APIRouter()
query_processor = CRMQueryProcessor() # Instantiate the processor

@router.post("/query/natural-language", response_model=QueryResponse)
async def process_natural_language_query(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Process natural language queries about CRM data.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    result_dict = await query_processor.process_query(request.query, db)
    
    if not result_dict["success"]:
        # You might want to return a different status code for processing errors
        # For now, let's assume 200 OK with success: false as per QueryResponse
        pass # The result_dict already contains error information

    return QueryResponse(**result_dict)


@router.post("/sample-data", summary="Create Sample CRM Data")
async def create_sample_data(db: Session = Depends(get_db)):
    """
    Create sample clients, invoices, and payments for testing purposes.
    This endpoint is for demonstration and should ideally be secured or removed in production.
    """
    try:
        # Create sample clients
        client1 = Client(name="ABC Corp", email="contact@abc.com")
        client2 = Client(name="XYZ Ltd", email="info@xyz.com")
        client3 = Client(name="Tech Solutions", email="hello@techsol.com")
        db.add_all([client1, client2, client3])
        db.commit() # Commit clients to get their IDs

        # Create sample invoices
        invoice1 = Invoice(
            client_id=client1.id,
            invoice_number="INV-2025-001", # Made more unique
            amount=5000.00,
            due_date=date(2025, 8, 15),
            issue_date=date(2025, 7, 15),
            status="pending"
        )
        invoice2 = Invoice(
            client_id=client2.id,
            invoice_number="INV-2025-002",
            amount=3200.00,
            due_date=date(2025, 7, 30),
            issue_date=date(2025, 6, 30),
            status="paid"
        )
        invoice3 = Invoice(
            client_id=client3.id,
            invoice_number="INV-2025-003",
            amount=1500.00,
            due_date=date(2025, 9, 1), # Original had 2024, changed to 2025 for consistency
            issue_date=date(2025, 8, 1),
            status="overdue"
        )
        db.add_all([invoice1, invoice2, invoice3])
        db.commit() # Commit invoices to get their IDs

        # Create sample payment
        payment1 = Payment(
            invoice_id=invoice2.id, # Assuming invoice2 is paid
            amount=3200.00,
            payment_date=date(2025, 7, 25),
            payment_method="bank_transfer"
        )
        db.add(payment1)
        db.commit()

        return {"message": "Sample data created successfully"}
    except Exception as e:
        db.rollback() # Rollback in case of error
        raise HTTPException(status_code=500, detail=f"Failed to create sample data: {str(e)}")