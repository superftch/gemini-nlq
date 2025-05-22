from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime # Added for QueryResponse timestamp

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    success: bool
    query: str
    results: List[Dict[str, Any]]
    sql_query: Optional[str] = None
    response_text: str
    execution_time: float