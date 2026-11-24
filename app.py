import os
import sqlite3
import secrets
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "restaurant.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-development-secret-key")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")

MENU_SEED = [
    ("South Indian", "Idli (2 pcs)", "Soft steamed idlis served with sambar and chutneys.", 45, "🌿", "popular"),
    ("South Indian", "Ghee Pongal", "Comforting rice and lentil pongal finished with ghee and pepper.", 95, "🍚", "veg"),
    ("South Indian", "Masala Dosa", "Crisp dosa with spiced potato masala, sambar and chutneys.", 110, "🥞", "popular"),
    ("South Indian", "Mini Tiffin", "A satisfying combo of idli, mini dosa, pongal and vada.", 145, "🍽️", "popular"),
    ("Meals", "South Indian Meals", "Rice, seasonal sides, kootu, poriyal, sambar, rasam and curd.", 160, "🍛", "veg"),
    ("Meals", "Curd Rice", "Creamy curd rice tempered with mustard and curry leaves.", 85, "🥣", "veg"),
    ("Starters", "Paneer 65", "Crispy paneer tossed with South Indian spices.", 165, "🧀", "veg"),
    ("Starters", "Chicken 65", "Crispy, spicy chicken bites with curry leaves.", 190, "🍗", "popular"),
    ("Main Course", "Chicken Biryani", "Aromatic dum-style biryani served with raita.", 210, "🍗", "popular"),
    ("Main Course", "Veg Biryani", "Fragrant basmati rice layered with vegetables and spices.", 165, "🍲", "veg"),
    ("Main Course", "Parotta (2) + Salna", "Flaky layered parottas with house-style salna.", 95, "🥘", "popular"),
    ("Beverages", "Filter Coffee", "Freshly brewed South Indian filter coffee.", 35, "☕", "popular"),
    ("Beverages", "Fresh Lime Soda", "Refreshing lime with soda, sweet or salted.", 55, "🍋", "veg"),
    ("Desserts", "Gulab Jamun (2)", "Warm soft dumplings in fragrant sugar syrup.", 65, "🍮", "veg"),
]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL,
            name TEXT NOT NULL, description TEXT, price REAL NOT NULL,
            emoji TEXT DEFAULT '🍽️', tag TEXT DEFAULT '')""")
        con.execute("""CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, order_code TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL, phone TEXT NOT NULL, order_type TEXT NOT NULL,
            address TEXT, notes TEXT, items_json TEXT NOT NULL, subtotal REAL NOT NULL,
            delivery_fee REAL NOT NULL, total REAL NOT NULL, status TEXT NOT NULL,
            created_at TEXT NOT NULL)""")
        count = con.execute("SELECT COUNT(*) FROM menu").fetchone()[0]
        if count == 0:
            con.executemany("INSERT INTO menu(category,name,description,price,emoji,tag) VALUES(?,?,?,?,?,?)", MENU_SEED)
        con.commit()

init_db()

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/menu")
def get_menu():
    with db() as con:
        rows = con.execute("SELECT * FROM menu ORDER BY category, id").fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/orders")
def create_order():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    order_type = data.get("order_type", "pickup")
    address = str(data.get("address", "")).strip()
    notes = str(data.get("notes", "")).strip()
    items = data.get("items", [])

    if len(name) < 2 or not phone or not phone.replace("+", "").replace("-", "").replace(" ", "").isdigit():
        return jsonify(error="Enter a valid name and phone number."), 400
    if order_type not in ("pickup", "delivery"):
        return jsonify(error="Choose pickup or delivery."), 400
    if order_type == "delivery" and len(address) < 8:
        return jsonify(error="Please enter your complete delivery address."), 400
    if not isinstance(items, list) or not items:
        return jsonify(error="Your cart is empty."), 400

    clean_items, subtotal = [], 0
    with db() as con:
        for item in items:
            try:
                menu_id, qty = int(item["id"]), int(item["qty"])
            except (KeyError, ValueError, TypeError):
                return jsonify(error="Invalid cart item."), 400
            if qty < 1 or qty > 20:
                return jsonify(error="Quantity must be between 1 and 20."), 400
            row = con.execute("SELECT id,name,price FROM menu WHERE id=?", (menu_id,)).fetchone()
            if not row:
                return jsonify(error="A selected menu item is no longer available."), 400
            line_total = round(row["price"] * qty, 2)
            subtotal += line_total
            clean_items.append({"id": row["id"], "name": row["name"], "price": row["price"], "qty": qty, "line_total": line_total})

        delivery_fee = 30 if order_type == "delivery" else 0
        total = round(subtotal + delivery_fee, 2)
        code = "AFC-" + secrets.token_hex(3).upper()
        created = datetime.now().strftime("%d %b %Y, %I:%M %p")
        con.execute("""INSERT INTO orders(order_code,customer_name,phone,order_type,address,notes,
            items_json,subtotal,delivery_fee,total,status,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (code, name, phone, order_type, address, notes, __import__("json").dumps(clean_items),
             subtotal, delivery_fee, total, "Received", created))
        con.commit()
    return jsonify(message="Order placed successfully!", order_code=code, total=total), 201

@app.get("/api/orders/<code>")
def track_order(code):
    with db() as con:
        row = con.execute("SELECT order_code,status,created_at,order_type,total FROM orders WHERE order_code=?",
                          (code.upper(),)).fetchone()
    if not row:
        return jsonify(error="We couldn't find that order. Check the order code and try again."), 404
    return jsonify(dict(row))

@app.get("/admin/login")
def admin_login():
    return render_template("admin_login.html")

@app.post("/admin/login")
def admin_login_post():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if ADMIN_PASSWORD_HASH:
        valid = username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password)
    else:
        valid = username == ADMIN_USERNAME and password == os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")
    if valid:
        session["admin"] = True
        return redirect(url_for("admin_dashboard"))
    flash("Invalid login details.", "error")
    return redirect(url_for("admin_login"))

@app.get("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.get("/admin")
@admin_required
def admin_dashboard():
    with db() as con:
        orders = con.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 100").fetchall()
    import json
    return render_template("admin.html", orders=[{**dict(r), "items": json.loads(r["items_json"])} for r in orders])

@app.post("/admin/orders/<int:order_id>/status")
@admin_required
def update_status(order_id):
    status = (request.get_json(silent=True) or {}).get("status")
    allowed = {"Received", "Preparing", "Ready", "Out for delivery", "Completed", "Cancelled"}
    if status not in allowed:
        return jsonify(error="Invalid status."), 400
    with db() as con:
        cur = con.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        con.commit()
    if cur.rowcount == 0:
        return jsonify(error="Order not found."), 404
    return jsonify(message="Status updated.")

@app.errorhandler(404)
def not_found(_):
    return render_template("index.html"), 404

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
