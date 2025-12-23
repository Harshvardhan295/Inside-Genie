import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect("sales.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    order_id INTEGER PRIMARY KEY,
    product_name TEXT,
    category TEXT,
    quantity INTEGER,
    price REAL,
    order_date TEXT
)
""")

products = [
    ("Laptop", "Electronics"),
    ("Phone", "Electronics"),
    ("Shoes", "Fashion"),
    ("Watch", "Accessories"),
    ("Bag", "Fashion")
]

start_date = datetime.now() - timedelta(days=90)

for _ in range(200):
    product, category = random.choice(products)
    quantity = random.randint(1, 5)
    price = random.randint(1000, 60000)
    date = start_date + timedelta(days=random.randint(0, 90))

    cursor.execute("""
    INSERT INTO sales (product_name, category, quantity, price, order_date)
    VALUES (?, ?, ?, ?, ?)
    """, (product, category, quantity, price, date.strftime("%Y-%m-%d")))

conn.commit()
conn.close()

print("Database and data created successfully")
