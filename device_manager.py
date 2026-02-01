#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
import random
import secrets
import os

class DeviceSimulator:
    """單一設備模擬器"""
    
    # 支援的設備型號和對應的預設韌體版本
    DEFAULT_DEVICE_MODELS = {
        'ZP2': 'T251107-S1',
    }
    DEVICE_MODELS = dict(DEFAULT_DEVICE_MODELS)
    
    def __init__(self, device_id, mac, model, fw_version, broker, port, username='', password='', 
                 heartbeat_interval=60, data_interval=60):
        self.device_id = device_id
        self.mac = mac
        self.model = model
        self.fw_version = fw_version
        self.hw_version = 'V2'
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.heartbeat_interval = heartbeat_interval
        self.data_interval = data_interval
        
        self.topic = f"ZP2/{mac}/data"
        self.client = mqtt.Client(client_id=f"device_{mac}")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.running = False
        self.connected = False
        
        if self.username:
            self.client.username_pw_set(self.username, self.password)
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"[{datetime.now()}] 設備 {self.device_id} ({self.mac}) 已連線")
            # 連線成功後立即發送版本資訊
            self.send_version_info()
        else:
            self.connected = False
            print(f"[{datetime.now()}] 設備 {self.device_id} ({self.mac}) 連線失敗，回傳碼: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print(f"[{datetime.now()}] 設備 {self.device_id} ({self.mac}) 已斷線")
    
    def send_version_info(self):
        """發送設備版本資訊 (連線成功時發送一次)"""
        payload = {
            "MODEL": "ZP25" if self.model == "ZP2" else self.model,
            "FW": self.fw_version,
            "HW": self.hw_version,
            "WE310F5": "39.00.008",
            "P750": "V8",
            "SADDR": "10",
            "SWTYPE": "0"
        }
        
        result = self.client.publish(self.topic, json.dumps(payload), qos=0)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[{datetime.now()}] 設備 {self.device_id} 已發送版本資訊")
    
    def send_sensor_data(self):
        """發送感測器數據"""
        payload = {
            "data": {
                "ts": 0,
                "t": round(random.uniform(20.0, 30.0), 2),
                "h": round(random.uniform(40.0, 80.0), 2),
                "ct": round(random.uniform(20.0, 35.0), 2),
                "ch": round(random.uniform(50.0, 70.0), 2),
                "p1": 0,
                "p25": 0,
                "p10": 0,
                "v": random.randint(50, 60),
                "vl": 0,
                "c": random.randint(900, 1000),
                "ec": random.randint(450, 550),
                "rs": random.randint(-50, -40),
                "lv": 0
            },
            "data1": {
                "P750": random.randint(1, 10),
                "AHT25": 1,
                "SCD4x": 1,
                "op": 1,
                "rset": 500,
                "speed": 0,
                "alarm": 0,
                "rpm": random.randint(500, 700),
                "sa": 10
            }
        }
        
        self.client.publish(self.topic, json.dumps(payload), qos=0)
    
    def send_heartbeat(self):
        """發送心跳訊息"""
        payload = {"Heartbeat": "1"}
        self.client.publish(self.topic, json.dumps(payload), qos=0)
    
    def data_sender_thread(self):
        """數據發送執行緒"""
        while self.running:
            jitter = random.uniform(0, 10)
            time.sleep(self.data_interval + jitter)
            if self.running and self.connected:
                self.send_sensor_data()
    
    def heartbeat_sender_thread(self):
        """心跳發送執行緒"""
        while self.running:
            jitter = random.uniform(0, 10)
            time.sleep(self.heartbeat_interval + jitter)
            if self.running and self.connected:
                self.send_heartbeat()
    
    def start(self):
        """啟動設備模擬器"""
        if self.running:
            return False
        
        try:
            print(f"[{datetime.now()}] 設備 {self.device_id} 嘗試連線到 {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, 60)
            self.running = True
            
            # 啟動發送執行緒
            threading.Thread(target=self.data_sender_thread, daemon=True).start()
            threading.Thread(target=self.heartbeat_sender_thread, daemon=True).start()
            
            # 啟動 MQTT 迴圈
            self.client.loop_start()
            print(f"[{datetime.now()}] 設備 {self.device_id} 啟動成功")
            return True
            
        except Exception as e:
            print(f"[{datetime.now()}] 設備 {self.device_id} 啟動失敗: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop(self):
        """停止設備模擬器"""
        if not self.running:
            return
        
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        print(f"[{datetime.now()}] 設備 {self.device_id} ({self.mac}) 已停止")
    
    def get_status(self):
        """取得設備狀態"""
        return {
            'device_id': self.device_id,
            'mac': self.mac,
            'model': self.model,
            'fw_version': self.fw_version,
            'running': self.running,
            'connected': self.connected,
            'topic': self.topic
        }


class DeviceManager:
    """設備管理器 - 管理多個設備模擬器"""
    
    # 批次處理配置
    BATCH_SIZE = 10  # 每個批次最多 10 台設備
    MAX_WORKERS = 5  # 最多 5 個併發執行緒
    
    def __init__(self, broker, port, username='', password=''):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.devices = {}
        self.device_counter = 0
        self.used_macs = set()
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=self.MAX_WORKERS, thread_name_prefix='DeviceWorker')
        self.model_store_path = os.getenv(
            'MODEL_STORE_PATH',
            os.path.join(os.path.dirname(__file__), 'data', 'models.json')
        )
        self._load_models()

    def _load_models(self):
        """載入型號設定（若無檔案則使用預設）"""
        with self.lock:
            if not os.path.exists(self.model_store_path):
                DeviceSimulator.DEVICE_MODELS = dict(DeviceSimulator.DEFAULT_DEVICE_MODELS)
                return

            try:
                with open(self.model_store_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict) and all(
                    isinstance(k, str) and isinstance(v, str) for k, v in data.items()
                ):
                    DeviceSimulator.DEVICE_MODELS = dict(data)
                else:
                    DeviceSimulator.DEVICE_MODELS = dict(DeviceSimulator.DEFAULT_DEVICE_MODELS)
            except Exception:
                DeviceSimulator.DEVICE_MODELS = dict(DeviceSimulator.DEFAULT_DEVICE_MODELS)

    def _save_models(self):
        """儲存型號設定"""
        with self.lock:
            os.makedirs(os.path.dirname(self.model_store_path), exist_ok=True)
            with open(self.model_store_path, 'w', encoding='utf-8') as f:
                json.dump(DeviceSimulator.DEVICE_MODELS, f, ensure_ascii=False, indent=2)
    
    def generate_mac(self):
        """生成唯一的 MAC 地址"""
        with self.lock:
            while True:
                # 生成隨機 MAC (格式: 12位16進制)
                mac = secrets.token_hex(6)
                if mac not in self.used_macs:
                    self.used_macs.add(mac)
                    return mac
    
    def generate_sequential_mac(self, index):
        """生成序列 MAC 地址"""
        with self.lock:
            # 格式: 4802af + 6位序列號
            mac = f"4802af{index:06x}"
            if mac not in self.used_macs:
                self.used_macs.add(mac)
                return mac
            # 如果已存在，使用隨機生成
            return self.generate_mac()
    
    def add_device(self, model, fw_version=None, mac=None, use_sequential=False):
        """新增設備"""
        with self.lock:
            # 檢查設備數量限制（最多 100 台）
            if len(self.devices) >= 100:
                return None, f"設備數量已達到上限 (100台)，無法新增"
            
            # 驗證型號
            if model not in DeviceSimulator.DEVICE_MODELS:
                return None, f"不支援的型號: {model}"
            
            # 設定韌體版本
            if not fw_version:
                fw_version = DeviceSimulator.DEVICE_MODELS[model]
            
            # 生成 MAC
            if mac and mac in self.used_macs:
                return None, f"MAC 地址已被使用: {mac}"
            
            if not mac:
                if use_sequential:
                    mac = self.generate_sequential_mac(self.device_counter)
                else:
                    mac = self.generate_mac()
            else:
                self.used_macs.add(mac)
            
            # 建立設備
            device_id = f"device_{self.device_counter}"
            self.device_counter += 1
            
            device = DeviceSimulator(
                device_id=device_id,
                mac=mac,
                model=model,
                fw_version=fw_version,
                broker=self.broker,
                port=self.port,
                username=self.username,
                password=self.password
            )
            
            self.devices[device_id] = device
            return device_id, None
    
    def remove_device(self, device_id):
        """移除設備"""
        with self.lock:
            if device_id not in self.devices:
                return False, "設備不存在"
            
            device = self.devices[device_id]
            device.stop()
            self.used_macs.discard(device.mac)
            del self.devices[device_id]
            return True, None
    
    def start_device(self, device_id):
        """啟動設備"""
        if device_id not in self.devices:
            return False, "設備不存在"
        
        device = self.devices[device_id]
        success = device.start()
        return success, None if success else "啟動失敗"
    
    def stop_device(self, device_id):
        """停止設備"""
        if device_id not in self.devices:
            return False, "設備不存在"
        
        device = self.devices[device_id]
        device.stop()
        return True, None
    
    def start_all(self):
        """啟動所有設備（使用執行緒池批次處理）"""
        count = 0
        with self.lock:
            devices_snapshot = list(self.devices.values())
        
        if not devices_snapshot:
            return 0
        
        # 使用執行緒池並行啟動設備
        futures = [self.executor.submit(device.start) for device in devices_snapshot]
        
        # 等待所有任務完成並計算成功數
        for future in futures:
            try:
                if future.result(timeout=5):  # 每個設備啟動最多等待 5 秒
                    count += 1
            except Exception as e:
                print(f"啟動設備時出錯: {e}")
        
        return count
    
    def stop_all(self):
        """停止所有設備（使用執行緒池批次處理）"""
        with self.lock:
            devices_snapshot = list(self.devices.values())
        
        if not devices_snapshot:
            return 0
        
        # 使用執行緒池並行停止設備
        futures = [self.executor.submit(device.stop) for device in devices_snapshot]
        
        # 等待所有任務完成
        for future in futures:
            try:
                future.result(timeout=5)  # 每個設備停止最多等待 5 秒
            except Exception as e:
                print(f"停止設備時出錯: {e}")
        
        return len(devices_snapshot)

    def remove_all(self):
        """移除所有設備（使用執行緒池批次處理）"""
        with self.lock:
            count = len(self.devices)
            devices_snapshot = list(self.devices.values())
        
        if not devices_snapshot:
            return 0
        
        # 並行停止所有設備
        futures = [self.executor.submit(device.stop) for device in devices_snapshot]
        
        # 等待所有停止操作完成
        for future in futures:
            try:
                future.result(timeout=5)
            except Exception as e:
                print(f"停止設備時出錯: {e}")
        
        # 清理設備與 MAC
        with self.lock:
            for device in devices_snapshot:
                self.used_macs.discard(device.mac)
            self.devices.clear()
        
        return count
    
    def get_all_status(self):
        """取得所有設備狀態"""
        with self.lock:
            devices_snapshot = list(self.devices.values())
        return [device.get_status() for device in devices_snapshot]
    
    def get_paginated_status(self, page=1, page_size=50):
        """
        取得分頁設備狀態（用於優化大量設備時的性能）
        
        參數：
        - page: 頁碼（1-based）
        - page_size: 每頁設備數
        
        回傳：
        {
            'devices': [...],
            'total': 總設備數,
            'page': 當前頁數,
            'page_size': 每頁大小,
            'total_pages': 總頁數,
            'max_devices': 最大設備數限制
        }
        """
        with self.lock:
            all_devices = list(self.devices.values())
        
        total = len(all_devices)
        total_pages = (total + page_size - 1) // page_size
        
        # 確保頁碼有效
        page = max(1, min(page, total_pages if total_pages > 0 else 1))
        
        # 計算切片索引
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # 獲取該頁的設備狀態
        page_devices = [device.get_status() for device in all_devices[start_idx:end_idx]]
        
        return {
            'devices': page_devices,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'max_devices': 100  # 設備上限
        }
    
    def get_device_status(self, device_id):
        """取得單一設備狀態"""
        if device_id not in self.devices:
            return None
        return self.devices[device_id].get_status()
    
    def get_supported_models(self):
        """取得支援的設備型號"""
        return dict(DeviceSimulator.DEVICE_MODELS)

    def add_model(self, model, fw_version):
        """新增支援的設備型號"""
        model = (model or '').strip()
        fw_version = (fw_version or '').strip()
        if not model:
            return False, "設備型號不可為空"
        if not fw_version:
            return False, "韌體版本不可為空"
        with self.lock:
            DeviceSimulator.DEVICE_MODELS[model] = fw_version
            self._save_models()
        return True, None

    def remove_model(self, model):
        """移除支援的設備型號"""
        model = (model or '').strip()
        if not model:
            return False, "設備型號不可為空"
        with self.lock:
            if model not in DeviceSimulator.DEVICE_MODELS:
                return False, "設備型號不存在"
            if any(device.model == model for device in self.devices.values()):
                return False, "仍有設備使用此型號，無法移除"
            del DeviceSimulator.DEVICE_MODELS[model]
            self._save_models()
        return True, None

    def import_models(self, models):
        """匯入型號設定"""
        if not isinstance(models, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in models.items()
        ):
            return False, "匯入資料格式不正確"

        with self.lock:
            in_use = {device.model for device in self.devices.values()}
            missing = in_use - set(models.keys())
            if missing:
                return False, f"仍有設備使用以下型號，無法匯入：{', '.join(sorted(missing))}"

            DeviceSimulator.DEVICE_MODELS = dict(models)
            self._save_models()
        return True, None
