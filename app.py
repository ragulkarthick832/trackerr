from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

DB_NAME = "tracker.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/add-entry", methods=["POST"])
def add_entry():
    data = request.json
    entry_type = data.get("entry_type")
    quantity_ml = data.get("quantity_ml")

    conn = get_db()
    conn.execute(
        "INSERT INTO entries (entry_type, quantity_ml) VALUES (?, ?)",
        (entry_type, quantity_ml),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Added"})


@app.route("/daily-stats")
def daily_stats():
    conn = get_db()

    rows = conn.execute("""
        SELECT
            strftime('%H:%M', timestamp) as time,
            entry_type,
            quantity_ml
        FROM entries
        WHERE date(timestamp) = date('now')
        ORDER BY timestamp
    """).fetchall()

    conn.close()

    return jsonify([dict(r) for r in rows])


@app.route("/summary")
def summary():
    start = request.args.get("start")
    end = request.args.get("end")

    conn = get_db()

    rows = conn.execute("""
        SELECT entry_type, SUM(quantity_ml) as total
        FROM entries
        WHERE timestamp BETWEEN ? AND ?
        GROUP BY entry_type
    """, (start, end)).fetchall()

    conn.close()

    result = {"water": 0, "urine": 0}

    for row in rows:
        result[row["entry_type"]] = row["total"]

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)