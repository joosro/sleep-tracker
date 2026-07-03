import os
from datetime import date, datetime
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client

from sleep_metrics import calculate_sleep_metrics

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def entry():
    message = None
    if request.method == "POST":
        record = {
            "date": request.form["date"],
            "ttb": int(request.form["ttb"]),
            "sl": int(request.form["sl"]),
            "noa": int(request.form["noa"]),
            "waso": int(request.form["waso"]),
            "ema": int(request.form["ema"]),
            "tob": int(request.form["tob"]),
            "notes": request.form.get("notes", "")
        }
        supabase.table("sleep_log").upsert(record, on_conflict="date").execute()
        message = f"Saved entry for {record['date']}!"

    return render_template("entry.html", today=date.today().isoformat(), message=message)

@app.route("/history")
def history():
    result = supabase.table("sleep_log").select("*").order("date", desc=True).limit(30).execute()
    records = result.data

    for r in records:
        record_date = datetime.strptime(r["date"], "%Y-%m-%d").date()
        metrics = calculate_sleep_metrics(
            record_date, r["ttb"], r["sl"], r["noa"], r["waso"], r["ema"], r["tob"]
        )
        r["tib"] = metrics["tib_minutes"]
        r["tst"] = metrics["tst_minutes"]
        r["se"] = metrics["se_percent"]

    return render_template("history.html", records=records)

@app.route("/edit/<entry_date>", methods=["GET", "POST"])
def edit(entry_date):
    if request.method == "POST":
        record = {
            "date": entry_date,
            "ttb": int(request.form["ttb"]),
            "sl": int(request.form["sl"]),
            "noa": int(request.form["noa"]),
            "waso": int(request.form["waso"]),
            "ema": int(request.form["ema"]),
            "tob": int(request.form["tob"]),
            "notes": request.form.get("notes", "")
        }
        supabase.table("sleep_log").upsert(record, on_conflict="date").execute()
        return redirect(url_for("history"))

    result = supabase.table("sleep_log").select("*").eq("date", entry_date).execute()
    record = result.data[0] if result.data else None
    return render_template("edit.html", record=record)

@app.route("/delete/<entry_date>", methods=["POST"])
def delete(entry_date):
    supabase.table("sleep_log").delete().eq("date", entry_date).execute()
    return redirect(url_for("history"))

@app.route("/dashboard")
def dashboard():
    result = supabase.table("sleep_log").select("*").order("date", desc=False).execute()
    records = result.data

    for r in records:
        record_date = datetime.strptime(r["date"], "%Y-%m-%d").date()
        metrics = calculate_sleep_metrics(
            record_date, r["ttb"], r["sl"], r["noa"], r["waso"], r["ema"], r["tob"]
        )
        r["tib"] = metrics["tib_minutes"]
        r["tst"] = metrics["tst_minutes"]
        r["se"] = metrics["se_percent"]
        r["tta"] = (r["sl"] or 0) + (r["waso"] or 0) + (r["ema"] or 0)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W-SUN").apply(lambda p: p.start_time.date().isoformat())

    weekly = df.groupby("week").agg({
        "se": "mean",
        "noa": "mean",
        "tst": "mean",
        "tib": "mean",
        "sl": "mean",
        "waso": "mean",
        "ema": "mean",
        "tta": "mean",
    }).reset_index().sort_values("week")

    for col in ["se", "noa", "tst", "tib", "sl", "waso", "ema", "tta"]:
        weekly[col] = weekly[col].round(1)

    weekly_data = weekly.to_dict(orient="records")

    return render_template("dashboard.html", weekly_data=weekly_data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
