"""
RestoCopilot AI - Local Kitchen Database & Inventory Schema
Handles:
- Perishable Inventory & Expiry Tracking (Vegetables, Meats, Dairy)
- Automated Ingredient Deduction Engine (Recipe BOM to Raw Ingredient Mapping)
- Active Kitchen Orders (Pending, Cooking, Ready)
- Customer Review Log & Sentiment Triage
"""
import sqlite3
import os
import re
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "kitchen_vault.db")

# Recipe Bill of Materials (BOM) mapping: How much raw ingredient each dish uses
RECIPE_BOM = {
    # Dish keyword -> [(Ingredient Name in inventory, deduction_qty, unit)]
    "egg": [("Farm Fresh Eggs", 2.0, "pcs")],
    "omelette": [("Farm Fresh Eggs", 3.0, "pcs")],
    "scramble": [("Farm Fresh Eggs", 2.0, "pcs")],
    "chicken": [("Boneless Chicken Breast", 0.25, "kg")],
    "murgh": [("Boneless Chicken Breast", 0.25, "kg")],
    "paneer": [("Fresh Paneer", 0.20, "kg")],
    "mushroom": [("Button Mushrooms", 0.15, "kg")],
    "naan": [("Maida & Sourdough Dough", 0.12, "kg")],
    "bread": [("Maida & Sourdough Dough", 0.10, "kg")],
    "cheese": [("English Cheddar Cheese", 0.05, "kg")],
    "makhani": [("Heavy Cooking Cream", 0.05, "litres"), ("Roma Tomatoes", 0.15, "kg")],
    "tikka": [("Roma Tomatoes", 0.10, "kg")]
}

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Inventory Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT NOT NULL,
        safety_threshold REAL NOT NULL,
        expiry_date TEXT NOT NULL,
        freshness_status TEXT DEFAULT 'Fresh',
        unit_cost REAL NOT NULL
    )
    """)
    
    # 2. Kitchen Orders (Voice KDS Table)
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_code TEXT NOT NULL,
        table_or_platform TEXT NOT NULL,
        customer_phone TEXT,
        items_json TEXT NOT NULL,
        deductions_json TEXT,  -- Log of raw ingredients deducted
        raw_receipt_text TEXT,
        status TEXT DEFAULT 'PENDING',
        created_at TEXT NOT NULL,
        announced INTEGER DEFAULT 0
    )
    """)
    
    # 3. Customer Reviews & Sentiment Triage Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        phone TEXT,
        order_ref TEXT,
        rating INTEGER,
        feedback_text TEXT,
        sentiment TEXT,
        auto_action TEXT,
        response_draft TEXT,
        created_at TEXT NOT NULL
    )
    """)
    
    conn.commit()
    
    # Auto-migrate orders table schema if deductions_json is missing
    c.execute("PRAGMA table_info(orders)")
    order_cols = [row[1] for row in c.fetchall()]
    if "deductions_json" not in order_cols:
        c.execute("ALTER TABLE orders ADD COLUMN deductions_json TEXT")
        conn.commit()
    
    # Check count
    c.execute("SELECT COUNT(*) as count FROM inventory")
    if c.fetchone()["count"] == 0:
        seed_inventory(conn)
        
    conn.close()

def reset_inventory_vault():
    """Restores inventory table to fresh baseline data for demo / testing."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM inventory")
    seed_inventory(conn)
    conn.close()

def deduct_ingredients_for_order(dishes: list) -> list:
    """
    Automated logic: Parses ordered dishes, calculates recipe BOM, 
    and deducts the real stock from SQLite inventory table.
    Returns a log of what was deducted and alerts if stock went critical.
    """
    conn = get_connection()
    c = conn.cursor()
    deduction_logs = []

    for dish in dishes:
        dish_lower = dish.lower()
        # Find matching quantity multiplier (e.g. "3x Garlic Butter Naan" -> multiplier = 3)
        qty_match = re.search(r"^(\d+)", dish.strip())
        multiplier = float(qty_match.group(1)) if qty_match else 1.0

        for keyword, ingredients in RECIPE_BOM.items():
            if keyword in dish_lower:
                for ing_name, base_qty, unit in ingredients:
                    total_to_deduct = round(base_qty * multiplier, 2)
                    
                    # Deduct from inventory
                    c.execute("SELECT quantity, safety_threshold FROM inventory WHERE item_name = ?", (ing_name,))
                    row = c.fetchone()
                    if row:
                        curr_qty = row["quantity"]
                        threshold = row["safety_threshold"]
                        new_qty = max(0.0, round(curr_qty - total_to_deduct, 2))
                        
                        # Recalculate status
                        new_status = "Fresh"
                        if new_qty <= 0:
                            new_status = "OUT OF STOCK"
                        elif new_qty <= threshold:
                            new_status = "Critical Low Stock"
                        else:
                            new_status = "Optimal"
                            
                        c.execute("""
                        UPDATE inventory 
                        SET quantity = ?, freshness_status = ? 
                        WHERE item_name = ?
                        """, (new_qty, new_status, ing_name))
                        
                        deduction_logs.append({
                            "dish": dish,
                            "ingredient": ing_name,
                            "deducted": f"-{total_to_deduct} {unit}",
                            "remaining": f"{new_qty} {unit}",
                            "status": new_status
                        })

    conn.commit()
    conn.close()
    return deduction_logs

def update_inventory_item(item_name: str, new_qty: float, safety_threshold: float = None, unit_cost: float = None, expiry_date: str = None) -> bool:
    """Counter / Manager stock update function."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT safety_threshold, unit_cost, expiry_date FROM inventory WHERE item_name = ?", (item_name,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
        
    threshold = safety_threshold if safety_threshold is not None else row["safety_threshold"]
    cost = unit_cost if unit_cost is not None else row["unit_cost"]
    exp = expiry_date if expiry_date is not None else row["expiry_date"]
    
    # Calculate freshness status
    if new_qty <= 0:
        status = "OUT OF STOCK"
    elif new_qty <= threshold:
        status = "Critical Low Stock"
    else:
        status = "Optimal"
        
    c.execute("""
    UPDATE inventory 
    SET quantity = ?, safety_threshold = ?, unit_cost = ?, expiry_date = ?, freshness_status = ?
    WHERE item_name = ?
    """, (round(new_qty, 2), round(threshold, 2), round(cost, 2), exp, status, item_name))
    conn.commit()
    conn.close()
    return True

def restock_inventory_item(item_name: str, add_qty: float) -> bool:
    """Adds stock quantity to existing inventory."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT quantity, safety_threshold FROM inventory WHERE item_name = ?", (item_name,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    new_qty = max(0.0, round(row["quantity"] + add_qty, 2))
    threshold = row["safety_threshold"]
    status = "OUT OF STOCK" if new_qty <= 0 else ("Critical Low Stock" if new_qty <= threshold else "Optimal")
    c.execute("UPDATE inventory SET quantity = ?, freshness_status = ? WHERE item_name = ?", (new_qty, status, item_name))
    conn.commit()
    conn.close()
    return True

def add_new_inventory_item(item_name: str, category: str, quantity: float, unit: str, safety_threshold: float, expiry_date: str, unit_cost: float) -> bool:
    """Adds a new ingredient to the inventory vault."""
    conn = get_connection()
    c = conn.cursor()
    status = "OUT OF STOCK" if quantity <= 0 else ("Critical Low Stock" if quantity <= safety_threshold else "Optimal")
    c.execute("""
    INSERT OR REPLACE INTO inventory (item_name, category, quantity, unit, safety_threshold, expiry_date, freshness_status, unit_cost)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (item_name.strip(), category.strip(), round(quantity, 2), unit.strip(), round(safety_threshold, 2), expiry_date, status, round(unit_cost, 2)))
    conn.commit()
    conn.close()
    return True

def seed_inventory(conn):
    today = datetime.now()
    seed_data = [
        ("Farm Fresh Eggs", "Perishable Poultry", 12.0, "pcs", 4.0, (today + timedelta(days=3)).strftime("%Y-%m-%d"), "Optimal", 7.0),
        ("Fresh Paneer", "Dairy", 2.5, "kg", 1.0, (today + timedelta(days=2)).strftime("%Y-%m-%d"), "Expires Soon", 360.0),
        ("Boneless Chicken Breast", "Perishable Meat", 5.0, "kg", 2.0, (today + timedelta(days=2)).strftime("%Y-%m-%d"), "Optimal", 280.0),
        ("Button Mushrooms", "Fresh Veggie", 1.5, "kg", 0.5, (today + timedelta(days=1)).strftime("%Y-%m-%d"), "Expires Soon", 180.0),
        ("English Cheddar Cheese", "Dairy", 1.8, "kg", 0.5, (today + timedelta(days=5)).strftime("%Y-%m-%d"), "Optimal", 650.0),
        ("Maida & Sourdough Dough", "Bakery", 10.0, "kg", 3.0, (today + timedelta(days=2)).strftime("%Y-%m-%d"), "Optimal", 55.0),
        ("Roma Tomatoes", "Fresh Veggie", 6.0, "kg", 2.0, (today + timedelta(days=3)).strftime("%Y-%m-%d"), "Optimal", 40.0),
        ("Heavy Cooking Cream", "Dairy", 2.0, "litres", 1.0, (today + timedelta(days=2)).strftime("%Y-%m-%d"), "Expires Soon", 220.0)
    ]
    conn.executemany("""
    INSERT INTO inventory (item_name, category, quantity, unit, safety_threshold, expiry_date, freshness_status, unit_cost)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, seed_data)
    conn.commit()

if __name__ == "__main__":
    init_db()
    print("Kitchen Vault database initialized successfully.")
