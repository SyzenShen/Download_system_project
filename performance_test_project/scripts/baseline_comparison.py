#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比基线测试
Baseline Comparison Test
"""

import os
import sys
import time
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple

# 添加工具路径
sys.path.append(os.path.dirname(__file__))
from utils import *

class BaselineComparison:
    """基线对比测试类"""
    
    def __init__(self):
        self.logger = TestLogger("BaselineComparison")
        self.auth_manager = AuthManager()
        self.file_generator = FileGenerator()
        self.result_saver = ResultSaver()
        
        # 登录测试用户
        self.test_user = TEST_USERS[0]
        self.auth_manager.register_user(self.test_user["email"], self.test_user["password"])
        self.token = self.auth_manager.login_user(self.test_user["email"], self.test_user["password"])
        
        if not self.token:
            raise Exception("无法登录测试用户")
        
        # 创建临时目录用于基线测试
        self.temp_dir = tempfile.mkdtemp(prefix="baseline_test_")
        self.logger.info(f"临时目录: {self.temp_dir}")
    
    def cleanup(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.logger.info("临时目录已清理")
        except Exception as e:
            self.logger.error(f"清理临时目录失败: {e}")
    
    def test_our_system_upload(self, file_path: str) -> Dict:
        """测试我们系统的上传性能"""
        self.logger.info(f"测试我们系统上传: {os.path.basename(file_path)}")
        
        start_time = time.time()
        
        try:
            headers = self.auth_manager.get_auth_headers(self.test_user["email"])
            
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                
                response = requests.post(
                    f"{API_BASE_URL}/files/upload/",
                    files=files,
                    headers=headers,
                    timeout=600
                )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 201:
                file_size = os.path.getsize(file_path)
                throughput = (file_size / (1024 * 1024)) / duration  # MB/s
                
                return {
                    "success": True,
                    "duration": duration,
                    "throughput_mbps": throughput,
                    "file_size_bytes": file_size,
                    "file_id": response.json().get('id')
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "duration": duration
                }
                
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "error": str(e),
                "duration": end_time - start_time
            }
    
    def test_our_system_download(self, file_id: int, download_path: str) -> Dict:
        """测试我们系统的下载性能"""
        self.logger.info(f"测试我们系统下载: 文件ID {file_id}")
        
        start_time = time.time()
        
        try:
            headers = self.auth_manager.get_auth_headers(self.test_user["email"])
            
            response = requests.get(
                f"{API_BASE_URL}/files/{file_id}/download/",
                headers=headers,
                stream=True,
                timeout=600
            )
            
            if response.status_code == 200:
                with open(download_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                end_time = time.time()
                duration = end_time - start_time
                file_size = os.path.getsize(download_path)
                throughput = (file_size / (1024 * 1024)) / duration  # MB/s
                
                return {
                    "success": True,
                    "duration": duration,
                    "throughput_mbps": throughput,
                    "file_size_bytes": file_size
                }
            else:
                end_time = time.time()
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "duration": end_time - start_time
                }
                
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "error": str(e),
                "duration": end_time - start_time
            }
    
    def test_scp_upload(self, file_path: str, remote_host: str = "localhost") -> Dict:
        """测试SCP上传性能"""
        self.logger.info(f"测试SCP上传: {os.path.basename(file_path)}")
        
        remote_path = f"{remote_host}:{self.temp_dir}/scp_upload_{os.path.basename(file_path)}"
        
        start_time = time.time()
        
        try:
            # 使用scp命令
            cmd = ["scp", "-o", "StrictHostKeyChecking=no", file_path, remote_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result.returncode == 0:
                file_size = os.path.getsize(file_path)
                throughput = (file_size / (1024 * 1024)) / duration  # MB/s
                
                return {
                    "success": True,
                    "duration": duration,
                    "throughput_mbps": throughput,
                    "file_size_bytes": file_size,
                    "command": " ".join(cmd)
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "duration": duration,
                    "command": " ".join(cmd)
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout",
                "duration": 600
            }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "error": str(e),
                "duration": end_time - start_time
            }
    
    def test_rsync_upload(self, file_path: str, remote_host: str = "localhost") -> Dict:
        """测试rsync上传性能"""
        self.logger.info(f"测试rsync上传: {os.path.basename(file_path)}")
        
        remote_path = f"{remote_host}:{self.temp_dir}/"
        
        start_time = time.time()
        
        try:
            # 使用rsync命令
            cmd = ["rsync", "-avz", "--progress", file_path, remote_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result.returncode == 0:
                file_size = os.path.getsize(file_path)
                throughput = (file_size / (1024 * 1024)) / duration  # MB/s
                
                return {
                    "success": True,
                    "duration": duration,
                    "throughput_mbps": throughput,
                    "file_size_bytes": file_size,
                    "command": " ".join(cmd),
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "duration": duration,
                    "command": " ".join(cmd)
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout",
                "duration": 600
            }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "error": str(e),
                "duration": end_time - start_time
            }
    
    def test_curl_upload(self, file_path: str) -> Dict:
        """测试curl上传性能"""
        self.logger.info(f"测试curl上传: {os.path.basename(file_path)}")
        
        start_time = time.time()
        
        try:
            # 获取认证token
            headers = self.auth_manager.get_auth_headers(self.test_user["email"])
            auth_header = f"Authorization: {headers['Authorization']}"
            
            # 使用curl命令
            cmd = [
                "curl", "-X", "POST",
                "-H", auth_header,
                "-F", f"file=@{file_path}",
                f"{API_BASE_URL}/files/upload/",
                "-w", "%{time_total},%{speed_upload}",
                "-s", "-o", "/dev/null"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result.returncode == 0:
                # 解析curl的输出
                output_parts = result.stdout.strip().split(',')
                if len(output_parts) >= 2:
                    curl_time = float(output_parts[0])
                    curl_speed = float(output_parts[1])  # bytes/sec
                    
                    file_size = os.path.getsize(file_path)
                    throughput = curl_speed / (1024 * 1024)  # MB/s
                    
                    return {
                        "success": True,
                        "duration": curl_time,
                        "throughput_mbps": throughput,
                        "file_size_bytes": file_size,
                        "command": " ".join(cmd),
                        "curl_speed_bytes_per_sec": curl_speed
                    }
                else:
                    file_size = os.path.getsize(file_path)
                    throughput = (file_size / (1024 * 1024)) / duration
                    
                    return {
                        "success": True,
                        "duration": duration,
                        "throughput_mbps": throughput,
                        "file_size_bytes": file_size,
                        "command": " ".join(cmd)
                    }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "duration": duration,
                    "command": " ".join(cmd)
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout",
                "duration": 600
            }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "error": str(e),
                "duration": end_time - start_time
            }
    
    def test_wget_download(self, url: str, download_path: str) -> Dict:
        """测试wget下载性能"""
        self.logger.info(f"测试wget下载")
        
        start_time = time.time()
        
        try:
            # 获取认证token
            headers = self.auth_manager.get_auth_headers(self.test_user["email"])
            auth_header = f"Authorization: {headers['Authorization']}"
            
            # 使用wget命令
            cmd = [
                "wget", "--header", auth_header,
                "-O", download_path,
                "--progress=bar:force",
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result.returncode == 0 and os.path.exists(download_path):
                file_size = os.path.getsize(download_path)
                throughput = (file_size / (1024 * 1024)) / duration  # MB/s
                
                return {
                    "success": True,
                    "duration": duration,
                    "throughput_mbps": throughput,
                    "file_size_bytes": file_size,
                    "command": " ".join(cmd),
                    "output": result.stderr  # wget输出到stderr
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "duration": duration,
                    "command": " ".join(cmd)
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout",
                "duration": 600
            }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "error": str(e),
                "duration": end_time - start_time
            }
    
    def run_comparison_test(self, file_size_label: str) -> Dict:
        """运行单个文件大小的对比测试"""
        self.logger.info(f"开始对比测试: {file_size_label}")
        
        file_size = FILE_SIZES[file_size_label]
        filename = f"baseline_test_{file_size_label.lower()}_{int(time.time())}.bin"
        file_path = self.file_generator.generate_test_file(file_size, filename)
        
        results = {
            "file_size_label": file_size_label,
            "file_size_bytes": file_size,
            "test_file": filename,
            "timestamp": datetime.now().isoformat()
        }
        
        # 测试我们的系统上传
        self.logger.info("测试我们系统的上传...")
        our_upload = self.test_our_system_upload(file_path)
        results["our_system_upload"] = our_upload
        
        file_id = None
        if our_upload.get("success"):
            file_id = our_upload.get("file_id")
        
        # 测试curl上传
        self.logger.info("测试curl上传...")
        curl_upload = self.test_curl_upload(file_path)
        results["curl_upload"] = curl_upload
        
        # 如果有SSH访问权限，测试scp和rsync
        try:
            # 测试scp上传（需要SSH配置）
            self.logger.info("测试scp上传...")
            scp_upload = self.test_scp_upload(file_path)
            results["scp_upload"] = scp_upload
        except Exception as e:
            self.logger.warning(f"SCP测试跳过: {e}")
            results["scp_upload"] = {"success": False, "error": "SSH not configured", "skipped": True}
        
        try:
            # 测试rsync上传（需要SSH配置）
            self.logger.info("测试rsync上传...")
            rsync_upload = self.test_rsync_upload(file_path)
            results["rsync_upload"] = rsync_upload
        except Exception as e:
            self.logger.warning(f"rsync测试跳过: {e}")
            results["rsync_upload"] = {"success": False, "error": "SSH not configured", "skipped": True}
        
        # 下载测试
        if file_id:
            # 测试我们系统的下载
            self.logger.info("测试我们系统的下载...")
            download_path = os.path.join(self.temp_dir, f"our_download_{filename}")
            our_download = self.test_our_system_download(file_id, download_path)
            results["our_system_download"] = our_download
            
            # 测试wget下载
            self.logger.info("测试wget下载...")
            download_url = f"{API_BASE_URL}/files/{file_id}/download/"
            wget_download_path = os.path.join(self.temp_dir, f"wget_download_{filename}")
            wget_download = self.test_wget_download(download_url, wget_download_path)
            results["wget_download"] = wget_download
        
        # 清理测试文件
        try:
            os.remove(file_path)
        except:
            pass
        
        return results
    
    def run_all_comparison_tests(self) -> Dict:
        """运行所有对比测试"""
        self.logger.info("开始基线对比测试")
        
        # 选择测试文件大小
        test_sizes = ["10MB", "100MB", "1GB"]  # 适中的文件大小用于对比
        
        all_results = {}
        
        for size_label in test_sizes:
            try:
                result = self.run_comparison_test(size_label)
                all_results[size_label] = result
                
                # 保存单个测试结果
                self.result_saver.save_test_result(
                    f"baseline_comparison_{size_label.lower()}",
                    result
                )
                
                self.logger.info(f"{size_label} 对比测试完成")
                
            except Exception as e:
                self.logger.error(f"{size_label} 对比测试失败: {e}")
                all_results[size_label] = {"error": str(e)}
            
            # 测试间隔
            time.sleep(30)
        
        # 生成对比统计
        comparison_stats = self.generate_comparison_stats(all_results)
        
        final_result = {
            "test_type": "baseline_comparison",
            "test_session_id": TEST_SESSION_ID,
            "test_config": {
                "test_sizes": test_sizes,
                "tools_tested": ["our_system", "curl", "scp", "rsync", "wget"]
            },
            "results": all_results,
            "comparison_stats": comparison_stats,
            "test_completed": datetime.now().isoformat()
        }
        
        # 保存最终结果
        self.result_saver.save_test_result("baseline_comparison_complete", final_result)
        
        self.logger.info("基线对比测试完成")
        return final_result
    
    def generate_comparison_stats(self, results: Dict) -> Dict:
        """生成对比统计"""
        stats = {}
        
        for size_label, result in results.items():
            if "error" in result:
                continue
            
            size_stats = {
                "file_size_label": size_label,
                "upload_comparison": {},
                "download_comparison": {}
            }
            
            # 上传对比
            upload_tools = ["our_system_upload", "curl_upload", "scp_upload", "rsync_upload"]
            upload_throughputs = {}
            
            for tool in upload_tools:
                if tool in result and result[tool].get("success"):
                    throughput = result[tool].get("throughput_mbps", 0)
                    upload_throughputs[tool] = throughput
            
            if upload_throughputs:
                best_upload = max(upload_throughputs.items(), key=lambda x: x[1])
                size_stats["upload_comparison"] = {
                    "throughputs_mbps": upload_throughputs,
                    "best_performer": best_upload[0],
                    "best_throughput_mbps": best_upload[1]
                }
                
                # 计算相对性能
                our_throughput = upload_throughputs.get("our_system_upload", 0)
                if our_throughput > 0:
                    relative_performance = {}
                    for tool, throughput in upload_throughputs.items():
                        if tool != "our_system_upload":
                            relative_performance[tool] = our_throughput / throughput if throughput > 0 else 0
                    size_stats["upload_comparison"]["relative_to_our_system"] = relative_performance
            
            # 下载对比
            download_tools = ["our_system_download", "wget_download"]
            download_throughputs = {}
            
            for tool in download_tools:
                if tool in result and result[tool].get("success"):
                    throughput = result[tool].get("throughput_mbps", 0)
                    download_throughputs[tool] = throughput
            
            if download_throughputs:
                best_download = max(download_throughputs.items(), key=lambda x: x[1])
                size_stats["download_comparison"] = {
                    "throughputs_mbps": download_throughputs,
                    "best_performer": best_download[0],
                    "best_throughput_mbps": best_download[1]
                }
                
                # 计算相对性能
                our_throughput = download_throughputs.get("our_system_download", 0)
                if our_throughput > 0:
                    relative_performance = {}
                    for tool, throughput in download_throughputs.items():
                        if tool != "our_system_download":
                            relative_performance[tool] = our_throughput / throughput if throughput > 0 else 0
                    size_stats["download_comparison"]["relative_to_our_system"] = relative_performance
            
            stats[size_label] = size_stats
        
        return stats

def main():
    """主函数"""
    try:
        # 设置测试环境
        setup_test_environment()
        
        # 运行对比测试
        comparison = BaselineComparison()
        
        try:
            results = comparison.run_all_comparison_tests()
            
            # 打印汇总结果
            print("\n" + "="*60)
            print("基线对比测试结果汇总")
            print("="*60)
            
            for size_label, stats in results.get('comparison_stats', {}).items():
                print(f"\n{size_label}:")
                
                # 上传对比
                upload_comp = stats.get('upload_comparison', {})
                if upload_comp:
                    print("  上传性能对比:")
                    throughputs = upload_comp.get('throughputs_mbps', {})
                    for tool, throughput in throughputs.items():
                        print(f"    {tool}: {throughput:.2f} MB/s")
                    
                    best = upload_comp.get('best_performer', '')
                    if best:
                        print(f"    最佳: {best}")
                
                # 下载对比
                download_comp = stats.get('download_comparison', {})
                if download_comp:
                    print("  下载性能对比:")
                    throughputs = download_comp.get('throughputs_mbps', {})
                    for tool, throughput in throughputs.items():
                        print(f"    {tool}: {throughput:.2f} MB/s")
                    
                    best = download_comp.get('best_performer', '')
                    if best:
                        print(f"    最佳: {best}")
            
            print("\n测试完成！详细结果已保存到 results 目录。")
            
        finally:
            comparison.cleanup()
        
    except Exception as e:
        print(f"测试失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())