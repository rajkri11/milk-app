from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

def get_db():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        rate REAL,
        phone TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        date TEXT,
        liters REAL
    )
    ''')

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers")
    customers = cur.fetchall()
    return render_template("index.html", customers=customers)

@app.route("/add_customer", methods=["GET", "POST"])
def add_customer():
    if request.method == "POST":
        name = request.form["name"]
        rate = request.form["rate"]
        phone = request.form["phone"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO customers (name, rate, phone) VALUES (?, ?, ?)",
            (name, rate, phone)
        )
        conn.commit()
        return redirect("/")

    return render_template("add_customer.html")

@app.route("/add_sale", methods=["POST"])
def add_sale():
    customer_id = request.form["customer_id"]
    liters = request.form["liters"]
    date = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sales (customer_id, date, liters) VALUES (?, ?, ?)",
        (customer_id, date, liters)
    )
    conn.commit()

    return redirect("/")

@app.route("/bill/<int:customer_id>")
def bill(customer_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT name, rate, phone FROM customers WHERE id=?", (customer_id,))
    customer = cur.fetchone()

    month = datetime.now().strftime("%Y-%m")

    cur.execute('''
        SELECT date, liters FROM sales
        WHERE customer_id=? AND date LIKE ?
    ''', (customer_id, f"{month}%"))

    sales = cur.fetchall()

    total_liters = sum([s[1] for s in sales])
    total_amount = total_liters * customer[1]

    # WhatsApp message
    message = f"Milk Bill for {customer[0]}\\n\\n"
    for s in sales:
        message += f"{s[0]} - {s[1]}L\\n"

    message += f"\\nTotal: {total_liters}L"
    message += f"\\nAmount: ₹{total_amount}"

    whatsapp_url = f"https://wa.me/{customer[2]}?text={message}"

    return render_template(
        "bill.html",
        customer=customer,
        sales=sales,
        total_liters=total_liters,
        total_amount=total_amount,
        whatsapp_url=whatsapp_url
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)