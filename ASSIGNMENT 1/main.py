from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel

app = FastAPI(title="FastAPI Day 6 – Search, Sort & Pagination")

# ──────────────────────────────────────────────
# DATA
# ──────────────────────────────────────────────
products = [
    {"product_id": 1, "name": "Wireless Mouse",  "price": 499, "category": "Electronics"},
    {"product_id": 2, "name": "Notebook",         "price":  99, "category": "Stationery"},
    {"product_id": 3, "name": "USB Hub",          "price": 799, "category": "Electronics"},
    {"product_id": 4, "name": "Pen Set",          "price":  49, "category": "Stationery"},
]

orders = []
order_counter = {"id": 1}


# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────
class OrderIn(BaseModel):
    customer_name: str
    product_id: int
    quantity: int


# ══════════════════════════════════════════════
# Q1 – GET /products/search   (case-insensitive keyword search)
# ══════════════════════════════════════════════
@app.get("/products/search")
def search_products(keyword: str = Query(..., description="Search keyword")):
    results = [p for p in products if keyword.lower() in p["name"].lower()]
    if not results:
        return {"message": f"No products found for: {keyword}"}
    return {"keyword": keyword, "total_found": len(results), "products": results}


# ══════════════════════════════════════════════
# Q2 – GET /products/sort   (sort by price or name, asc/desc)
# ══════════════════════════════════════════════
@app.get("/products/sort")
def sort_products(
    sort_by: str = Query("price", description="'price' or 'name'"),
    order:   str = Query("asc",   description="'asc' or 'desc'"),
):
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}
    sorted_products = sorted(products, key=lambda p: p[sort_by], reverse=(order == "desc"))
    return {"sort_by": sort_by, "order": order, "products": sorted_products}


# ══════════════════════════════════════════════
# Q3 – GET /products/page   (pagination)
# ══════════════════════════════════════════════
@app.get("/products/page")
def get_products_paged(
    page:  int = Query(1, ge=1,  description="Page number"),
    limit: int = Query(2, ge=1, le=20, description="Items per page"),
):
    total = len(products)
    start = (page - 1) * limit
    paged = products[start: start + limit]
    return {
        "page":        page,
        "limit":       limit,
        "total":       total,
        "total_pages": -(-total // limit),   # ceiling division
        "products":    paged,
    }


# ══════════════════════════════════════════════
# POST /orders  (used by Q4 Bonus – place orders first)
# ══════════════════════════════════════════════
@app.post("/orders")
def place_order(order: OrderIn):
    product = next((p for p in products if p["product_id"] == order.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    new_order = {
        "order_id":      order_counter["id"],
        "customer_name": order.customer_name,
        "product_id":    order.product_id,
        "product_name":  product["name"],
        "quantity":      order.quantity,
        "total_price":   product["price"] * order.quantity,
    }
    orders.append(new_order)
    order_counter["id"] += 1
    return {"message": "Order placed successfully", "order": new_order}


# ══════════════════════════════════════════════
# Q4 – GET /orders/search   (search by customer name)
# ══════════════════════════════════════════════
@app.get("/orders/search")
def search_orders(customer_name: str = Query(..., description="Customer name keyword")):
    results = [o for o in orders if customer_name.lower() in o["customer_name"].lower()]
    if not results:
        return {"message": f"No orders found for: {customer_name}"}
    return {"customer_name": customer_name, "total_found": len(results), "orders": results}


# ══════════════════════════════════════════════
# Q5 – GET /products/sort-by-category   (multi-key sort)
# ══════════════════════════════════════════════
@app.get("/products/sort-by-category")
def sort_by_category():
    result = sorted(products, key=lambda p: (p["category"], p["price"]))
    return {"products": result, "total": len(result)}


# ══════════════════════════════════════════════
# Q6 – GET /products/browse   (search + sort + paginate combined)
# ══════════════════════════════════════════════
@app.get("/products/browse")
def browse_products(
    keyword: str = Query(None,    description="Filter by keyword (optional)"),
    sort_by: str = Query("price", description="'price' or 'name'"),
    order:   str = Query("asc",   description="'asc' or 'desc'"),
    page:    int = Query(1,  ge=1,       description="Page number"),
    limit:   int = Query(4,  ge=1, le=20, description="Items per page"),
):
    # Step 1: Filter
    result = products
    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]

    # Step 2: Sort
    if sort_by in ["price", "name"]:
        result = sorted(result, key=lambda p: p[sort_by], reverse=(order == "desc"))

    # Step 3: Paginate
    total = len(result)
    start = (page - 1) * limit
    paged = result[start: start + limit]

    return {
        "keyword":     keyword,
        "sort_by":     sort_by,
        "order":       order,
        "page":        page,
        "limit":       limit,
        "total_found": total,
        "total_pages": -(-total // limit),
        "products":    paged,
    }


# ══════════════════════════════════════════════
# BONUS – GET /orders/page   (paginate orders)
# ══════════════════════════════════════════════
@app.get("/orders/page")
def get_orders_paged(
    page:  int = Query(1, ge=1,       description="Page number"),
    limit: int = Query(3, ge=1, le=20, description="Items per page"),
):
    start = (page - 1) * limit
    return {
        "page":        page,
        "limit":       limit,
        "total":       len(orders),
        "total_pages": -(-len(orders) // limit),
        "orders":      orders[start: start + limit],
    }


# ══════════════════════════════════════════════
# GET /products/{product_id}  (must stay LAST to avoid route conflicts)
# ══════════════════════════════════════════════
@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = next((p for p in products if p["product_id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product