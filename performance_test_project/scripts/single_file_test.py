#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单文件上传下载速度测试
Single File Upload/Download Speed Test
"""

import os
import sys
import time
import requests
from typing import Dict, List, Tuple

# 添加工具路径
sys.path.append(os.path.dirname(__file__))
from utils import *

class SingleFileSpeedTest:
    """单文件速度测试类"""
    
    def __init__(self):
        self.logger = TestLogger("SingleFileTest")
        self.auth_manager = AuthManager()
        self.file_generator = FileGenerator()
        self.performance_monitor = PerformanceMonitor()
        self.result_saver = ResultSaver()
        self.stats_calc = StatisticsCalculator()
        
        # 登录测试用户
        self.test_user = TEST_USERS[0]
        self.auth_manager.register_user(self.test_user["email"], self.test_user["password"])
        self.token = self.auth_manager.login_user(self.test_user["email"], self.test_user["password"])
        
        if not self.token:
            raise Exception("无法登录测试用户")
    
    def upload_file(self, file_path: str, folder_id: int = None) -> Tuple[bool, float, Dict]:
        """上传文件并测量性能"""
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        self.logger.info(f"开始上传文件: {filename} ({file_size / (1024*1024):.1f} MB)")
        
        # 开始性能监控
        self.performance_monitor.start_monitoring()
        
        start_time = time.time()
        success = False
        response_data = {}
        
        try:
            headers = self.auth_manager.get_auth_headers(self.test_user["email"])
            
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}
                data = {}
                if folder_id:
                    data['folder'] = folder_id
                
                response = requests.post(
                    f"{API_BASE_URL}/files/upload/",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=TIMEOUTS.get(self._get_size_label(file_size), 3600)
                )
                
                if response.status_code == 201:
                    success = True
                    response_data = response.json()
                    self.logger.info(f"文件上传成功: {filename}")
                else:
                    self.logger.error(f"文件上传失败: {filename}, 状态码: {response.status_code}")
                    response_data = {"error": response.text}
        
        except Exception as e:
            self.logger.error(f"上传过程中发生错误: {e}")
            response_data = {"error": str(e)}
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 停止性能监控
        self.performance_monitor.stop_monitoring()
        monitor_stats = self.performance_monitor.get_stats()
        
        # 计算吞吐量
        throughput = self.stats_calc.calculate_throughput(file_size, duration)
        
        result = {
            "success": success,
            "filename": filename,
            "file_size_bytes": file_size,
            "file_size_mb": file_size / (1024 * 1024),
            "duration_seconds": duration,
            "throughput_mbps": throughput,
            "response_data": response_data,
            "monitor_stats": monitor_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"上传完成 - 耗时: {duration:.2f}s, 吞吐量: {throughput:.2f} MB/s")
        
        return success, duration, result
    
    def download_file(self, file_id: int, expected_size: int) -> Tuple[bool, float, Dict]:
        """下载文件并测量性能"""
        self.logger.info(f"开始下载文件 ID: {file_id} (预期大小: {expected_size / (1024*1024):.1f} MB)")
        
        # 开始性能监控
        self.performance_monitor.start_monitoring()
        
        start_time = time.time()
        success = False
        downloaded_size = 0
        
        try:
            headers = self.auth_manager.get_auth_headers(self.test_user["email"])
            
            response = requests.get(
                f"{API_BASE_URL}/files/{file_id}/download/",
                headers=headers,
                stream=True,
                timeout=TIMEOUTS.get(self._get_size_label(expected_size), 3600)
            )
            
            if response.status_code == 200:
                # 下载到临时文件
                download_path = os.path.join(TEST_FILES_DIR, f"downloaded_{file_id}_{int(time.time())}.tmp")
                
                with open(download_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                
                success = True
                self.logger.info(f"文件下载成功: {downloaded_size / (1024*1024):.1f} MB")
                
                # 清理临时文件
                os.remove(download_path)
            else:
                self.logger.error(f"文件下载失败, 状态码: {response.status_code}")
        
        except Exception as e:
            self.logger.error(f"下载过程中发生错误: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 停止性能监控
        self.performance_monitor.stop_monitoring()
        monitor_stats = self.performance_monitor.get_stats()
        
        # 计算吞吐量
        throughput = self.stats_calc.calculate_throughput(downloaded_size, duration)
        
        result = {
            "success": success,
            "file_id": file_id,
            "expected_size_bytes": expected_size,
            "downloaded_size_bytes": downloaded_size,
            "downloaded_size_mb": downloaded_size / (1024 * 1024),
            "duration_seconds": duration,
            "throughput_mbps": throughput,
            "monitor_stats": monitor_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"下载完成 - 耗时: {duration:.2f}s, 吞吐量: {throughput:.2f} MB/s")
        
        return success, duration, result
    
    def _get_size_label(self, size_bytes: int) -> str:
        """根据文件大小获取标签"""
        for label, size in FILE_SIZES.items():
            if size_bytes <= size * 1.1:  # 允许10%的误差
                return label
        return "UNKNOWN"
    
    def run_single_file_test(self, size_label: str) -> Dict:
        """运行单个文件大小的测试"""
        self.logger.info(f"开始 {size_label} 文件测试")
        
        file_size = FILE_SIZES[size_label]
        filename = f"test_{size_label.lower()}_{int(time.time())}.bin"
        
        # 生成测试文件
        file_path = self.file_generator.generate_test_file(file_size, filename)
        
        upload_results = []
        download_results = []
        
        # 进行多次测试
        for iteration in range(TEST_ITERATIONS):
            self.logger.info(f"第 {iteration + 1}/{TEST_ITERATIONS} 次测试")
            
            # 上传测试
            upload_success, upload_duration, upload_result = self.upload_file(file_path)
            upload_results.append(upload_result)
            
            if upload_success and 'id' in upload_result.get('response_data', {}):
                file_id = upload_result['response_data']['id']
                
                # 等待一段时间再下载
                time.sleep(2)
                
                # 下载测试
                download_success, download_duration, download_result = self.download_file(file_id, file_size)
                download_results.append(download_result)
            else:
                self.logger.error(f"上传失败，跳过下载测试")
                download_results.append({
                    "success": False,
                    "error": "Upload failed",
                    "timestamp": datetime.now().isoformat()
                })
            
            # 测试间隔
            if iteration < TEST_ITERATIONS - 1:
                time.sleep(5)
        
        # 计算统计数据
        upload_stats = self._calculate_test_stats(upload_results, "upload")
        download_stats = self._calculate_test_stats(download_results, "download")
        
        result = {
            "size_label": size_label,
            "file_size_bytes": file_size,
            "file_size_mb": file_size / (1024 * 1024),
            "test_iterations": TEST_ITERATIONS,
            "upload_results": upload_results,
            "download_results": download_results,
            "upload_stats": upload_stats,
            "download_stats": download_stats,
            "test_timestamp": datetime.now().isoformat()
        }
        
        # 保存结果
        self.result_saver.save_test_result(f"single_file_{size_label.lower()}", result)
        
        self.logger.info(f"{size_label} 文件测试完成")
        return result
    
    def _calculate_test_stats(self, results: List[Dict], test_type: str) -> Dict:
        """计算测试统计数据"""
        successful_results = [r for r in results if r.get('success', False)]
        
        if not successful_results:
            return {
                "success_rate": 0,
                "avg_throughput_mbps": 0,
                "max_throughput_mbps": 0,
                "min_throughput_mbps": 0,
                "avg_duration_seconds": 0,
                "total_tests": len(results),
                "successful_tests": 0
            }
        
        throughputs = [r['throughput_mbps'] for r in successful_results]
        durations = [r['duration_seconds'] for r in successful_results]
        
        return {
            "success_rate": len(successful_results) / len(results),
            "avg_throughput_mbps": self.stats_calc.calculate_average(throughputs),
            "max_throughput_mbps": max(throughputs),
            "min_throughput_mbps": min(throughputs),
            "avg_duration_seconds": self.stats_calc.calculate_average(durations),
            "total_tests": len(results),
            "successful_tests": len(successful_results)
        }
    
    def run_all_tests(self) -> Dict:
        """运行所有文件大小的测试"""
        self.logger.info("开始单文件速度测试")
        
        all_results = {}
        summary_stats = {}
        
        for size_label in FILE_SIZES.keys():
            try:
                result = self.run_single_file_test(size_label)
                all_results[size_label] = result
                
                # 收集汇总统计
                summary_stats[size_label] = {
                    "upload_avg_throughput": result['upload_stats']['avg_throughput_mbps'],
                    "download_avg_throughput": result['download_stats']['avg_throughput_mbps'],
                    "upload_success_rate": result['upload_stats']['success_rate'],
                    "download_success_rate": result['download_stats']['success_rate']
                }
                
            except Exception as e:
                self.logger.error(f"{size_label} 测试失败: {e}")
                all_results[size_label] = {"error": str(e)}
        
        final_result = {
            "test_type": "single_file_speed",
            "test_session_id": TEST_SESSION_ID,
            "test_config": {
                "file_sizes": FILE_SIZES,
                "test_iterations": TEST_ITERATIONS,
                "base_url": BASE_URL
            },
            "results": all_results,
            "summary_stats": summary_stats,
            "test_completed": datetime.now().isoformat()
        }
        
        # 保存最终结果
        self.result_saver.save_test_result("single_file_speed_complete", final_result)
        
        self.logger.info("单文件速度测试完成")
        return final_result

def main():
    """主函数"""
    try:
        # 设置测试环境
        setup_test_environment()
        
        # 运行测试
        test = SingleFileSpeedTest()
        results = test.run_all_tests()
        
        # 打印汇总结果
        print("\n" + "="*60)
        print("单文件速度测试结果汇总")
        print("="*60)
        
        for size_label, stats in results.get('summary_stats', {}).items():
            print(f"\n{size_label}:")
            print(f"  上传平均吞吐量: {stats['upload_avg_throughput']:.2f} MB/s")
            print(f"  下载平均吞吐量: {stats['download_avg_throughput']:.2f} MB/s")
            print(f"  上传成功率: {stats['upload_success_rate']:.1%}")
            print(f"  下载成功率: {stats['download_success_rate']:.1%}")
        
        print("\n测试完成！详细结果已保存到 results 目录。")
        
    except Exception as e:
        print(f"测试失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())