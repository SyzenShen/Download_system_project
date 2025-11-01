#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工具函数
Test Utility Functions
"""

import os
import sys
import time
import json
import hashlib
import requests
import logging
import psutil
import threading
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 添加配置路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'configs'))
from test_config import *

class TestLogger:
    """测试日志记录器"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # 创建文件处理器
        log_file = os.path.join(LOGS_DIR, f"{name}_{TEST_SESSION_ID}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式器
        formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def debug(self, message: str):
        self.logger.debug(message)

class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.logger = TestLogger("AuthManager")
        self.tokens = {}
        self.session = requests.Session()
    
    def register_user(self, email: str, password: str) -> bool:
        """注册用户"""
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/register/",
                json={
                    "email": email,
                    "password": password,
                    "password_confirm": password
                },
                timeout=30
            )
            
            if response.status_code == 201:
                self.logger.info(f"用户注册成功: {email}")
                return True
            else:
                self.logger.warning(f"用户注册失败: {email}, 状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"注册用户时发生错误: {e}")
            return False
    
    def login_user(self, email: str, password: str) -> Optional[str]:
        """用户登录，返回token"""
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/login/",
                json={
                    "email": email,
                    "password": password
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                if token:
                    self.tokens[email] = token
                    self.logger.info(f"用户登录成功: {email}")
                    return token
            
            self.logger.warning(f"用户登录失败: {email}, 状态码: {response.status_code}")
            return None
            
        except Exception as e:
            self.logger.error(f"登录用户时发生错误: {e}")
            return None
    
    def get_token(self, email: str) -> Optional[str]:
        """获取用户token"""
        return self.tokens.get(email)
    
    def get_auth_headers(self, email: str) -> Dict[str, str]:
        """获取认证头"""
        token = self.get_token(email)
        if token:
            return {"Authorization": f"Token {token}"}
        return {}

class FileGenerator:
    """测试文件生成器"""
    
    def __init__(self):
        self.logger = TestLogger("FileGenerator")
    
    def generate_test_file(self, size_bytes: int, filename: str) -> str:
        """生成指定大小的测试文件"""
        file_path = os.path.join(TEST_FILES_DIR, filename)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) == size_bytes:
            self.logger.info(f"测试文件已存在: {filename}")
            return file_path
        
        self.logger.info(f"生成测试文件: {filename} ({size_bytes / (1024*1024):.1f} MB)")
        
        try:
            with open(file_path, 'wb') as f:
                chunk_size = 1024 * 1024  # 1MB chunks
                written = 0
                
                while written < size_bytes:
                    remaining = size_bytes - written
                    current_chunk_size = min(chunk_size, remaining)
                    
                    # 生成随机数据
                    chunk = os.urandom(current_chunk_size)
                    f.write(chunk)
                    written += current_chunk_size
                    
                    # 显示进度
                    if written % (100 * 1024 * 1024) == 0:  # 每100MB显示一次
                        progress = (written / size_bytes) * 100
                        self.logger.info(f"生成进度: {progress:.1f}%")
            
            self.logger.info(f"测试文件生成完成: {filename}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"生成测试文件失败: {e}")
            raise
    
    def calculate_md5(self, file_path: str) -> str:
        """计算文件MD5"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"计算MD5失败: {e}")
            return ""

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.logger = TestLogger("PerformanceMonitor")
        self.monitoring = False
        self.monitor_thread = None
        self.data = []
    
    def start_monitoring(self, duration: int = None):
        """开始监控"""
        self.monitoring = True
        self.data = []
        
        def monitor():
            start_time = time.time()
            while self.monitoring:
                if duration and (time.time() - start_time) > duration:
                    break
                
                try:
                    # CPU使用率
                    cpu_percent = psutil.cpu_percent(interval=1)
                    
                    # 内存使用
                    memory = psutil.virtual_memory()
                    
                    # 磁盘I/O
                    disk_io = psutil.disk_io_counters()
                    
                    # 网络I/O
                    net_io = psutil.net_io_counters()
                    
                    data_point = {
                        'timestamp': time.time(),
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'memory_used_gb': memory.used / (1024**3),
                        'disk_read_mb': disk_io.read_bytes / (1024**2) if disk_io else 0,
                        'disk_write_mb': disk_io.write_bytes / (1024**2) if disk_io else 0,
                        'net_sent_mb': net_io.bytes_sent / (1024**2) if net_io else 0,
                        'net_recv_mb': net_io.bytes_recv / (1024**2) if net_io else 0,
                    }
                    
                    self.data.append(data_point)
                    
                except Exception as e:
                    self.logger.error(f"监控数据收集错误: {e}")
                
                time.sleep(MONITOR_INTERVAL)
        
        self.monitor_thread = threading.Thread(target=monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("性能监控已开始")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("性能监控已停止")
    
    def get_stats(self) -> Dict:
        """获取统计数据"""
        if not self.data:
            return {}
        
        cpu_values = [d['cpu_percent'] for d in self.data]
        memory_values = [d['memory_used_gb'] for d in self.data]
        
        return {
            'duration': len(self.data) * MONITOR_INTERVAL,
            'cpu_avg': sum(cpu_values) / len(cpu_values),
            'cpu_max': max(cpu_values),
            'memory_avg': sum(memory_values) / len(memory_values),
            'memory_max': max(memory_values),
            'data_points': len(self.data)
        }

class StatisticsCalculator:
    """统计计算器"""
    
    @staticmethod
    def calculate_throughput(file_size_bytes: int, duration_seconds: float) -> float:
        """计算吞吐量 (MB/s)"""
        if duration_seconds <= 0:
            return 0
        return (file_size_bytes / (1024 * 1024)) / duration_seconds
    
    @staticmethod
    def calculate_average(values: List[float]) -> float:
        """计算平均值"""
        if not values:
            return 0
        return sum(values) / len(values)
    
    @staticmethod
    def calculate_percentile(values: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    @staticmethod
    def calculate_success_rate(total: int, successful: int) -> float:
        """计算成功率"""
        if total <= 0:
            return 0
        return successful / total

class ResultSaver:
    """结果保存器"""
    
    def __init__(self):
        self.logger = TestLogger("ResultSaver")
    
    def save_test_result(self, test_name: str, result_data: Dict):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_name}_{timestamp}.json"
        file_path = os.path.join(RESULTS_DIR, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"测试结果已保存: {filename}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {e}")
            return None
    
    def load_test_result(self, file_path: str) -> Optional[Dict]:
        """加载测试结果"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载测试结果失败: {e}")
            return None

def setup_test_environment():
    """设置测试环境"""
    logger = TestLogger("Setup")
    
    # 创建必要的目录
    for dir_path in [TEST_FILES_DIR, RESULTS_DIR, LOGS_DIR, REPORTS_DIR]:
        os.makedirs(dir_path, exist_ok=True)
    
    # 注册测试用户
    auth_manager = AuthManager()
    for user in TEST_USERS:
        auth_manager.register_user(user["email"], user["password"])
        time.sleep(1)  # 避免请求过快
    
    logger.info("测试环境设置完成")
    return auth_manager

def cleanup_test_environment():
    """清理测试环境"""
    logger = TestLogger("Cleanup")
    
    # 清理大文件（可选）
    # for filename in os.listdir(TEST_FILES_DIR):
    #     if filename.endswith('.bin'):
    #         os.remove(os.path.join(TEST_FILES_DIR, filename))
    
    logger.info("测试环境清理完成")