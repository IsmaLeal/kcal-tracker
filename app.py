from flask import Flask, render_template, request
import sqlite3
from datetime import datetime

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

    conn = sqlite3.connect("kcal.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        food TEXT,
        total_kcal REAL,
        timestamp TEXT
    ) 
    """)
    c.execute("INSERT INTO entries (food, total_kcal, timestamp) VALUES (?, ?, ?)", (food, total_kcal, now))
    conn.commit()
    conn.close()

    return "Saved successfully!"