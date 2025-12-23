import streamlit as st
import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
from google import genai

# ---------------- CONFIG ----------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("GEMINI_API_KEY not found in .env file")
    st.stop()

client = genai.Client(api_key=API_KEY)

st.set_page_config(page_title="InsightGen", layout="wide")
st.title("📊 InsightGen – GenAI Dashboard Generator")

# ---------------- DATABASE ----------------
def get_connection():
    return sqlite3.connect("sales.db")

# ---------------- UTILS ----------------
def clean_sql(sql: str) -> str:
    """Remove markdown/code fences from LLM SQL output"""
    return (
        sql.replace("```sql", "")
           .replace("```", "")
           .strip()
    )

def is_safe_sql(sql: str) -> bool:
    """Allow only SELECT queries"""
    sql = sql.strip().lower()
    return sql.startswith("select")

# ---------------- GENAI FUNCTIONS ----------------
def generate_sql(user_question: str) -> str:
    prompt = f"""
You are an expert SQL developer.

Database schema:
sales(
    order_id INTEGER,
    product_name TEXT,
    category TEXT,
    quantity INTEGER,
    price REAL,
    order_date TEXT
)

Rules:
- Generate ONLY a SELECT SQL query
- SQLite compatible SQL
- No explanations, only SQL

User question:
{user_question}

SQL:
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return clean_sql(response.text)
    except Exception as e:
        return f"-- ERROR: {str(e)}"


def generate_insights(df: pd.DataFrame) -> str:
    preview = df.head(10).to_string(index=False)

    prompt = f"""
You are a business analyst.

Given this data:
{preview}

Give 3 short business insights in bullet points.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"- Unable to generate insights: {str(e)}"

# ---------------- UI ----------------
question = st.text_input("Ask a business question:")

if st.button("Generate Dashboard"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Generating SQL..."):
            sql_query = generate_sql(question)

        st.subheader("Generated SQL")
        st.code(sql_query, language="sql")

        if sql_query.startswith("-- ERROR"):
            st.error(sql_query)
            st.stop()

        if not is_safe_sql(sql_query):
            st.error("Unsafe SQL detected. Only SELECT queries are allowed.")
            st.stop()

        try:
            with get_connection() as conn:
                df = pd.read_sql(sql_query, conn)
        except Exception as e:
            st.error(f"SQL execution failed: {e}")
            st.stop()

        if df.empty:
            st.warning("No data found.")
            st.stop()

        # -------- TABLE --------
        st.subheader("Query Result")
        st.dataframe(df, use_container_width=True)

        # -------- AUTO CHART --------
        st.subheader("Auto Chart")

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        non_numeric_cols = df.select_dtypes(exclude="number").columns.tolist()

        if numeric_cols and non_numeric_cols:
            x_col = non_numeric_cols[0]
            y_col = numeric_cols[0]
            st.bar_chart(df[[x_col, y_col]].set_index(x_col))
        elif numeric_cols:
            st.metric(
                label="Value",
                value=int(df[numeric_cols[0]].iloc[0])
            )
        else:
            st.info("No suitable data for chart.")

        # -------- INSIGHTS --------
        st.subheader("Business Insights")
        st.markdown(generate_insights(df))
