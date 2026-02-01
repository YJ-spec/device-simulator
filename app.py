#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from device_manager import DeviceManager
import os
from dotenv import load_dotenv
import io
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

# 初始化設備管理器
manager = DeviceManager(
    broker=os.getenv('MQTT_BROKER', 'localhost'),
    port=int(os.getenv('MQTT_PORT', 1883)),
    username=os.getenv('MQTT_USERNAME', ''),
    password=os.getenv('MQTT_PASSWORD', '')
)

@app.route('/')
def index():
    """首頁"""
    return render_template('index.html')

@app.route('/api/models', methods=['GET'])
def get_models():
    """取得支援的設備型號"""
    return jsonify({
        'success': True,
        'models': manager.get_supported_models()
    })

@app.route('/api/models', methods=['POST'])
def add_model():
    """新增支援的設備型號"""
    data = request.json or {}
    model = data.get('model')
    fw_version = data.get('fw_version')

    success, error = manager.add_model(model, fw_version)
    if error:
        return jsonify({'success': False, 'error': error}), 400

    return jsonify({
        'success': True,
        'models': manager.get_supported_models()
    })

@app.route('/api/models/<model>', methods=['DELETE'])
def remove_model(model):
    """移除支援的設備型號"""
    success, error = manager.remove_model(model)
    if error:
        return jsonify({'success': False, 'error': error}), 400

    return jsonify({
        'success': True,
        'models': manager.get_supported_models()
    })

@app.route('/api/models/export', methods=['GET'])
def export_models():
    """匯出支援的設備型號"""
    models = manager.get_supported_models()
    data = json.dumps(models, ensure_ascii=False, indent=2)
    return send_file(
        io.BytesIO(data.encode('utf-8')),
        mimetype='application/json',
        as_attachment=True,
        download_name='device_models.json'
    )

@app.route('/api/models/import', methods=['POST'])
def import_models():
    """匯入支援的設備型號"""
    data = request.json or {}
    models = data.get('models') if isinstance(data, dict) else None
    if models is None and isinstance(data, dict):
        models = data

    success, error = manager.import_models(models)
    if error:
        return jsonify({'success': False, 'error': error}), 400

    return jsonify({
        'success': True,
        'models': manager.get_supported_models()
    })

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """
    取得設備狀態，支援分頁
    
    查詢參數：
    - page: 頁碼（預設 1）
    - page_size: 每頁大小（預設 50，最大 100）
    - use_pagination: 是否使用分頁（預設 true）
    """
    # 檢查是否使用分頁
    use_pagination = request.args.get('use_pagination', 'true').lower() != 'false'
    
    if not use_pagination:
        # 不分頁，返回所有設備（警告：大量設備時可能很慢）
        return jsonify({
            'success': True,
            'devices': manager.get_all_status()
        })
    
    # 使用分頁
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))
    
    # 限制 page_size 最多 100
    page_size = min(max(1, page_size), 100)
    
    paginated_result = manager.get_paginated_status(page, page_size)
    
    return jsonify({
        'success': True,
        **paginated_result  # 展開分頁結果
    })

@app.route('/api/devices', methods=['POST'])
def add_device():
    """新增設備"""
    data = request.json
    model = data.get('model')
    fw_version = data.get('fw_version')
    mac = data.get('mac')
    use_sequential = data.get('use_sequential', False)
    
    if not model:
        return jsonify({'success': False, 'error': '缺少設備型號'}), 400
    
    device_id, error = manager.add_device(model, fw_version, mac, use_sequential)
    
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    return jsonify({
        'success': True,
        'device_id': device_id,
        'device': manager.get_device_status(device_id)
    })

@app.route('/api/devices/batch', methods=['POST'])
def add_devices_batch():
    """批次新增設備"""
    data = request.json
    count = data.get('count', 1)
    model = data.get('model')
    fw_version = data.get('fw_version')
    use_sequential = data.get('use_sequential', True)
    
    if not model:
        return jsonify({'success': False, 'error': '缺少設備型號'}), 400
    
    # 檢查請求數量
    if count < 1 or count > 100:
        return jsonify({'success': False, 'error': '設備數量必須在 1-100 之間'}), 400
    
    # 檢查是否會超過總限制 (提前拒絕，不創建部分設備)
    current_device_count = len(manager.devices)
    if current_device_count + count > 100:
        return jsonify({
            'success': False,
            'error': f'設備數量超出限制。目前有 {current_device_count} 台設備，最多還能新增 {100 - current_device_count} 台'
        }), 400
    
    added_devices = []
    errors = []
    
    for i in range(count):
        device_id, error = manager.add_device(model, fw_version, use_sequential=use_sequential)
        if error:
            errors.append(f"設備 {i+1}: {error}")
        else:
            added_devices.append(manager.get_device_status(device_id))
    
    return jsonify({
        'success': len(errors) == 0,
        'devices': added_devices,
        'errors': errors
    })

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def remove_device(device_id):
    """移除設備"""
    success, error = manager.remove_device(device_id)
    
    if error:
        return jsonify({'success': False, 'error': error}), 404
    
    return jsonify({'success': True})

@app.route('/api/devices/<device_id>/start', methods=['POST'])
def start_device(device_id):
    """啟動設備"""
    success, error = manager.start_device(device_id)
    
    if error:
        print(f"[ERROR] 啟動設備 {device_id} 失敗: {error}")
        return jsonify({'success': False, 'error': error}), 400
    
    print(f"[INFO] 設備 {device_id} 啟動成功")
    return jsonify({
        'success': True,
        'device': manager.get_device_status(device_id)
    })

@app.route('/api/devices/<device_id>/stop', methods=['POST'])
def stop_device(device_id):
    """停止設備"""
    success, error = manager.stop_device(device_id)
    
    if error:
        return jsonify({'success': False, 'error': error}), 404
    
    return jsonify({
        'success': True,
        'device': manager.get_device_status(device_id)
    })

@app.route('/api/devices/start-all', methods=['POST'])
def start_all_devices():
    """啟動所有設備"""
    count = manager.start_all()
    return jsonify({
        'success': True,
        'started_count': count
    })

@app.route('/api/devices/stop-all', methods=['POST'])
def stop_all_devices():
    """停止所有設備"""
    manager.stop_all()
    return jsonify({'success': True})

@app.route('/api/devices/remove-all', methods=['POST'])
def remove_all_devices():
    """移除所有設備"""
    count = manager.remove_all()
    return jsonify({
        'success': True,
        'removed_count': count
    })

if __name__ == '__main__':
    port = int(os.getenv('WEB_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
