import os
import sqlite3
import sys

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "health.db")
FHIR = "http://localhost:8080/fhir"
SNOMED = "http://snomed.info/sct"


def fhir_count(resource, params):
    p = dict(params)
    p["_summary"] = "count"
    r = requests.get(f"{FHIR}/{resource}", params=p, timeout=120)
    r.raise_for_status()
    return r.json()["total"]


def show(label, sql_value, fhir_value):
    same = "一致 ✅" if sql_value == fhir_value else "不一致 ❌"
    print(f"{label:<28} SQL = {sql_value:<6} FHIR = {fhir_value:<6} {same}")


def main():
    conn = sqlite3.connect(DB)

    # 沒給代碼：列出病人數最多的診斷，讓你挑一個
    if len(sys.argv) < 2:
        print("病人數最多的前 10 個診斷（代碼 / 病人數 / 名稱）：")
        rows = conn.execute(
            "SELECT code, COUNT(DISTINCT patient) AS n, description "
            "FROM conditions WHERE description LIKE '%(disorder)%' "
            "GROUP BY code, description ORDER BY n DESC LIMIT 10"
        ).fetchall()
        for code, n, desc in rows:
            print(f"{code}  {n:>4}  {desc}")
        print("\n挑一個代碼，執行：python compare_fhir_sql.py 代碼")
        return

    code = sys.argv[1]
    desc = conn.execute(
        "SELECT description FROM conditions WHERE code = ? LIMIT 1", (code,)
    ).fetchone()
    print(f"診斷代碼 {code}：{desc[0] if desc else '（資料庫查無此代碼）'}\n")

    sql_total = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    sql_pat = conn.execute(
        "SELECT COUNT(DISTINCT patient) FROM conditions WHERE code = ?", (code,)
    ).fetchone()[0]
    sql_cond = conn.execute(
        "SELECT COUNT(*) FROM conditions WHERE code = ?", (code,)
    ).fetchone()[0]
    conn.close()

    fhir_total = fhir_count("Patient", {})
    fhir_pat = fhir_count(
        "Patient", {"_has:Condition:patient:code": f"{SNOMED}|{code}"}
    )
    fhir_cond = fhir_count("Condition", {"code": f"{SNOMED}|{code}"})

    show("病人總數", sql_total, fhir_total)
    show("有此診斷的病人數", sql_pat, fhir_pat)
    show("此診斷的紀錄筆數", sql_cond, fhir_cond)


if __name__ == "__main__":
    main()