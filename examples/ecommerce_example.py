"""
AgentBridge — E-Commerce Example

Shows how a real e-commerce backend would use AgentBridge
to become agent-ready without rebuilding anything.
"""
import sys
sys.path.insert(0, '..')

from agentbridge import AgentBridge
from agentbridge.permissions import PermissionPolicy, PermissionLevel

bridge = AgentBridge(
    system_name="ShopFlow E-Commerce",
    system_description="Product catalog, order management, and customer service",
    port=8090
)

# Define permission policies for different agent types
bridge.permissions.add_policy(PermissionPolicy(
    name="customer_service_bot",
    allowed_actions=["get_order_status", "list_products", "search_products"],
    max_permission_level=PermissionLevel.READ_ONLY
))

bridge.permissions.add_policy(PermissionPolicy(
    name="ops_agent",
    max_permission_level=PermissionLevel.WRITE
))


# ─── Product Actions ──────────────────────────────────────────────────────────

@bridge.action(
    name="list_products",
    description="List all available products with prices and stock levels",
    permissions=["read_only"],
    tags=["products"]
)
def list_products(category: str = "all", in_stock_only: bool = False):
    products = [
        {"id": "P001", "name": "Laptop Pro", "price": 999.99, "stock": 15, "category": "electronics"},
        {"id": "P002", "name": "Wireless Mouse", "price": 29.99, "stock": 50, "category": "electronics"},
        {"id": "P003", "name": "Mechanical Keyboard", "price": 79.99, "stock": 0, "category": "electronics"},
        {"id": "P004", "name": "Ergonomic Chair", "price": 299.99, "stock": 8, "category": "furniture"},
        {"id": "P005", "name": "Standing Desk", "price": 499.99, "stock": 3, "category": "furniture"},
    ]
    if category != "all":
        products = [p for p in products if p["category"] == category]
    if in_stock_only:
        products = [p for p in products if p["stock"] > 0]
    return {"products": products, "total": len(products)}


@bridge.action(
    name="search_products",
    description="Search products by keyword",
    permissions=["read_only"],
    tags=["products"]
)
def search_products(query: str):
    all_products = [
        {"id": "P001", "name": "Laptop Pro", "price": 999.99, "stock": 15},
        {"id": "P002", "name": "Wireless Mouse", "price": 29.99, "stock": 50},
        {"id": "P003", "name": "Mechanical Keyboard", "price": 79.99, "stock": 0},
    ]
    results = [p for p in all_products if query.lower() in p["name"].lower()]
    return {"results": results, "count": len(results), "query": query}


# ─── Order Actions ────────────────────────────────────────────────────────────

@bridge.action(
    name="get_order_status",
    description="Get the current status and details of a customer order",
    permissions=["read_only"],
    tags=["orders"],
    examples=[
        {"inputs": {"order_id": "ORD001"}, "description": "Check status of order ORD001"}
    ]
)
def get_order_status(order_id: str):
    orders = {
        "ORD001": {"status": "shipped", "delivery_date": "2026-04-15", "items": ["Laptop Pro"], "total": 999.99},
        "ORD002": {"status": "processing", "delivery_date": "2026-04-18", "items": ["Wireless Mouse"], "total": 29.99},
        "ORD003": {"status": "delivered", "delivery_date": "2026-04-08", "items": ["Ergonomic Chair"], "total": 299.99},
    }
    if order_id not in orders:
        return {"error": f"Order {order_id} not found"}
    return {**orders[order_id], "order_id": order_id}


@bridge.action(
    name="update_order_status",
    description="Update the status of an existing order",
    permissions=["write"],
    tags=["orders"]
)
def update_order_status(order_id: str, new_status: str):
    valid_statuses = ["processing", "shipped", "delivered", "cancelled"]
    if new_status not in valid_statuses:
        return {"error": f"Invalid status. Must be one of: {valid_statuses}"}
    return {"updated": True, "order_id": order_id, "new_status": new_status}


@bridge.action(
    name="cancel_order",
    description="Cancel a customer order — requires human approval",
    permissions=["write", "requires_approval"],
    tags=["orders"]
)
def cancel_order(order_id: str, reason: str):
    return {
        "cancelled": True,
        "order_id": order_id,
        "reason": reason,
        "refund_status": "initiated",
        "refund_eta": "3-5 business days"
    }


# ─── Customer Actions ─────────────────────────────────────────────────────────

@bridge.action(
    name="get_customer_profile",
    description="Get customer profile — restricted, agents cannot access",
    permissions=["restricted"],
    tags=["customers"]
)
def get_customer_profile(customer_id: str):
    return {"name": "John Doe", "email": "john@example.com"}


if __name__ == "__main__":
    bridge.serve()