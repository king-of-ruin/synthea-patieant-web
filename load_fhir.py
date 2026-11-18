import glob
import os
import sys

import requests

# 如果你的 Synthea 在別的位置，請改這一行
FHIR_DIR = r"C:\Users\peter\OneDrive\Desktop\synthea\output\fhir"
BASE = "http://localhost:8080/fhir"
HEADERS = {"Content-Type": "application/fhir+json"}


def main():
    # 安全檢查：伺服器已有病人就停止，避免重複載入
    r = requests.get(f"{BASE}/Patient", params={"_summary": "count"}, timeout=60)
    r.raise_for_status()
    if r.json().get("total", 0) > 0:
        print("伺服器裡已經有病人資料，為避免重複載入，程式停止。")
        print("要重新載入請先執行：docker rm -f hapi，再重新啟動伺服器。")
        sys.exit()

    files = sorted(glob.glob(os.path.join(FHIR_DIR, "*.json")))
    # 先載入機構與醫師資料，病人檔案會引用它們
    first = [f for f in files
             if os.path.basename(f).startswith(("hospitalInformation",
                                                "practitionerInformation"))]
    rest = [f for f in files if f not in first]
    ordered = first + rest

    ok, failed = 0, []
    for i, path in enumerate(ordered, 1):
        with open(path, "rb") as f:
            resp = requests.post(BASE, data=f.read(),
                                 headers=HEADERS, timeout=1200)
        name = os.path.basename(path)
        if resp.status_code in (200, 201):
            ok += 1
            print(f"[{i}/{len(ordered)}] 成功 {name}")
        else:
            failed.append(name)
            print(f"[{i}/{len(ordered)}] 失敗 {resp.status_code} {name}")

    print(f"\n完成：成功 {ok} 個檔案，失敗 {len(failed)} 個")
    for n in failed:
        print("  失敗：", n)


if __name__ == "__main__":
    main()