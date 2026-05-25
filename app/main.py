from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse
import sqlite3
import uvicorn

app = FastAPI(title="SwiggyOps Order Service")

# Prometheus metrics
request_counter = Counter("order_requests_total", "Total requests", ["method", "endpoint"])
request_latency = Histogram("order_request_latency_seconds", "Request latency")

# Database setup
def get_db():
    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            restaurant_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            total_amount REAL NOT NULL,
            delivery_address TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    """)
    # Sample data
    conn.execute("INSERT OR IGNORE INTO orders (id, customer_id, restaurant_id, status, total_amount, delivery_address) VALUES (1, 101, 1, 'delivered', 360, 'Hyderabad, Banjara Hills')")
    conn.execute("INSERT OR IGNORE INTO orders (id, customer_id, restaurant_id, status, total_amount, delivery_address) VALUES (2, 102, 2, 'pending', 299, 'Hyderabad, Madhapur')")
    conn.execute("INSERT OR IGNORE INTO order_items (id, order_id, item_name, quantity, price) VALUES (1, 1, 'Chicken Biryani', 2, 180)")
    conn.execute("INSERT OR IGNORE INTO order_items (id, order_id, item_name, quantity, price) VALUES (2, 2, 'Margherita Pizza', 1, 299)")
    conn.commit()
    conn.close()

init_db()

# Models
class Order(BaseModel):
    customer_id: int
    restaurant_id: int
    total_amount: float
    delivery_address: str

class OrderItem(BaseModel):
    order_id: int
    item_name: str
    quantity: int
    price: float

class OrderStatus(BaseModel):
    status: str

# Order Routes
@app.get("/orders")
def get_orders():
    request_counter.labels(method="GET", endpoint="/orders").inc()
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders").fetchall()
    conn.close()
    return [dict(o) for o in orders]

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    request_counter.labels(method="GET", endpoint="/orders/id").inc()
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone
@app.get('/health')
def health():
    return {'status': 'healthy', 'service': 'order-service'}

