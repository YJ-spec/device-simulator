# 設備啟動失敗問題解決方案

## 問題現象
- 點擊「啟動設備」按鈕後顯示「啟動失敗」
- 容器日誌顯示 `ConnectionRefusedError: [Errno 111] Connection refused`

## 根本原因
在 Docker 容器內，`localhost` 指向容器本身，而非主機。當 MQTT Broker 在主機上運行時，容器無法透過 `localhost:1883` 連線。

## 解決方案

### 方案 1：使用 host.docker.internal（已修正）
修改 `.env` 檔案的 `MQTT_BROKER` 設定：

```env
MQTT_BROKER=host.docker.internal
MQTT_PORT=1883
```

### 方案 2：使用主機網路模式
修改 `docker-compose.yml`：

```yaml
services:
  device-simulator:
    network_mode: "host"
    # 移除 ports 設定（host 模式不需要）
```

### 方案 3：使用主機 IP
```env
MQTT_BROKER=192.168.1.103  # 替換成你的主機 IP
```

### 方案 4：在容器內啟動 MQTT Broker
使用 Docker Compose 新增 MQTT 服務：

```yaml
services:
  mosquitto:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
  
  device-simulator:
    depends_on:
      - mosquitto
    environment:
      - MQTT_BROKER=mosquitto
```

## 驗證步驟

### 1. 確認環境變數
```powershell
docker compose exec device-simulator python -c "import os; print('MQTT_BROKER:', os.getenv('MQTT_BROKER'))"
```

預期輸出：`MQTT_BROKER: host.docker.internal`

### 2. 測試網路連線
```powershell
docker compose exec device-simulator ping -c 3 host.docker.internal
```

### 3. 測試 MQTT 連線（需要主機有 MQTT Broker）
```powershell
docker compose exec device-simulator python -c "import socket; sock = socket.socket(); sock.settimeout(2); result = sock.connect_ex(('host.docker.internal', 1883)); print('連線成功' if result == 0 else f'連線失敗: {result}'); sock.close()"
```

### 4. 完整測試流程
```powershell
# 重啟容器
docker compose restart device-simulator

# 等待啟動
Start-Sleep -Seconds 3

# 新增設備
$result = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/devices -ContentType 'application/json' -Body '{"model":"ZP25"}'
$deviceId = $result.device_id

# 啟動設備
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5000/api/devices/$deviceId/start"

# 查看日誌
docker compose logs --tail 20 device-simulator
```

## 如果沒有 MQTT Broker

### 快速啟動 Mosquitto MQTT Broker
```powershell
# 建立設定檔
New-Item -ItemType Directory -Force mosquitto
@"
listener 1883
allow_anonymous true
"@ | Out-File -Encoding UTF8 mosquitto/mosquitto.conf

# 啟動 Mosquitto
docker run -d --name mosquitto -p 1883:1883 -v ${PWD}/mosquitto:/mosquitto/config eclipse-mosquitto
```

### 或使用公開測試 Broker
修改 `.env`：
```env
MQTT_BROKER=test.mosquitto.org
MQTT_PORT=1883
```

## 疑難排解

### 問題：容器無法解析 host.docker.internal
**解決**：使用主機 IP 或啟用 host 模式

### 問題：主機防火牆阻擋
**解決**：開放 1883 埠口或暫時關閉防火牆測試

### 問題：MQTT Broker 未啟動
**檢查**：
```powershell
netstat -an | Select-String "1883"
```

## 已修改檔案清單
- `.env` - MQTT_BROKER 改為 `host.docker.internal`
- `.env.example` - 更新預設值
- `app.py` - 新增啟動錯誤日誌
- `device_manager.py` - 增強錯誤追蹤與詳細日誌
