#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试配置文件
Performance Test Configuration
"""

import os
from datetime import datetime

# 基础配置
BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api"
FRONTEND_URL = "http://localhost:5173"

# 测试用户配置
TEST_USERS = [
    {"email": "test1@example.com", "password": "TestPass123!"},
    {"email": "test2@example.com", "password": "TestPass123!"},
    {"email": "test3@example.com", "password": "TestPass123!"},
    {"email": "test4@example.com", "password": "TestPass123!"},
    {"email": "test5@example.com", "password": "TestPass123!"},
]

# 文件大小配置 (字节)
FILE_SIZES = {
    "10MB": 10 * 1024 * 1024,
    "100MB": 100 * 1024 * 1024,
    "1GB": 1 * 1024 * 1024 * 1024,
    "10GB": 10 * 1024 * 1024 * 1024,
    "100GB": 100 * 1024 * 1024 * 1024,
}

# 并发测试配置
CONCURRENT_LEVELS = [1, 10, 50, 100]

# 测试重复次数
TEST_ITERATIONS = 3

# 超时配置 (秒)
TIMEOUTS = {
    "10MB": 300,    # 5分钟
    "100MB": 600,   # 10分钟
    "1GB": 1800,    # 30分钟
    "10GB": 3600,   # 1小时
    "100GB": 7200,  # 2小时
}

# 分片大小配置
CHUNK_SIZES = {
    "small": 1024 * 1024,      # 1MB
    "medium": 5 * 1024 * 1024, # 5MB
    "large": 10 * 1024 * 1024, # 10MB
}

# 路径配置
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_FILES_DIR = os.path.join(PROJECT_ROOT, "test_files")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")

# 确保目录存在
for dir_path in [TEST_FILES_DIR, RESULTS_DIR, LOGS_DIR, REPORTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 日志配置
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# 测试标识
TEST_SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

# 资源监控配置
MONITOR_INTERVAL = 1  # 秒
MONITOR_DURATION = 3600  # 1小时

# 对比基线工具配置
BASELINE_TOOLS = {
    "scp": {
        "upload_cmd": "scp {file_path} user@localhost:/tmp/",
        "download_cmd": "scp user@localhost:/tmp/{filename} {local_path}",
        "enabled": False  # 需要SSH配置
    },
    "rsync": {
        "upload_cmd": "rsync -avz {file_path} user@localhost:/tmp/",
        "download_cmd": "rsync -avz user@localhost:/tmp/{filename} {local_path}",
        "enabled": False  # 需要SSH配置
    },
    "curl": {
        "upload_cmd": "curl -X POST -F 'file=@{file_path}' {base_url}/upload/",
        "download_cmd": "curl -o {local_path} {base_url}/download/{file_id}",
        "enabled": True
    }
}

# 安全测试配置
SECURITY_TESTS = {
    "auth_bypass": True,
    "token_validation": True,
    "permission_check": True,
    "path_traversal": True,
    "file_type_validation": True,
}

# 部署模拟配置
DEPLOYMENT_SIMULATION = {
    "institution": "首都医科大学",
    "users_count": 500,
    "daily_uploads": 200,
    "daily_downloads": 800,
    "avg_file_size_mb": 50,
    "peak_concurrent_users": 50,
    "simulation_days": 30,
}

# 性能阈值配置
PERFORMANCE_THRESHOLDS = {
    "min_throughput_mbps": 10,  # 最小吞吐量 MB/s
    "max_response_time_ms": 5000,  # 最大响应时间 ms
    "min_success_rate": 0.95,  # 最小成功率
    "max_cpu_usage": 0.8,  # 最大CPU使用率
    "max_memory_usage_gb": 4,  # 最大内存使用 GB
}

# 报告配置
REPORT_CONFIG = {
    "include_charts": True,
    "include_raw_data": True,
    "export_formats": ["html", "pdf", "json"],
    "chart_types": ["line", "bar", "scatter"],
}