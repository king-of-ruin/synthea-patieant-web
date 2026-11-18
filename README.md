# Synthea 合成病人查詢網頁

用 Synthea 產生 100 位「非真人」的合成病人，匯入 SQLite 資料庫，
並以 Flask 做出可篩選病人、查看就診紀錄的網頁。

> 本專案全程只使用 Synthea 產生的合成資料，沒有任何真實病人資料。

## 環境需求

- Windows 10/11（Mac/Linux 的指令差異見各步驟備註）
- JDK 17 以上（執行 Synthea 用）
- Python 3.10 以上
- Git

確認版本：

```
java -version
python --version
git --version
```

## 專案結構

```
synthea-patient-web/
├─ data/               Synthea 產生的 CSV（patients、encounters、conditions）
├─ templates/          網頁模板（patients.html、patient_detail.html）
├─ import_data.py      匯入資料到 SQLite，並印出資料核對結果
├─ app.py              Flask 網頁程式
├─ requirements.txt    Python 套件清單
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

在專案**資料夾外面**下載並執行 Synthea：

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

把 `synthea/output/csv/` 裡的 `patients.csv`、`encounters.csv`、`conditions.csv`
複製到本專案的 `data/` 資料夾（已附在 repo 內的可略過此步）。

### 5. 匯入資料庫

回到專案資料夾，並確認虛擬環境已啟動（終端機最前面有 `(venv)`）：

```
python import_data.py
```

會建立 `health.db`，並印出各表的 CSV 筆數與資料庫筆數，以及孤兒資料檢查結果。

### 6. 啟動網頁

```
python app.py
```

瀏覽器開啟 http://127.0.0.1:5000 。按 Ctrl+C 可停止伺服器。

## 功能

- **病人清單頁（/）**：列出所有病人，可依性別、年齡區間篩選（年齡以 2026-11-01 計算）。
- **病人詳細頁（/patient/病人ID）**：依日期由早到晚顯示就診日期、就診類型、診斷。

## 資料表關係

- `patients`（主鍵 `id`）
- `encounters`（主鍵 `id`，外鍵 `patient` → `patients.id`）
- `conditions`（外鍵 `patient` → `patients.id`，外鍵 `encounter` → `encounters.id`）

一位病人有多筆就診，每次就診可有多筆診斷。

## 備註

- Synthea 的 `-p 100` 代表 100 位存活病人，已死亡的合成病人會一併輸出，
  所以 `patients.csv` 筆數會多於 100。
- `health.db` 與 `venv/` 不放進 Git，請依上述步驟自行產生。