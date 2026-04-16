import sys
sys.path.insert(0, '..')

from agentbridge import AgentBridge

# Initialize AgentBridge with your system info
bridge = AgentBridge(
    system_name="Demo E-Commerce System",
    system_description="Order management and product catalog for demo purposes",
    port=8090
)

# --- Register Actions ---

@bridge.action(
    name="get_order_status",
    description="Get the current status of a customer order by order ID",
    permissions=["read_only"],
    tags=["orders"]
)
def get_order_status(order_id: str):
    # Simulated database lookup
    orders = {
        "ORD001": {"status": "shipped", "delivery_date": "2026-04-15", "items": ["laptop", "mouse"]},
        "ORD002": {"status": "processing", "delivery_date": "2026-04-18", "items": ["keyboard"]},
        "ORD003": {"status": "delivered", "delivery_date": "2026-04-08", "items": ["monitor"]},
    }
    if order_id not in orders:
        return {"error": f"Order {order_id} not found"}
    return orders[order_id]


@bridge.action(
    name="list_products",
    description="List all available products with prices and stock levels",
    permissions=["read_only"],
    tags=["products"]
)
def list_products(category: str = "all"):
    products = [
        {"id": "P001", "name": "Laptop", "price": 999.99, "stock": 15, "category": "electronics"},
        {"id": "P002", "name": "Mouse", "price": 29.99, "stock": 50, "category": "electronics"},
        {"id": "P003", "name": "Keyboard", "price": 79.99, "stock": 30, "category": "electronics"},
        {"id": "P004", "name": "Desk Chair", "price": 299.99, "stock": 8, "category": "furniture"},
    ]
    if category != "all":
        products = [p for p in products if p["category"] == category]
    return {"products": products, "total": len(products)}


@bridge.action(
    name="cancel_order",
    description="Cancel an existing order — requires human approval before execution",
    permissions=["write", "requires_approval"],
    tags=["orders"]
)
def cancel_order(order_id: str, reason: str):
    return {
        "cancelled": True,
        "order_id": order_id,
        "reason": reason,
        "refund_status": "initiated"
    }


@bridge.action(
    name="get_customer_info",
    description="Get customer details — restricted, not accessible by agents",
    permissions=["restricted"],
    tags=["customers"]
)
def get_customer_info(customer_id: str):
    return {"name": "John Doe", "email": "john@example.com"}


# --- Start the server ---
if __name__ == "__main__":
    bridge.serve()