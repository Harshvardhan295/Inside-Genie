import sqlite3
import pandas as pd
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from fastapi.middleware.cors import CORSMiddleware

# ---------------- CONFIG ----------------
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in .env file")

client = genai.Client(api_key=API_KEY)

app = FastAPI(title="InsightGen API")

# Allow CORS so Next.js (running on a different port) can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Next.js URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DATA MODELS ----------------
class QuestionRequest(BaseModel):
    question: str

class SqlExecutionRequest(BaseModel):
    sql_query: str

class InsightRequest(BaseModel):
    data: list[dict] # Passing JSON data to generate insights

# ---------------- UTILS ----------------
def get_connection():
    # Ensure sales.db is in the same directory or provide full path
    return sqlite3.connect("sales.db")

def clean_sql(sql: str) -> str:
    return sql.replace("```sql", "").replace("```", "").strip()

def is_safe_sql(sql: str) -> bool:
    sql = sql.strip().lower()
    return sql.startswith("select")

# ---------------- ENDPOINTS ----------------

@app.get("/")
def health_check():
    return {"status": "ok", "message": "InsightGen API is running"}

@app.post("/api/generate-sql")
def generate_sql_endpoint(request: QuestionRequest):
    """
    Takes a natural language question and returns a SQL query.
    """
    prompt = f"""
    You are an expert SQL developer.
    Database schema:
    sales(order_id INTEGER, product_name TEXT, category TEXT, quantity INTEGER, price REAL, order_date TEXT)
    
    Rules:
    - Generate ONLY a SELECT SQL query
    - SQLite compatible SQL
    - No explanations, only SQL
    
    User question: {request.question}
    SQL:
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        sql = clean_sql(response.text)
        if not is_safe_sql(sql):
            raise HTTPException(status_code=400, detail="Generated unsafe SQL (non-SELECT).")
        return {"sql_query": sql}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute-sql")
def execute_sql_endpoint(request: SqlExecutionRequest):
    """
    Executes the SQL query and returns the result as JSON.
    """
    if not is_safe_sql(request.sql_query):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed.")
        
    try:
        with get_connection() as conn:
            # Read into Pandas to easily convert to JSON
            df = pd.read_sql(request.sql_query, conn)
            
        if df.empty:
            return {"data": [], "columns": []}
            
        # Convert dataframe to a dictionary format suitable for frontend
        result = df.to_dict(orient="records")
        return {
            "data": result,
            "columns": list(df.columns) # Helpful for frontend table headers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/generate-insights")
def generate_insights_endpoint(request: InsightRequest):
    """
    Takes data records and generates business insights.
    """
    # Convert list of dicts back to dataframe for preview string
    try:
        df = pd.DataFrame(request.data)
        if df.empty:
             return {"insights": "No data available to generate insights."}

        preview = df.head(10).to_string(index=False)
        
        prompt = f"""
        You are a business analyst.
        Given this data:
        {preview}
        Give 3 short business insights in bullet points.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return {"insights": response.text.strip()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)