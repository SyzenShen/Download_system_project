#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发上传下载测试
Concurrent Upload/Download Test
"""

import os
import sys
import time
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

# 添加工具路径
sys.path.append(os.path.dirname(__file__))
from utils import *

class ConcurrentTest:
    """并发测试类"""
    
    def __init__(self):
        self.logger = TestLogger("ConcurrentTest")
        self.auth_manager = AuthManager()
        self.file_generator = FileGenerator()
        self.performance_monitor = PerformanceMonitor()
        self.result_saver = ResultSaver()
        self.stats_calc = StatisticsCalculator()
        
        # 准备测试用户
        self.test_users = []
        for i, user in enumerate(TEST_USERS):
            self.auth_manager.register_user(user["email"], user["password"])
            token = self.auth_manager.login_user(user["email"], user["password"])
            if token:
                self.test_users.append(user)
            
            if len(self.test_users) >= max(CONCURRENT_LEVELS):
                break
        
        if len(self.test_users) < max(CONCURRENT_LEVELS):
            raise Exception(f"需要至少 {max(CONCURRENT_LEVELS)} 个测试用户")
        
        self.logger.info(f"准备了 {len(self.test_users)} 个测试用户")
    
    def upload_file_worker(self, user_email: str, file_path: str, result_queue: queue.Queue):
        """上传文件工作线程"""
        worker_id = threading.current_thread().name
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        start_time = time.time()
        success = False
        error_msg = ""
        
        try:
            headers = self.auth_manager.get_auth_headers(user_email)
            
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}
                
                response = requests.post(
                    f"{API_BASE_URL}/files/upload/",
                    files=files,
                    headers=headers,
                    timeout=300  # 5分钟超时
                )
                
                if response.status_code == 201:
                    success = True
                    response_data = response.json()
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
        
        except Exception as e:
            error_msg = str(e)
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = self.stats_calc.calculate_throughput(file_size, duration)
        
        result = {
            "worker_id": worker_id,
            "user_email": user_email,
            "filename": filename,
            "file_size_bytes": file_size,
            "success": success,
            "duration_seconds": duration,
            "throughput_mbps": throughput,
            "start_time": start_time,
            "end_time": end_time,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        
        result_queue.put(result)
        
        if success:
            self.logger.debug(f"[{worker_id}] 上传成功: {filename} - {throughput:.2f} MB/s")
        else:
            self.logger.error(f"[{worker_id}] 上传失败: {filename} - {error_msg}")
    
    def download_file_worker(self, user_email: str, file_id: int, expected_size: int, result_queue: queue.Queue):
        """下载文件工作线程"""
        worker_id = threading.current_thread().name
        
        start_time = time.time()
        success = False
        downloaded_size = 0
        error_msg = ""
        
        try:
            headers = self.auth_manager.get_auth_headers(user_email)
            
            response = requests.get(
                f"{API_BASE_URL}/files/{file_id}/download/",
                headers=headers,
                stream=True,
                timeout=300  # 5分钟超时
            )
            
            if response.status_code == 200:
                # 下载到内存（不保存文件）
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        downloaded_size += len(chunk)
                
                success = True
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
        
        except Exception as e:
            error_msg = str(e)
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = self.stats_calc.calculate_throughput(downloaded_size, duration)
        
        result = {
            "worker_id": worker_id,
            "user_email": user_email,
            "file_id": file_id,
            "expected_size_bytes": expected_size,
            "downloaded_size_bytes": downloaded_size,
            "success": success,
            "duration_seconds": duration,
            "throughput_mbps": throughput,
            "start_time": start_time,
            "end_time": end_time,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        
        result_queue.put(result)
        
        if success:
            self.logger.debug(f"[{worker_id}] 下载成功: {file_id} - {throughput:.2f} MB/s")
        else:
            self.logger.error(f"[{worker_id}] 下载失败: {file_id} - {error_msg}")
    
    def run_concurrent_upload_test(self, concurrent_level: int, file_size_label: str) -> Dict:
        """运行并发上传测试"""
        self.logger.info(f"开始 {concurrent_level} 并发上传测试 ({file_size_label})")
        
        file_size = FILE_SIZES[file_size_label]
        
        # 生成测试文件
        filename = f"concurrent_test_{file_size_label.lower()}_{int(time.time())}.bin"
        file_path = self.file_generator.generate_test_file(file_size, filename)
        
        # 开始性能监控
        self.performance_monitor.start_monitoring()
        
        # 准备结果队列
        result_queue = queue.Queue()
        
        # 创建线程
        threads = []
        test_start_time = time.time()
        
        for i in range(concurrent_level):
            user = self.test_users[i % len(self.test_users)]
            thread = threading.Thread(
                target=self.upload_file_worker,
                args=(user["email"], file_path, result_queue),
                name=f"Upload-{i+1}"
            )
            threads.append(thread)
        
        # 启动所有线程
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        test_end_time = time.time()
        total_duration = test_end_time - test_start_time
        
        # 停止性能监控
        self.performance_monitor.stop_monitoring()
        monitor_stats = self.performance_monitor.get_stats()
        
        # 收集结果
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        # 计算统计数据
        successful_results = [r for r in results if r['success']]
        success_rate = len(successful_results) / len(results) if results else 0
        
        if successful_results:
            throughputs = [r['throughput_mbps'] for r in successful_results]
            durations = [r['duration_seconds'] for r in successful_results]
            
            avg_throughput = sum(throughputs) / len(throughputs)
            total_throughput = sum(r['file_size_bytes'] for r in successful_results) / (1024 * 1024) / total_duration
        else:
            avg_throughput = 0
            total_throughput = 0
        
        result = {
            "test_type": "concurrent_upload",
            "concurrent_level": concurrent_level,
            "file_size_label": file_size_label,
            "file_size_bytes": file_size,
            "total_duration_seconds": total_duration,
            "success_rate": success_rate,
            "successful_uploads": len(successful_results),
            "total_uploads": len(results),
            "avg_individual_throughput_mbps": avg_throughput,
            "total_system_throughput_mbps": total_throughput,
            "individual_results": results,
            "monitor_stats": monitor_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"并发上传测试完成 - 成功率: {success_rate:.1%}, 系统吞吐量: {total_throughput:.2f} MB/s")
        
        return result
    
    def run_concurrent_download_test(self, concurrent_level: int, file_size_label: str) -> Dict:
        """运行并发下载测试"""
        self.logger.info(f"开始 {concurrent_level} 并发下载测试 ({file_size_label})")
        
        file_size = FILE_SIZES[file_size_label]
        
        # 首先上传一个文件供下载
        filename = f"download_test_{file_size_label.lower()}_{int(time.time())}.bin"
        file_path = self.file_generator.generate_test_file(file_size, filename)
        
        # 上传文件
        test_user = self.test_users[0]
        headers = self.auth_manager.get_auth_headers(test_user["email"])
        
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/octet-stream')}
            response = requests.post(
                f"{API_BASE_URL}/files/upload/",
                files=files,
                headers=headers,
                timeout=600
            )
        
        if response.status_code != 201:
            raise Exception(f"无法上传测试文件: {response.status_code}")
        
        file_id = response.json()['id']
        self.logger.info(f"测试文件已上传，ID: {file_id}")
        
        # 开始性能监控
        self.performance_monitor.start_monitoring()
        
        # 准备结果队列
        result_queue = queue.Queue()
        
        # 创建线程
        threads = []
        test_start_time = time.time()
        
        for i in range(concurrent_level):
            user = self.test_users[i % len(self.test_users)]
            thread = threading.Thread(
                target=self.download_file_worker,
                args=(user["email"], file_id, file_size, result_queue),
                name=f"Download-{i+1}"
            )
            threads.append(thread)
        
        # 启动所有线程
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        test_end_time = time.time()
        total_duration = test_end_time - test_start_time
        
        # 停止性能监控
        self.performance_monitor.stop_monitoring()
        monitor_stats = self.performance_monitor.get_stats()
        
        # 收集结果
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        # 计算统计数据
        successful_results = [r for r in results if r['success']]
        success_rate = len(successful_results) / len(results) if results else 0
        
        if successful_results:
            throughputs = [r['throughput_mbps'] for r in successful_results]
            total_throughput = sum(r['downloaded_size_bytes'] for r in successful_results) / (1024 * 1024) / total_duration
            avg_throughput = sum(throughputs) / len(throughputs)
        else:
            avg_throughput = 0
            total_throughput = 0
        
        result = {
            "test_type": "concurrent_download",
            "concurrent_level": concurrent_level,
            "file_size_label": file_size_label,
            "file_size_bytes": file_size,
            "file_id": file_id,
            "total_duration_seconds": total_duration,
            "success_rate": success_rate,
            "successful_downloads": len(successful_results),
            "total_downloads": len(results),
            "avg_individual_throughput_mbps": avg_throughput,
            "total_system_throughput_mbps": total_throughput,
            "individual_results": results,
            "monitor_stats": monitor_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"并发下载测试完成 - 成功率: {success_rate:.1%}, 系统吞吐量: {total_throughput:.2f} MB/s")
        
        return result
    
    def run_all_concurrent_tests(self) -> Dict:
        """运行所有并发测试"""
        self.logger.info("开始并发测试")
        
        all_results = {}
        
        # 选择中等大小的文件进行并发测试
        test_file_size = "100MB"
        
        for concurrent_level in CONCURRENT_LEVELS:
            self.logger.info(f"测试并发级别: {concurrent_level}")
            
            try:
                # 上传测试
                upload_result = self.run_concurrent_upload_test(concurrent_level, test_file_size)
                
                # 等待一段时间
                time.sleep(10)
                
                # 下载测试
                download_result = self.run_concurrent_download_test(concurrent_level, test_file_size)
                
                all_results[concurrent_level] = {
                    "upload": upload_result,
                    "download": download_result
                }
                
                # 保存单个并发级别的结果
                self.result_saver.save_test_result(
                    f"concurrent_{concurrent_level}",
                    all_results[concurrent_level]
                )
                
            except Exception as e:
                self.logger.error(f"并发级别 {concurrent_level} 测试失败: {e}")
                all_results[concurrent_level] = {"error": str(e)}
            
            # 测试间隔
            time.sleep(30)
        
        # 生成汇总统计
        summary_stats = {}
        for level, results in all_results.items():
            if "error" not in results:
                summary_stats[level] = {
                    "upload_success_rate": results["upload"]["success_rate"],
                    "download_success_rate": results["download"]["success_rate"],
                    "upload_system_throughput": results["upload"]["total_system_throughput_mbps"],
                    "download_system_throughput": results["download"]["total_system_throughput_mbps"]
                }
        
        final_result = {
            "test_type": "concurrent_performance",
            "test_session_id": TEST_SESSION_ID,
            "test_config": {
                "concurrent_levels": CONCURRENT_LEVELS,
                "test_file_size": test_file_size,
                "test_users_count": len(self.test_users)
            },
            "results": all_results,
            "summary_stats": summary_stats,
            "test_completed": datetime.now().isoformat()
        }
        
        # 保存最终结果
        self.result_saver.save_test_result("concurrent_complete", final_result)
        
        self.logger.info("并发测试完成")
        return final_result

def main():
    """主函数"""
    try:
        # 设置测试环境
        setup_test_environment()
        
        # 运行测试
        test = ConcurrentTest()
        results = test.run_all_concurrent_tests()
        
        # 打印汇总结果
        print("\n" + "="*60)
        print("并发测试结果汇总")
        print("="*60)
        
        for level, stats in results.get('summary_stats', {}).items():
            print(f"\n并发级别 {level}:")
            print(f"  上传成功率: {stats['upload_success_rate']:.1%}")
            print(f"  下载成功率: {stats['download_success_rate']:.1%}")
            print(f"  上传系统吞吐量: {stats['upload_system_throughput']:.2f} MB/s")
            print(f"  下载系统吞吐量: {stats['download_system_throughput']:.2f} MB/s")
        
        print("\n测试完成！详细结果已保存到 results 目录。")
        
    except Exception as e:
        print(f"测试失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())