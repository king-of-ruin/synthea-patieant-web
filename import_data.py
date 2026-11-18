import os
import sqlite3
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
DB = os.path.join(BASE, "health.db")

SCHEMA = """
DROP TABLE IF EXISTS conditions;
DROP TABLE IF EXISTS encounters;
DROP TABLE IF EXISTS patients;

CREATE TABLE patients (
    id TEXT PRIMARY KEY,
    birthdate TEXT,
    deathdate TEXT,
    prefix TEXT,
    first_name TEXT,
    last_name TEXT,
    gender TEXT,
    race TEXT,
    ethnicity TEXT,
    city TEXT,
    state TEXT
);

CREATE TABLE encounters (
    id TEXT PRIMARY KEY,
    patient TEXT NOT NULL,
    start TEXT,
    stop TEXT,
    encounterclass TEXT,
    code TEXT,
    description TEXT,
    FOREIGN KEY (patient) REFERENCES patients(id)
);

CREATE TABLE conditions (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient TEXT NOT NULL,
    encounter TEXT,
    start TEXT,
    stop TEXT,
    code TEXT,
    description TEXT,
    FOREIGN KEY (patient) REFERENCES patients(id),
    FOREIGN KEY (encounter) REFERENCES encounters(id)
);
"""


def load(name, columns, rename=None):
    """讀 CSV，欄位轉小寫，只留下需要的欄位。"""
    path = os.path.join(DATA, name + ".csv")
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.lower() for c in df.columns]
    if rename:
        df = df.rename(columns=rename)
    return df.reindex(columns=columns)


def main():
    patients = load(
        "patients",
        ["id", "birthdate", "deathdate", "prefix", "first_name", "last_name",
         "gender", "race", "ethnicity", "city", "state"],
        rename={"first": "first_name", "last": "last_name"},
    )
    encounters = load(
        "encounters",
        ["id", "patient", "start", "stop", "encounterclass", "code", "description"],
    )
    conditions = load(
        "conditions",
        ["patient", "encounter", "start", "stop", "code", "description"],
    )

    conn = sqlite3.connect(DB)
    conn.executescript(SCHEMA)
    conn.execute("PRAGMA foreign_keys = ON")

    patients.to_sql("patients", conn, if_exists="append", index=False)
    encounters.to_sql("encounters", conn, if_exists="append", index=False)
    conditions.to_sql("conditions", conn, if_exists="append", index=False)
    conn.commit()

    # ===== 資料核對（報告第 2 題要用）=====
    print("=== 資料核對 ===")
    for name, df in [("patients", patients), ("encounters", encounters),
                     ("conditions", conditions)]:
        n_db = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"{name}: CSV 筆數 = {len(df)}, 資料庫筆數 = {n_db}")

    orphan_enc = conn.execute(
        "SELECT COUNT(*) FROM encounters WHERE patient NOT IN (SELECT id FROM patients)"
    ).fetchone()[0]
    orphan_cond = conn.execute(
        "SELECT COUNT(*) FROM conditions WHERE encounter IS NOT NULL "
        "AND encounter NOT IN (SELECT id FROM encounters)"
    ).fetchone()[0]
    print(f"找不到病人的就診筆數: {orphan_enc}")
    print(f"找不到就診的診斷筆數: {orphan_cond}")

    conn.close()
    print("完成！資料庫檔案：", DB)


if __name__ == "__main__":
    main()