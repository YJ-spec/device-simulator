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
- ✅ **支援多種型號** - ZP25, ZP2, ZF1, ZF2
- ✅ **即時狀態監控** - 查看設備運行和連線狀態
- ✅ **模擬 MCU 特性** - 時間浮動 0-10 秒模擬不準時發送

## 支援的設備型號

| 型號 | 預設韌體版本 |
|------|-------------|
| ZP25 | T251107-S1 |
| ZP2  | T251107-S1 |
| ZF1  | F101205-S2 |
| ZF2  | F201205-S2 |

## 訊息格式

### 1. 版本資訊 (連線成功時發送一次)
```json
{
  "MODEL": "ZP25",
  "FW": "T251107-S1",
  "HW": "V2",
  "WE310F5": "39.00.008",
  "E750": "VS",
  "SADDR": "10",
  "SWTYPE": "0"
}
```

### 2. 感測器數據 (每分鐘發送)
```json
{
  "data": {
    "ts": "0",
    "t": 24.71,
    "h": 68.60,
    "cc": 26.55,
    "ch": 64.59,
    "pi": 0,
    "p25": 0,
    "p10": 0,
    "v": 50,
    "vi": 0,
    "c": 933,
    "ec": 500,
    "ra": -44,
    "lv": 0
  },
  "datai": {
    "sanple": 1,
    "SCDdx": 1,
    "cp": 1,
    "raet": 500,
    "speed": 0,
    "alarm": 0,
    "gre": 656,
    "aA": 10
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

### 管理設備
- **啟動設備**: 點擊設備列表中的「▶️ 啟動」按鈕
- **停止設備**: 點擊設備列表中的「⏸️ 停止」按鈕
- **刪除設備**: 點擊設備列表中的「🗑️ 刪除」按鈕
- **啟動全部**: 點擊上方的「▶️ 啟動全部」按鈕
- **停止全部**: 點擊上方的「⏸️ 停止全部」按鈕

### 監控狀態
- 頁面會每 3 秒自動更新設備狀態
- 統計卡片顯示總設備數、運行中數量、已連線數量
- 設備列表顯示每個設備的詳細資訊和狀態

## API 文件

### 取得支援的型號
```http
GET /api/models
```

### 取得所有設備
```http
GET /api/devices
```

### 新增單一設備
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

### 批次新增設備
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

### 刪除設備
```http
DELETE /api/devices/{device_id}
```

### 啟動設備
```http
POST /api/devices/{device_id}/start
```

### 停止設備
```http
POST /api/devices/{device_id}/stop
```

### 啟動所有設備
```http
POST /api/devices/start-all
```

### 停止所有設備
```http
POST /api/devices/stop-all
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

每個設備會發布到獨立的 Topic：`ZP2/{MAC}/data`

例如：
- `ZP2/4802af000001/data`
- `ZP2/4802af000002/data`

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

## 注意事項

- MAC 地址在所有設備間保證唯一，即使不同型號也不會重複
- 序列 MAC 格式為 `4802af` + 6位16進制序列號
- 隨機 MAC 格式為 12位16進制隨機數
- 每個設備在連線成功後會立即發送版本資訊
- 心跳和感測器數據會在背景執行緒中定期發送
- 時間間隔會加入 0-10 秒的隨機浮動，模擬實際 MCU 不準時的特性
- 網頁介面支援即時監控，每 3 秒自動更新狀態

## License

MIT
