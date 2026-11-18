import os
import sqlite3
from datetime import date

from flask import Flask, render_template, request, abort

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "health.db")
REF_DATE = date(2026, 11, 1)  # 作業指定的參考日期，年齡以此計算

AGE_GROUPS = {
    "0-17": (0, 17),
    "18-39": (18, 39),
    "40-64": (40, 64),
    "65+": (65, 200),
}

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def calc_age(birthdate):
    b = date.fromisoformat(birthdate[:10])
    years = REF_DATE.year - b.year
    if (REF_DATE.month, REF_DATE.day) < (b.month, b.day):
        years -= 1
    return years


@app.route("/")
def patient_list():
    gender = request.args.get("gender", "")
    age_group = request.args.get("age_group", "")

    sql = ("SELECT id, first_name, last_name, gender, birthdate, deathdate "
           "FROM patients")
    params = []
    if gender in ("M", "F"):
        sql += " WHERE gender = ?"
        params.append(gender)
    sql += " ORDER BY last_name, first_name"

    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    patients = []
    for r in rows:
        age = calc_age(r["birthdate"])
        if age_group in AGE_GROUPS:
            low, high = AGE_GROUPS[age_group]
            if not (low <= age <= high):
                continue
        patients.append({
            "id": r["id"],
            "name": f'{r["first_name"]} {r["last_name"]}',
            "gender": r["gender"],
            "birthdate": r["birthdate"],
            "age": age,
            "deceased": bool(r["deathdate"]),
        })

    return render_template(
        "patients.html",
        patients=patients,
        gender=gender,
        age_group=age_group,
        age_groups=list(AGE_GROUPS.keys()),
        ref_date=REF_DATE.isoformat(),
    )


@app.route("/patient/<patient_id>")
def patient_detail(patient_id):
    conn = get_db()
    patient = conn.execute(
        "SELECT * FROM patients WHERE id = ?", (patient_id,)
    ).fetchone()
    if patient is None:
        conn.close()
        abort(404)

    encounters = conn.execute(
        "SELECT id, start, encounterclass, description "
        "FROM encounters WHERE patient = ? ORDER BY start",
        (patient_id,),
    ).fetchall()

    cond_rows = conn.execute(
        "SELECT encounter, description FROM conditions WHERE patient = ?",
        (patient_id,),
    ).fetchall()
    conn.close()

    conditions_by_enc = {}
    for c in cond_rows:
        conditions_by_enc.setdefault(c["encounter"], []).append(c["description"])

    visits = []
    for e in encounters:
        visits.append({
            "date": (e["start"] or "")[:10],
            "type": e["encounterclass"],
            "description": e["description"],
            "diagnoses": conditions_by_enc.get(e["id"], []),
        })

    info = {
        "name": f'{patient["first_name"]} {patient["last_name"]}',
        "gender": patient["gender"],
        "birthdate": patient["birthdate"],
        "age": calc_age(patient["birthdate"]),
        "deathdate": patient["deathdate"],
        "city": patient["city"],
        "state": patient["state"],
    }
    return render_template("patient_detail.html", p=info, visits=visits)


if __name__ == "__main__":
    app.run(debug=True)