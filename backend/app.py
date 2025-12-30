import sqlite3
import pandas as pd
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from fastapi.middleware.cors import CORSMiddleware

# ---------------- LOGGING CONFIG ----------------
# Standard Python logging to see what's happening in the terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ---------------- CONFIG ----------------
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    logger.error("GOOGLE_API_KEY not found in .env file")
    raise RuntimeError("GOOGLE_API_KEY not found in .env file")

client = genai.Client(api_key=API_KEY)
app = FastAPI(title="InsightGen API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    data: list[dict]

# ---------------- UTILS ----------------
def get_connection():
    db_path = os.path.join(os.path.dirname(__file__), "sales.db")
    logger.info(f"Connecting to database at: {db_path}")
    return sqlite3.connect(db_path)

def clean_sql(sql: str) -> str:
    return sql.replace("```sql", "").replace("```", "").strip()

def is_safe_sql(sql: str) -> bool:
    sql = sql.strip().lower()
    return sql.startswith("select")

# ---------------- ENDPOINTS ----------------

@app.get("/")
def health_check():
    logger.info("Health check endpoint hit")
    return {"status": "ok", "message": "InsightGen API is running"}

@app.post("/api/generate-sql")
def generate_sql_endpoint(request: QuestionRequest):
    logger.info(f"Received question: {request.question}")
    
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
        logger.info(f"Generated SQL: {sql}")
        
        if not is_safe_sql(sql):
            logger.warning(f"Unsafe SQL generated: {sql}")
            raise HTTPException(status_code=400, detail="Generated unsafe SQL (non-SELECT).")
            
        return {"sql_query": sql}
    except Exception as e:
        logger.error(f"SQL Generation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute-sql")
def execute_sql_endpoint(request: SqlExecutionRequest):
    logger.info(f"Executing SQL query: {request.sql_query}")
    
    if not is_safe_sql(request.sql_query):
        logger.warning("Rejected non-SELECT query execution")
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed.")
        
    try:
        with get_connection() as conn:
            df = pd.read_sql(request.sql_query, conn)
            
        logger.info(f"Query returned {len(df)} rows")
            
        if df.empty:
            return {"data": [], "columns": []}
            
        result = df.to_dict(orient="records")
        return {
            "data": result,
            "columns": list(df.columns)
        }
    except Exception as e:
        logger.error(f"Database Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/generate-insights")
def generate_insights_endpoint(request: InsightRequest):
    logger.info("Generating business insights for data...")
    
    try:
        df = pd.DataFrame(request.data)
        if df.empty:
            logger.info("Insight generation skipped: No data provided")
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
        logger.info("Insights generated successfully")
        return {"insights": response.text.strip()}
        
    except Exception as e:
        logger.error(f"Insight Generation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting InsightGen API on port 5000")
    uvicorn.run(app, host="127.0.0.1", port=5000)