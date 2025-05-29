from flask import Flask, render_template, request
import psycopg2
import os
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    weight = request.form["weight"]
    total_kcal = request.form["total_kcal"]
    kcal_per_100g = request.form["kcal"]
    food = request.form["food"]

    if total_kcal:
        total_kcal = int(total_kcal)
    elif kcal_per_100g and weight:
        kcal_per_100g = int(kcal_per_100g)
        weight = int(weight)
        total_kcal = weight * kcal_per_100g / 100
    else:
        return "Error: missing required data", 400

    total_kcal = round(total_kcal)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        food TEXT,
        total_kcal REAL,
        timestamp TEXT
    ) 
    """)
    c.execute("INSERT INTO entries (food, total_kcal, timestamp) VALUES (%s, %s, %s)", (food, total_kcal, now))
    conn.commit()
    conn.close()

    return "Saved successfully!"

@app.route("/view")
def view():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("SELECT food, total_kcal, timestamp FROM entries ORDER BY timestamp DESC")
    entries = c.fetchall()
    conn.close()
    return render_template("view.html", entries=entries)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
