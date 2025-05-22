import google.generativeai as genai # Changed from openai
import json
import re
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

class CRMQueryProcessor:
    def __init__(self):
        self.db_schema = self._get_schema_info()
        # Initialize the Gemini model - using a recent efficient model
        # You can choose other models like 'gemini-pro' as well
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.0 # For deterministic SQL
        )
        self.response_generation_config = genai.types.GenerationConfig(
            temperature=0.3 # For slightly more natural responses
        )


    def _get_schema_info(self) -> str:
        # Same schema info as before
        return """
        Database Schema:

        Table: clients
        - id (UUID, Primary Key)
        - name (String, Client name)
        - email (String, Client email)
        - created_at (DateTime)

        Table: invoices
        - id (UUID, Primary Key)
        - client_id (UUID, Foreign Key to clients)
        - invoice_number (String, Unique)
        - amount (Decimal, Invoice amount)
        - due_date (Date, When payment is due)
        - issue_date (Date, When invoice was issued)
        - status (String: pending, paid, overdue)
        - created_at (DateTime)

        Table: payments
        - id (UUID, Primary Key)
        - invoice_id (UUID, Foreign Key to invoices)
        - amount (Decimal, Payment amount)
        - payment_date (Date, When payment was made)
        - payment_method (String: cash, credit_card, bank_transfer)
        - created_at (DateTime)

        Relationships:
        - clients -> invoices (one to many)
        - invoices -> payments (one to many)
        """

    async def process_query(self, query: str, db: Session) -> Dict[str, Any]:
        start_time = datetime.now()
        sql_query_generated = None # Initialize to store generated SQL

        try:
            sql_query_generated = await self._generate_sql(query)
            if not self._is_safe_sql(sql_query_generated):
                raise ValueError("Generated SQL contains unsafe operations or is not a SELECT statement.")
            
            results = self._execute_sql(sql_query_generated, db)
            response_text = await self._generate_response(query, results)
            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "query": query,
                "results": results,
                "sql_query": sql_query_generated,
                "response_text": response_text,
                "execution_time": execution_time
            }
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "query": query,
                "results": [],
                "sql_query": sql_query_generated, # Return SQL if generated, even on error
                "response_text": f"Error processing query: {str(e)}",
                "execution_time": execution_time
            }

    async def _generate_sql(self, query: str) -> str:
        # System message incorporated into the prompt for Gemini
        prompt = f"""
        You are a SQL expert. Convert natural language queries into safe, read-only SQL queries against the application's data tables (clients, invoices, payments).
        Rules:
        1. ONLY generate SELECT statements.
        2. Queries MUST ONLY target the application tables: 'clients', 'invoices', 'payments'.
        3. DO NOT generate queries that inspect or retrieve database schema, metadata, table structures, column lists, or system catalog information (e.g., from information_schema, pg_catalog, or similar system views/tables). Such queries are strictly forbidden.
        4. Use proper JOINs when accessing multiple application tables based on the provided schema.
        5. Use appropriate WHERE clauses based on the user's query.
        6. Format dates in SQL conditions as 'YYYY-MM-DD'.
        7. Return ONLY the SQL query, with no explanations, comments, or markdown.

        Application Database Schema (only these tables are allowed for querying):
        {self.db_schema} 
        
        Natural language query:
        "{query}"

        SQL Query:
        """
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=self.generation_config
            )
            # Check for safety blocks or empty response
            if not response.parts:
                 if response.prompt_feedback and response.prompt_feedback.block_reason:
                    raise ValueError(f"SQL generation blocked due to: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason.name}")
                 raise ValueError("SQL generation failed: No content received from model.")
            
            sql_query = response.text.strip()
        except Exception as e:
            # Catch API errors or other issues during generation
            raise Exception(f"Gemini SQL generation error: {str(e)}")


        # Clean up the SQL (remove markdown formatting if present by mistake)
        sql_query = re.sub(r'^```sql\s*', '', sql_query, flags=re.IGNORECASE)
        sql_query = re.sub(r'\s*```$', '', sql_query)
        sql_query = sql_query.strip() # Ensure no leading/trailing whitespace

        if not sql_query:
            raise ValueError("Generated SQL query is empty.")
        return sql_query

    def _is_safe_sql(self, sql: str) -> bool:
        sql_upper = sql.upper().strip()
        if not sql_upper.startswith('SELECT'):
            print(f"Validation Failed: SQL does not start with SELECT. Query: {sql}")
            return False

        # Block queries to information_schema or pg_catalog (PostgreSQL specific)
        # or other common database schema/metadata tables
        blocked_schema_keywords = [
            'INFORMATION_SCHEMA.',
            'PG_CATALOG.',
            'PG_TABLES',
            'PG_CLASS',
            'PG_NAMESPACE',
            'PG_ATTRIBUTE',
            'SYSTABLES', # Example for other DBs
            'SYSCOLUMNS', # Example for other DBs
            'ALL_TABLES', # Example for Oracle
            'ALL_TAB_COLUMNS' # Example for Oracle
        ]
        for schema_keyword in blocked_schema_keywords:
            if schema_keyword in sql_upper:
                print(f"Validation Failed: SQL attempts to access blocked schema info ('{schema_keyword}'). Query: {sql}")
                return False

        dangerous_keywords = [
            'DELETE', 'DROP', 'UPDATE', 'INSERT', 'CREATE', 'ALTER',
            'TRUNCATE', 'EXEC', 'EXECUTE', '-- ', ';', '/*', '*/' 
            # Semicolon is tricky; allowed if it's the absolute last char by some logic below
        ]
        for keyword in dangerous_keywords:
            # Check if keyword is a whole word or followed by non-alphanumeric
            # Regex: \b matches word boundary. re.escape handles special chars in keyword.
            # The replace part handles keywords like '-- ' which have a space.
            pattern = r'\b' + re.escape(keyword.replace(' ', r'\s+')) + r'\b'
            if re.search(pattern, sql_upper):
                # Special handling for semicolon: allow ONLY if it's the absolute last character of the SQL string
                if keyword == ';':
                    if sql_upper.endswith(';') and sql_upper.count(';') == 1:
                        continue # Allow single trailing semicolon
                
                print(f"Validation Failed: SQL contains dangerous keyword '{keyword}'. Query: {sql}")
                return False
        
        # Check for attempts to list all tables or columns broadly if not caught by schema keywords
        # This is more heuristic
        if "FROM PG_CLASS" in sql_upper or "FROM INFORMATION_SCHEMA.TABLES" in sql_upper or "FROM INFORMATION_SCHEMA.COLUMNS" in sql_upper:
             print(f"Validation Failed: SQL attempts to list all tables/columns broadly. Query: {sql}")
             return False


        return True

    def _execute_sql(self, sql: str, db: Session) -> List[Dict[str, Any]]:
        try:
            result_proxy = db.execute(text(sql)) # Using text() for SQLAlchemy
            columns = result_proxy.keys()
            rows = result_proxy.fetchall()
            results = []
            for row in rows:
                row_dict = {}
                for i, column_name in enumerate(columns):
                    value = row[i]
                    if isinstance(value, Decimal):
                        value = float(value)
                    elif isinstance(value, (date, datetime)):
                        value = value.isoformat()
                    elif isinstance(value, uuid.UUID):
                        value = str(value)
                    row_dict[str(column_name)] = value # Ensure column_name is string
                results.append(row_dict)
            return results
        except Exception as e:
            print(f"SQL execution error for SQL: {sql}")
            raise Exception(f"SQL execution error: {str(e)}")

    async def _generate_response(self, query: str, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "No results found for your query."

        results_for_prompt = results[:5] # Limit for prompt brevity
        summary_note = f"\n(Showing first {len(results_for_prompt)} of {len(results)} results)" if len(results) > 5 else ""
        
        # System message incorporated into the prompt
        prompt = f"""
        You are a helpful business analyst. Your task is to provide a clear, concise, and natural language summary of the provided data results,
        based on the user's original query.

        User's original query: "{query}"

        Data results (sample):
        {json.dumps(results_for_prompt, indent=2)}{summary_note}

        Based on these results and the user's query, generate a natural, conversational response.
        Summarize the key findings. If there are numbers (counts, totals, amounts), try to include them.
        Keep the response concise but informative. Avoid just saying "Here are the results."

        Response:
        """
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=self.response_generation_config
            )
            if not response.parts:
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    raise ValueError(f"Response generation blocked due to: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason.name}")
                raise ValueError("Response generation failed: No content received from model.")
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini response generation error: {str(e)}")