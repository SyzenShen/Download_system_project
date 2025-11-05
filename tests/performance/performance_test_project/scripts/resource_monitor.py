#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源消耗监控脚本
Resource Consumption Monitor
"""

import os
import sys
import time
import psutil
import threading
import subprocess
from typing import Dict, List, Optional
from datetime import datetime

# 添加工具路径
sys.path.append(os.path.dirname(__file__))
from utils import *

class ResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self, sample_interval: float = 1.0):
        self.logger = TestLogger("ResourceMonitor")
        self.sample_interval = sample_interval
        self.monitoring = False
        self.monitor_thread = None
        self.resource_data = []
        self.start_time = None
        
        # 获取系统信息
        self.system_info = self.get_system_info()
        self.logger.info(f"系统信息: {self.system_info}")
    
    def get_system_info(self) -> Dict:
        """获取系统基本信息"""
        try:
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_physical_cores": cpu_count,
                "cpu_logical_cores": cpu_count_logical,
                "total_memory_gb": round(memory.total / (1024**3), 2),
                "total_disk_gb": round(disk.total / (1024**3), 2),
                "platform": psutil.WINDOWS if os.name == 'nt' else psutil.LINUX if os.name == 'posix' else 'unknown'
            }
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return {}
    
    def get_network_stats(self) -> Dict:
        """获取网络统计信息"""
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        except Exception as e:
            self.logger.error(f"获取网络统计失败: {e}")
            return {}
    
    def get_disk_io_stats(self) -> Dict:
        """获取磁盘I/O统计信息"""
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                return {
                    "read_bytes": disk_io.read_bytes,
                    "write_bytes": disk_io.write_bytes,
                    "read_count": disk_io.read_count,
                    "write_count": disk_io.write_count,
                    "read_time": disk_io.read_time,
                    "write_time": disk_io.write_time
                }
            else:
                return {}
        except Exception as e:
            self.logger.error(f"获取磁盘I/O统计失败: {e}")
            return {}
    
    def get_process_stats(self, process_name: str = "python") -> List[Dict]:
        """获取特定进程的资源使用情况"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'io_counters']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        cpu_percent = proc.cpu_percent()
                        memory_info = proc.memory_info()
                        io_counters = proc.io_counters() if hasattr(proc, 'io_counters') else None
                        
                        process_data = {
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "cpu_percent": cpu_percent,
                            "memory_rss_mb": round(memory_info.rss / (1024*1024), 2),
                            "memory_vms_mb": round(memory_info.vms / (1024*1024), 2)
                        }
                        
                        if io_counters:
                            process_data.update({
                                "io_read_bytes": io_counters.read_bytes,
                                "io_write_bytes": io_counters.write_bytes,
                                "io_read_count": io_counters.read_count,
                                "io_write_count": io_counters.write_count
                            })
                        
                        processes.append(process_data)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"获取进程统计失败: {e}")
        
        return processes
    
    def sample_resources(self) -> Dict:
        """采样系统资源"""
        timestamp = datetime.now()
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # 磁盘使用情况
            disk_usage = psutil.disk_usage('/')
            disk_io = self.get_disk_io_stats()
            
            # 网络使用情况
            network_io = self.get_network_stats()
            
            # 进程信息
            python_processes = self.get_process_stats("python")
            
            # 负载平均值（仅Linux/macOS）
            load_avg = None
            try:
                if hasattr(os, 'getloadavg'):
                    load_avg = os.getloadavg()
            except:
                pass
            
            sample_data = {
                "timestamp": timestamp.isoformat(),
                "elapsed_seconds": (timestamp - self.start_time).total_seconds() if self.start_time else 0,
                
                # CPU信息
                "cpu": {
                    "total_percent": cpu_percent,
                    "per_core_percent": cpu_per_core,
                    "load_average": load_avg
                },
                
                # 内存信息
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent,
                    "swap_total_gb": round(swap.total / (1024**3), 2),
                    "swap_used_gb": round(swap.used / (1024**3), 2),
                    "swap_percent": swap.percent
                },
                
                # 磁盘信息
                "disk": {
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "used_gb": round(disk_usage.used / (1024**3), 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                    "percent": (disk_usage.used / disk_usage.total) * 100,
                    "io": disk_io
                },
                
                # 网络信息
                "network": network_io,
                
                # 进程信息
                "processes": {
                    "python_processes": python_processes,
                    "total_processes": len(psutil.pids())
                }
            }
            
            return sample_data
            
        except Exception as e:
            self.logger.error(f"资源采样失败: {e}")
            return {
                "timestamp": timestamp.isoformat(),
                "error": str(e)
            }
    
    def monitor_loop(self):
        """监控循环"""
        self.logger.info(f"开始资源监控，采样间隔: {self.sample_interval}s")
        
        while self.monitoring:
            try:
                sample = self.sample_resources()
                self.resource_data.append(sample)
                
                # 限制内存使用，保留最近的数据
                if len(self.resource_data) > 10000:
                    self.resource_data = self.resource_data[-5000:]
                
                time.sleep(self.sample_interval)
                
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                time.sleep(self.sample_interval)
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            self.logger.warning("监控已在运行")
            return
        
        self.monitoring = True
        self.start_time = datetime.now()
        self.resource_data = []
        
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("资源监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.monitoring:
            self.logger.warning("监控未在运行")
            return
        
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("资源监控已停止")
    
    def get_statistics(self) -> Dict:
        """获取监控统计信息"""
        if not self.resource_data:
            return {"error": "没有监控数据"}
        
        try:
            # 提取数值数据
            cpu_data = [sample["cpu"]["total_percent"] for sample in self.resource_data if "cpu" in sample]
            memory_data = [sample["memory"]["percent"] for sample in self.resource_data if "memory" in sample]
            
            # 计算统计值
            stats = {
                "monitoring_duration_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                "total_samples": len(self.resource_data),
                "sample_interval": self.sample_interval,
                
                "cpu": {
                    "avg_percent": sum(cpu_data) / len(cpu_data) if cpu_data else 0,
                    "max_percent": max(cpu_data) if cpu_data else 0,
                    "min_percent": min(cpu_data) if cpu_data else 0
                },
                
                "memory": {
                    "avg_percent": sum(memory_data) / len(memory_data) if memory_data else 0,
                    "max_percent": max(memory_data) if memory_data else 0,
                    "min_percent": min(memory_data) if memory_data else 0
                }
            }
            
            # 添加最新样本信息
            if self.resource_data:
                latest = self.resource_data[-1]
                stats["latest_sample"] = latest
            
            return stats
            
        except Exception as e:
            self.logger.error(f"计算统计信息失败: {e}")
            return {"error": str(e)}
    
    def save_monitoring_data(self, test_name: str):
        """保存监控数据"""
        try:
            result_saver = ResultSaver()
            
            monitoring_result = {
                "test_name": test_name,
                "system_info": self.system_info,
                "monitoring_config": {
                    "sample_interval": self.sample_interval,
                    "start_time": self.start_time.isoformat() if self.start_time else None
                },
                "statistics": self.get_statistics(),
                "raw_data": self.resource_data,
                "saved_at": datetime.now().isoformat()
            }
            
            result_saver.save_test_result(f"resource_monitor_{test_name}", monitoring_result)
            self.logger.info(f"监控数据已保存: {test_name}")
            
        except Exception as e:
            self.logger.error(f"保存监控数据失败: {e}")

class LoadTestResourceMonitor:
    """负载测试资源监控器"""
    
    def __init__(self):
        self.logger = TestLogger("LoadTestResourceMonitor")
        self.result_saver = ResultSaver()
    
    def run_load_test_monitoring(self, test_scenarios: List[Dict]) -> Dict:
        """运行负载测试监控"""
        self.logger.info("开始负载测试资源监控")
        
        all_results = {}
        
        for scenario in test_scenarios:
            scenario_name = scenario["name"]
            duration = scenario.get("duration", 300)  # 默认5分钟
            
            self.logger.info(f"开始监控场景: {scenario_name}")
            
            # 创建监控器
            monitor = ResourceMonitor(sample_interval=1.0)
            
            try:
                # 开始监控
                monitor.start_monitoring()
                
                # 模拟负载（这里可以集成实际的负载测试）
                self.simulate_load(scenario)
                
                # 等待测试完成
                time.sleep(duration)
                
                # 停止监控
                monitor.stop_monitoring()
                
                # 获取统计信息
                stats = monitor.get_statistics()
                
                # 保存监控数据
                monitor.save_monitoring_data(scenario_name)
                
                all_results[scenario_name] = {
                    "scenario": scenario,
                    "statistics": stats,
                    "success": True
                }
                
                self.logger.info(f"场景 {scenario_name} 监控完成")
                
            except Exception as e:
                self.logger.error(f"场景 {scenario_name} 监控失败: {e}")
                all_results[scenario_name] = {
                    "scenario": scenario,
                    "success": False,
                    "error": str(e)
                }
            
            # 场景间隔
            time.sleep(30)
        
        # 保存汇总结果
        final_result = {
            "test_type": "load_test_resource_monitoring",
            "test_session_id": TEST_SESSION_ID,
            "scenarios": test_scenarios,
            "results": all_results,
            "test_completed": datetime.now().isoformat()
        }
        
        self.result_saver.save_test_result("load_test_monitoring_complete", final_result)
        
        self.logger.info("负载测试资源监控完成")
        return final_result
    
    def simulate_load(self, scenario: Dict):
        """模拟负载"""
        load_type = scenario.get("type", "idle")
        
        if load_type == "cpu_intensive":
            self.logger.info("模拟CPU密集型负载")
            # 这里可以启动CPU密集型任务
            
        elif load_type == "memory_intensive":
            self.logger.info("模拟内存密集型负载")
            # 这里可以启动内存密集型任务
            
        elif load_type == "io_intensive":
            self.logger.info("模拟I/O密集型负载")
            # 这里可以启动I/O密集型任务
            
        else:
            self.logger.info("空闲状态监控")

def main():
    """主函数"""
    try:
        # 设置测试环境
        setup_test_environment()
        
        # 定义测试场景
        test_scenarios = [
            {
                "name": "idle_baseline",
                "type": "idle",
                "duration": 60,
                "description": "系统空闲基线"
            },
            {
                "name": "light_load",
                "type": "light",
                "duration": 180,
                "description": "轻负载（1-10个并发）"
            },
            {
                "name": "medium_load",
                "type": "medium",
                "duration": 300,
                "description": "中等负载（10-50个并发）"
            },
            {
                "name": "heavy_load",
                "type": "heavy",
                "duration": 300,
                "description": "重负载（50-100个并发）"
            }
        ]
        
        # 运行负载测试监控
        monitor = LoadTestResourceMonitor()
        results = monitor.run_load_test_monitoring(test_scenarios)
        
        # 打印汇总结果
        print("\n" + "="*60)
        print("资源消耗监控测试结果汇总")
        print("="*60)
        
        for scenario_name, result in results.get('results', {}).items():
            print(f"\n{scenario_name}:")
            if result.get('success'):
                stats = result['statistics']
                print(f"  监控时长: {stats.get('monitoring_duration_seconds', 0):.1f}s")
                print(f"  采样数量: {stats.get('total_samples', 0)}")
                
                cpu_stats = stats.get('cpu', {})
                print(f"  CPU使用率: 平均{cpu_stats.get('avg_percent', 0):.1f}% "
                      f"最大{cpu_stats.get('max_percent', 0):.1f}%")
                
                memory_stats = stats.get('memory', {})
                print(f"  内存使用率: 平均{memory_stats.get('avg_percent', 0):.1f}% "
                      f"最大{memory_stats.get('max_percent', 0):.1f}%")
            else:
                print(f"  测试失败: {result.get('error', '未知错误')}")
        
        print("\n测试完成！详细结果已保存到 results 目录。")
        
    except Exception as e:
        print(f"测试失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())