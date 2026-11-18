# Synthea 合成病人查詢網頁

用 Synthea 產生 100 位「非真人」的合成病人，匯入 SQLite 資料庫，
並以 Flask 做出可篩選病人、查看就診紀錄的網頁。

> 本專案全程只使用 Synthea 產生的合成資料，沒有任何真實病人資料。
** 線上展示：https://synthea-patieant-web.onrender.com **
（免費主機閒置 15 分鐘後會休眠，第一次開啟可能需要等約 1 分鐘。）

## 環境需求

- Windows 10/11（Mac/Linux 的指令差異見各步驟備註）
- JDK 17 以上（執行 Synthea 用）
- Python 3.10 以上
- Git

- Docker Desktop（只有做 FHIR 比對才需要）

確認版本：

```
java -version
python --version (若python不行 改成py重試)
git --version
```

## 專案結構

```
synthea-patieant-web/
├─ data/                  Synthea 產生的 CSV（共 5 個）
├─ templates/             網頁模板（patients、patient_detail、stats）
├─ import_data.py         匯入資料到 SQLite，並印出資料核對結果
├─ app.py                 Flask 網頁程式
├─ load_fhir.py           把 Synthea 的 FHIR JSON 載入 HAPI FHIR
├─ compare_fhir_sql.py    以 FHIR 與 SQL 查同一題並比較
├─ requirements.txt       Python 套件清單
└─ README.md
```

## 安裝與執行步驟

### 1. 下載本專案

```
git clone https://github.com/king-of-ruin/synthea-patieant-web.git
cd synthea-patient-web
```

### 2. 建立 Python 虛擬環境並安裝套件

```
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

（Mac/Linux：`source venv/bin/activate`。若 PowerShell 擋住指令碼，先執行
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`。）

### 3. 用 Synthea 產生資料

在專案** 資料夾外面 **下載並執行 Synthea：

```
cd ..
git clone https://github.com/synthetichealth/synthea.git
cd synthea
.\run_synthea.bat -p 100 -s 2026 -r 20261101 --exporter.csv.export=true
```

（Mac/Linux：`./run_synthea -p 100 -s 2026 -r 20261101 --exporter.csv.export=true`）

參數說明：`-p 100` 人數、`-s 2026` 亂數種子、`-r 20261101` 參考日期 2026-11-01，
`--exporter.csv.export=true` 開啟 CSV 輸出。

完成後 `synthea/output/csv/` 會有 CSV 檔，`synthea/output/fhir/` 會有 FHIR JSON。

### 4. 複製 CSV 到專案的 data 資料夾

把 `synthea/output/csv/` 裡的 `patients.csv`、`encounters.csv`、`conditions.csv`、`medications.csv`、`observations.csv`複製到本專案的 `data/` 資料夾（已附在 repo 內可略過此步）。

### 5. 匯入資料庫

回到專案資料夾，並確認虛擬環境已啟動（終端機最前面有 `(venv)`）：

```
python import_data.py (若python不行 改成py重試)
```

會建立 `health.db`，並印出各表的 CSV 筆數與資料庫筆數，以及孤兒資料檢查結果。

### 6. 啟動網頁

```
python app.py (若python不行 改成py重試)
```

瀏覽器開啟 http://127.0.0.1:5000 。按 Ctrl+C 可停止伺服器。

### 7.（選做）FHIR 與 SQL 比對

1. 安裝並開啟 Docker Desktop，啟動 HAPI FHIR 伺服器：

```
docker run -d --name hapi -p 8080:8080 hapiproject/hapi:latest
```

等 1 到 2 分鐘，開啟 http://localhost:8080/fhir/metadata 能看到內容即可。

2. 用編輯器開啟 `load_fhir.py`，把 `FHIR_DIR` 改成你自己的 `synthea/output/fhir` 路徑，然後載入資料（只能執行一次，約需 10 到 30 分鐘）：

```
python load_fhir.py (若python不行 改成py重試)
```

3. 列出病人數最多的診斷，挑一個代碼後比較：

```
python compare_fhir_sql.py          (若python不行 改成py重試)
python compare_fhir_sql.py 診斷代碼  (若python不行 改成py重試)
```

程式會比較「病人總數」、「有此診斷的病人數」、「此診斷的紀錄筆數」，並標示 SQL 與 FHIR 是否一致。

常用 Docker 指令：`docker stop hapi`（停止）、`docker start hapi`（再次啟動）、
`docker rm -f hapi`（刪除，要重新載入資料時使用）。

## 功能

- ** 病人清單頁（/）**：列出所有病人，可依性別、年齡區間篩選（年齡以 2026-11-01 計算）。
- - ** 病人詳細頁（/patient/病人ID）**：依日期由早到晚顯示就診日期、就診類型、診斷，並列出用藥紀錄與檢驗值（檢驗值顯示最近 50 筆）。
- ** 年齡層統計圖（/stats）**：各年齡層男女人數長條圖。
- **FHIR 與 SQL 比對 **：用 HAPI FHIR 與 SQL 查同一個問題並比較結果。
- ** 公開網址（B1）**：部署在 Render，見下方「部署」。

## 部署

部署在 Render（免費 Web Service），設定如下：

- Build Command：`pip install -r requirements.txt && python import_data.py` 
- Start Command：`gunicorn app:app`
- 環境變數：`PYTHON_VERSION` 設為與本機相同的 Python 版本

`health.db` 不放進 Git，而是在部署時由 `import_data.py` 讀取 `data/` 的 CSV 自動建立。

## 資料表關係

- `patients`（主鍵 `id`）
- `encounters`（主鍵 `id`，外鍵 `patient` → `patients.id`）
- `conditions`（外鍵 `patient` → `patients.id`，外鍵 `encounter` → `encounters.id`）

- `medications`（外鍵 `patient` → `patients.id`，外鍵 `encounter` → `encounters.id`）
- `observations`（外鍵 `patient` → `patients.id`，外鍵 `encounter` → `encounters.id`）

一位病人有多筆就診，每次就診可有多筆診斷、用藥與檢驗值。

## 備註

- Synthea 的 `-p 100` 代表 100 位存活病人，已死亡的合成病人會一併輸出，
  所以 `patients.csv` 實際有 140 筆。
- `conditions.csv` 除了疾病（disorder），也包含「情況」「發現」等項目
  （例如 Medication review due），不全是診斷。
- `health.db` 與 `venv/` 不放進 Git，請依上述步驟自行產生。