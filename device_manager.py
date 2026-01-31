#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import threading
import random
import secrets

class DeviceSimulator:
    """單一設備模擬器"""
    
    # 支援的設備型號和對應的預設韌體版本
    DEVICE_MODELS = {
        'ZP25': 'T251107-S1',
        'ZP2': 'T251107-S1',
        'ZF1': 'F101205-S2',
        'ZF2': 'F201205-S2',
    }
    
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
            "MODEL": self.model,
            "FW": self.fw_version,
            "HW": self.hw_version,
            "WE310F5": "39.00.008",
            "E750": "VS",
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
                "ts": "0",
                "t": round(random.uniform(20.0, 30.0), 2),
                "h": round(random.uniform(40.0, 80.0), 2),
                "cc": round(random.uniform(20.0, 35.0), 2),
                "ch": round(random.uniform(50.0, 70.0), 2),
                "pi": 0,
                "p25": 0,
                "p10": 0,
                "v": 50,
                "vi": 0,
                "c": random.randint(900, 1000),
                "ec": random.randint(450, 550),
                "ra": random.randint(-50, -40),
                "lv": 0
            },
            "datai": {
                "sanple": 1,
                "SCDdx": 1,
                "cp": 1,
                "raet": 500,
                "speed": 0,
                "alarm": 0,
                "gre": random.randint(600, 700),
                "aA": 10
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
    
    def __init__(self, broker, port, username='', password=''):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.devices = {}
        self.device_counter = 0
        self.used_macs = set()
        self.lock = threading.RLock()
    
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
        """啟動所有設備"""
        count = 0
        for device in self.devices.values():
            if device.start():
                count += 1
        return count
    
    def stop_all(self):
        """停止所有設備"""
        for device in self.devices.values():
            device.stop()
    
    def get_all_status(self):
        """取得所有設備狀態"""
        return [device.get_status() for device in self.devices.values()]
    
    def get_device_status(self, device_id):
        """取得單一設備狀態"""
        if device_id not in self.devices:
            return None
        return self.devices[device_id].get_status()
    
    def get_supported_models(self):
        """取得支援的設備型號"""
        return DeviceSimulator.DEVICE_MODELS
