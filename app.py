from flask import Flask, render_template, request, Response, url_for, redirect
import psycopg2
import os
from datetime import datetime, timedelta
import csv
from io import StringIO

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

    return render_template("index.html", message="Saved successfully!")

@app.route("/view")
def view():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("SELECT food, total_kcal, timestamp FROM entries ORDER BY timestamp DESC")
    entries = c.fetchall()
    conn.close()
    return render_template("view.html", entries=entries)

@app.route("/download")
def download():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("SELECT food, total_kcal, timestamp FROM entries ORDER BY timestamp DESC")
    entries = c.fetchall()
    conn.close()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["food", "total_kcal", "timestamp"])
    cw.writerows(entries)
    
    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=entries.csv"}
    )

@app.route("/counter")
def count_kcal():
    today = datetime.now()
    today_iso = today.strftime("%Y-%m-%d")
    today_display = today.strftime("%d/%m")
    
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    
    c.execute("""
        SELECT SUM(total_kcal)
        FROM entries
        WHERE timestamp::date = %s
    """, (today_iso,))

    todays_result = c.fetchone()[0]
    todays_total = todays_result if todays_result else 0

    previous_results = {}
    for i in range(1, 16):
        date = today - timedelta(days=i)
        date_iso = date.strftime("%Y-%m-%d")
        c.execute("""
            SELECT SUM(total_kcal)
            FROM entries
            WHERE timestamp::date = %s
        """, (date_iso,))
        value = c.fetchone()[0]
        previous_results[date.strftime("%d/%m")] = value if value else 0
    
    conn.close()
    return render_template("counter.html", total_kcal=todays_total, today=today_display, prev=previous_results)

@app.route("/delete", methods=["GET", "POST"])
def delete():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()

    if request.method == "POST":
        timestamps_to_delete = request.form.getlist("delete_ids")
        for ts in timestamps_to_delete:
            c.execute("DELETE FROM entries WHERE timestamp = %s", (ts,))
        conn.commit()
        conn.close()
        return redirect(url_for("delete")) # refresh the list
    
    c.execute("""
        SELECT food, total_kcal, timestamp
        FROM entries
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    last_entries = c.fetchall()
    conn.close()

    return render_template("delete.html", entries=last_entries)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
