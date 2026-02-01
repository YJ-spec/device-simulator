# Device Simulator - ZP2/ZF1 設備模擬器

這是一個用於模擬 ZP2/ZF1 設備的 Docker 工具，可以透過網頁介面動態管理多個設備模擬器。

## 功能特性

- ✅ **網頁管理介面** - 直觀的圖形化介面管理所有設備
- ✅ **多設備支援** - 同時管理多個不同型號的設備
- ✅ **動態新增/刪除** - 即時新增或移除設備，無需重啟
- ✅ **批次操作** - 一次新增多個設備
- ✅ **唯一 MAC 地址** - 自動生成不重複的 MAC 地址
- ✅ **序列 MAC** - 支援序列格式 (4802afXXXXXX) 或隨機生成
- ✅ **自訂韌體版本** - 可指定每個設備的韌體版本
- ✅ **支援多種型號** - 預設 ZP25（系列 ZP2），使用者可自行新增/移除型號
- ✅ **即時狀態監控** - 查看設備運行和連線狀態
- ✅ **模擬 MCU 特性** - 時間浮動 0-10 秒模擬不準時發送

## 支援的設備型號

**預設型號:**

| 型號 | 預設韌體版本 |
|------|----------|
| ZP25 | T251107-S1 |

> **注意**: 上表仅为預設設備型號。使用者可以透過網頁介面的【預設型號管理】區域適時新增、修改或移除型號。

## 訊息格式

### 1. 版本資訊 (連線成功時發送一次)

發送到: `{系列名稱}/{MAC}/data`

```json
{
  "MODEL": "ZP25",
  "FW": "T251107-S1",
  "HW": "V2",
  "WE310F5": "39.00.008",
  "P750": "V8",
  "SADDR": "10",
  "SWTYPE": "0"
}
```

### 2. 感測器數據 (每分鐘發送)
```json
{
  "data": {
    "ts": 0,
    "t": 24.71,
    "h": 68.60,
    "ct": 26.55,
    "ch": 64.59,
    "p1": 0,
    "p25": 0,
    "p10": 0,
    "v": 55,
    "vl": 0,
    "c": 933,
    "ec": 500,
    "rs": -44,
    "lv": 0
  },
  "data1": {
    "P750": 5,
    "AHT25": 1,
    "SCD4x": 1,
    "op": 1,
    "rset": 500,
    "speed": 0,
    "alarm": 0,
    "rpm": 656,
    "sa": 10
  }
}
```

### 3. 心跳訊息 (每分鐘發送)
```json
{
  "Heartbeat": "1"
}
```

## 快速開始

### 方法 1: 使用根目錄 Compose (推薦)

1. 在專案根目錄（compose.yaml 所在）啟動服務：
```powershell
docker compose -f compose.yaml up -d device-simulator
```

2. 開啟瀏覽器訪問管理介面：
```
http://localhost:5000
```

3. 查看日誌：
```powershell
docker compose -f compose.yaml logs -f device-simulator
```

4. 停止服務：
```powershell
docker compose -f compose.yaml stop device-simulator
```

### 方法 2: 使用 Python 直接執行

1. 安裝相依套件：
```powershell
pip install -r requirements.txt
```

2. 設定環境變數或建立 `.env` 檔案

3. 執行網頁伺服器：
```powershell
python app.py
```

4. 開啟瀏覽器訪問：
```
http://localhost:5000
```

## 網頁介面使用說明

### 新增單一設備
1. 選擇設備型號
2. (選填) 輸入自訂韌體版本
3. (選填) 輸入自訂 MAC 地址
4. 勾選是否使用序列 MAC
5. 點擊「新增設備」

### 批次新增設備
1. 選擇設備型號
2. (選填) 輸入自訂韌體版本
3. 設定要新增的數量 (1-100)
4. 勾選是否使用序列 MAC
5. 點擊「批次新增」

> **注意**: 最多可以統時管理 **100 台設備**

### 管理設備
- **啟動設備**: 點擊設備列表中的「▶️ 啟動」按鈕
- **停止設備**: 點擊設備列表中的「⏸️ 停止」按鈕
- **刪除設備**: 點擊設備列表中的「🗑️ 刪除」按鈕
- **啟動全部**: 點擊上方的「▶️ 啟動全部」按鈕
- **停止全部**: 點擊上方的「⏸️ 停止全部」按鈕
- **移除全部**: 點擊上方的「🧹 移除全部」按鈕 (需要確認)

### 預設型號管理
1. 向下滾到「預設型號管理」區域
2. 輸入系列名稱 (例如：ZP2)
3. 輸入新型號名稱 (例如：ZP25)
4. 輸入預設韌體版本 (例如：T251107-S1)
5. 點擊【新增型號】按鈕
5. 可以在設備列表下方查看已設置的型號，點擊【移除】可以刪除
6. 支援【⬇️ 匯出】和「⬆️ 匯入」功能儲存/恢復設定

### 監控狀態
- 頁面會每 60 秒自動更新設備狀態
- 統計卡片顯示總設備數、運行中數量、已連線數量
- 設備列表顯示每個設備的詳細資訊和狀態
- 所有操作結果透過 Toast 通知顯示（自動消失，無須點擊確認）

## API 文件

### 型號管理

#### 取得支援的型號
```http
GET /api/models
```

#### 新增型號
```http
POST /api/models
Content-Type: application/json

{
  "series": "ZP2",
  "model": "ZP25",
  "fw_version": "T251107-S1"
}
```

#### 移除型號
```http
DELETE /api/models/{model}
```

#### 匯出型號設定
```http
GET /api/models/export
```
回傳視窗下載 `device_models.json` 檔案

#### 匯入型號設定
```http
POST /api/models/import
Content-Type: application/json

{
  "models": {
    "ZP25": {
      "series": "ZP2",
      "fw_version": "T251107-S1"
    },
    "ZF1": {
      "series": "ZF",
      "fw_version": "F101205-S2"
    }
  }
}
```

### 設備管理

#### 取得所有設備
```http
GET /api/devices
```

#### 新增單一設備
```http
POST /api/devices
Content-Type: application/json

{
  "model": "ZP25",
  "fw_version": "T251107-S1",  // 選填
  "mac": "4802af000001",       // 選填
  "use_sequential": true       // 選填
}
```

#### 批次新增設備
```http
POST /api/devices/batch
Content-Type: application/json

{
  "model": "ZP25",
  "fw_version": "T251107-S1",  // 選填
  "count": 10,
  "use_sequential": true
}
```

#### 刪除設備
```http
DELETE /api/devices/{device_id}
```

#### 啟動設備
```http
POST /api/devices/{device_id}/start
```

#### 停止設備
```http
POST /api/devices/{device_id}/stop
```

#### 啟動所有設備
```http
POST /api/devices/start-all
```

#### 停止所有設備
```http
POST /api/devices/stop-all
```

#### 移除所有設備
```http
POST /api/devices/remove-all
```

## 環境變數說明

| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `MQTT_BROKER` | MQTT Broker 主機位址 | `localhost` |
| `MQTT_PORT` | MQTT Broker 連接埠 | `1883` |
| `MQTT_USERNAME` | MQTT 使用者名稱 | `` |
| `MQTT_PASSWORD` | MQTT 密碼 | `` |
| `WEB_PORT` | 網頁伺服器連接埠 | `5000` |

## MQTT Topic 格式

**格式**: `{系列名稱}/{MAC}/data`

例如：
- `ZP2/4802af000001/data` (ZP25 型號設備)
- `ZF/4802af000002/data` (ZF1 型號設備)

## 專案結構

```
device-simulator/
├── app.py                  # Flask 網頁伺服器
├── device_manager.py       # 設備管理器
├── templates/
│   └── index.html         # 網頁管理介面
├── requirements.txt        # Python 相依套件
├── .env.example           # 環境變數範例
├── .gitignore            # Git 忽略檔案
└── README.md             # 說明文件
```

## 已淘汰檔案

以下檔案已不再使用，已移除或保留僅作為提醒：
- ~~device_simulator.py~~ (已移除)
- Dockerfile (已復原為生產模式)
- docker-compose.yml (已復原為生產模式)

## 技術特色

### 效能優化
- 批次停止/啟動/移除使用執行緒池並行處理
- 100 台設備僅需 20-30 秒，立即反應

### UI/UX 改進
- Toast 通知系統（自動消失，不需要再次確認）
- 進度提示模態框（批量操作時顯示進度）
- 響應式設計，依情況探選項

## 數量上限 & 風險

- **設備容量**: 最多 **100 台**
- **設備型號**: 使用者可以自由新增/移除 (但不可刪除有設備使用中的型號)
- **批次新增**: 一次最多 100 台
- **批次停止/啟動**: 使用執行緒池，5 個並行執行緒
- **批次移除**: 需要二次確認，無法復原

## 注意事項

- **設備數量上限**: 最多 100 台，上限上會立即讓新增失敗
- MAC 地址在所有設備間保證唯一，即使不同型號也不會重複
- 序列 MAC 格式為 `4802af` + 6位16進制序列號
- 隨機 MAC 格式為 12位16進制隨機數
- 每個設備在連線成功會立即發送一次版本資訊
- 心跳和感測器數據會在背景執行緒中定期發送（預設 60 秒）
- 時間間隔會加入 0-10 秒的隨機浮動，模擬實際 MCU 不準時的特性
- 網頁介面每 60 秒自動更新一次設備狀態
- 版本設定會持久化到 `data/models.json`，服務重新啟動時自動載入

## License

MIT
