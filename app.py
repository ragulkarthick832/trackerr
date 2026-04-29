from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime, time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

IST = ZoneInfo("Asia/Kolkata")

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client["water_tracker"]
entries = db["entries"]


def log(msg):
    print(f"[{datetime.now(IST).isoformat()}] {msg}")


@app.route("/")
def home():
    log("Homepage requested")
    return render_template("index.html")


@app.route("/add-entry", methods=["POST"])
def add_entry():
    data = request.json

    entry_type = data.get("entry_type")
    quantity_ml = int(data.get("quantity_ml"))
    timestamp_str = data.get("timestamp")

    if timestamp_str:
        timestamp = datetime.fromisoformat(timestamp_str).replace(tzinfo=IST)
    else:
        timestamp = datetime.now(IST)

    doc = {
        "entry_type": entry_type,
        "quantity_ml": quantity_ml,
        "timestamp": timestamp
    }

    result = entries.insert_one(doc)

    log(f"Inserted {entry_type} {quantity_ml}ml at {timestamp}")

    return jsonify({"message": "Added", "id": str(result.inserted_id)})


@app.route("/daily-stats")
def daily_stats():
    today = datetime.now(IST).date()

    start_of_day = datetime.combine(today, time.min, tzinfo=IST)
    end_of_day = datetime.combine(today, time.max, tzinfo=IST)

    docs = list(entries.find({
        "timestamp": {
            "$gte": start_of_day,
            "$lte": end_of_day
        }
    }).sort("timestamp", 1))

    result = []

    for d in docs:
        result.append({
            "time": d["timestamp"].strftime("%H:%M"),
            "entry_type": d["entry_type"],
            "quantity_ml": d["quantity_ml"]
        })

    log(f"Returned {len(result)} daily stats")

    return jsonify(result)


@app.route("/summary")
def summary():
    start = datetime.fromisoformat(request.args.get("start")).replace(tzinfo=IST)
    end = datetime.fromisoformat(request.args.get("end")).replace(tzinfo=IST)

    docs = list(entries.find({
        "timestamp": {
            "$gte": start,
            "$lte": end
        }
    }))

    water = 0
    urine = 0

    for d in docs:
        if d["entry_type"] == "water":
            water += d["quantity_ml"]
        elif d["entry_type"] == "urine":
            urine += d["quantity_ml"]

    log(f"Summary requested: Water={water}, Urine={urine}")

    return jsonify({
        "water": water,
        "urine": urine
    })


@app.route("/clear-all", methods=["POST"])
def clear_all():
    result = entries.delete_many({})
    log(f"Deleted {result.deleted_count} entries")

    return jsonify({
        "message": "All entries cleared",
        "deleted_count": result.deleted_count
    })


if __name__ == "__main__":
    app.run(debug=True)
