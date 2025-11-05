#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
断点续传健壮性测试
Resume Transfer Robustness Test
"""

import os
import sys
import time
import signal
import subprocess
import threading
import requests
from typing import Dict, List, Tuple, Optional

# 添加工具路径
sys.path.append(os.path.dirname(__file__))
from utils import *

class ResumeTest:
    """断点续传测试类"""
    
    def __init__(self):
        self.logger = TestLogger("ResumeTest")
        self.auth_manager = AuthManager()
        self.file_generator = FileGenerator()
        self.result_saver = ResultSaver()
        
        # 登录测试用户
        self.test_user = TEST_USERS[0]
        self.auth_manager.register_user(self.test_user["email"], self.test_user["password"])
        self.token = self.auth_manager.login_user(self.test_user["email"], self.test_user["password"])
        
        if not self.token:
            raise Exception("无法登录测试用户")
    
    def start_chunked_upload(self, file_path: str, chunk_size: int = 5*1024*1024) -> Tuple[str, int]:
        """开始分片上传"""
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        headers = self.auth_manager.get_auth_headers(self.test_user["email"])
        
        # 初始化上传会话
        response = requests.post(
            f"{API_BASE_URL}/files/chunked-upload/init/",
            json={
                "filename": filename,
                "total_size": file_size,
                "chunk_size": chunk_size
            },
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 201:
            raise Exception(f"初始化上传失败: {response.status_code}")
        
        upload_session_id = response.json()['upload_session_id']
        self.logger.info(f"上传会话已创建: {upload_session_id}")
        
        return upload_session_id, file_size
    
    def upload_chunk(self, upload_session_id: str, file_path: str, chunk_index: int, chunk_size: int) -> bool:
        """上传单个分片"""
        headers = self.auth_manager.get_auth_headers(self.test_user["email"])
        
        start_byte = chunk_index * chunk_size
        
        with open(file_path, 'rb') as f:
            f.seek(start_byte)
            chunk_data = f.read(chunk_size)
        
        if not chunk_data:
            return False
        
        end_byte = start_byte + len(chunk_data) - 1
        file_size = os.path.getsize(file_path)
        
        files = {'chunk': ('chunk', chunk_data, 'application/octet-stream')}
        data = {
            'upload_session_id': upload_session_id,
            'chunk_index': chunk_index
        }
        
        # 设置Content-Range头
        headers['Content-Range'] = f'bytes {start_byte}-{end_byte}/{file_size}'
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/files/chunked-upload/chunk/",
                files=files,
                data=data,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                self.logger.debug(f"分片 {chunk_index} 上传成功")
                return True
            else:
                self.logger.error(f"分片 {chunk_index} 上传失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"分片 {chunk_index} 上传异常: {e}")
            return False
    
    def complete_upload(self, upload_session_id: str) -> Optional[Dict]:
        """完成上传"""
        headers = self.auth_manager.get_auth_headers(self.test_user["email"])
        
        response = requests.post(
            f"{API_BASE_URL}/files/chunked-upload/complete/",
            json={"upload_session_id": upload_session_id},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 201:
            self.logger.info("上传完成")
            return response.json()
        else:
            self.logger.error(f"完成上传失败: {response.status_code}")
            return None
    
    def get_upload_status(self, upload_session_id: str) -> Optional[Dict]:
        """获取上传状态"""
        headers = self.auth_manager.get_auth_headers(self.test_user["email"])
        
        response = requests.get(
            f"{API_BASE_URL}/files/chunked-upload/status/{upload_session_id}/",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error(f"获取上传状态失败: {response.status_code}")
            return None
    
    def simulate_network_interruption(self, duration: int = 10):
        """模拟网络中断"""
        self.logger.info(f"模拟网络中断 {duration} 秒")
        
        # 这里可以实现真实的网络中断模拟
        # 例如：修改防火墙规则、断开网络连接等
        # 为了简化，我们使用sleep来模拟
        time.sleep(duration)
        
        self.logger.info("网络恢复")
    
    def test_upload_interruption_recovery(self, file_size_label: str) -> Dict:
        """测试上传中断恢复"""
        self.logger.info(f"开始上传中断恢复测试 ({file_size_label})")
        
        file_size = FILE_SIZES[file_size_label]
        filename = f"resume_test_{file_size_label.lower()}_{int(time.time())}.bin"
        file_path = self.file_generator.generate_test_file(file_size, filename)
        
        # 计算原始文件MD5
        original_md5 = self.file_generator.calculate_md5(file_path)
        
        chunk_size = 5 * 1024 * 1024  # 5MB chunks
        total_chunks = (file_size + chunk_size - 1) // chunk_size
        
        test_start_time = time.time()
        
        try:
            # 开始上传
            upload_session_id, _ = self.start_chunked_upload(file_path, chunk_size)
            
            # 上传前几个分片
            interruption_point = total_chunks // 2  # 在中间位置中断
            
            for chunk_index in range(interruption_point):
                success = self.upload_chunk(upload_session_id, file_path, chunk_index, chunk_size)
                if not success:
                    raise Exception(f"分片 {chunk_index} 上传失败")
                time.sleep(0.1)  # 小延迟
            
            self.logger.info(f"已上传 {interruption_point}/{total_chunks} 个分片，开始模拟中断")
            
            # 模拟网络中断
            interruption_start = time.time()
            self.simulate_network_interruption(15)  # 中断15秒
            interruption_duration = time.time() - interruption_start
            
            # 检查上传状态
            status = self.get_upload_status(upload_session_id)
            if not status:
                raise Exception("无法获取上传状态")
            
            uploaded_chunks = status.get('uploaded_chunks', 0)
            self.logger.info(f"中断后状态: 已上传 {uploaded_chunks} 个分片")
            
            # 恢复上传
            recovery_start = time.time()
            
            for chunk_index in range(uploaded_chunks, total_chunks):
                success = self.upload_chunk(upload_session_id, file_path, chunk_index, chunk_size)
                if not success:
                    raise Exception(f"恢复上传分片 {chunk_index} 失败")
                time.sleep(0.1)
            
            # 完成上传
            result = self.complete_upload(upload_session_id)
            if not result:
                raise Exception("完成上传失败")
            
            recovery_end = time.time()
            recovery_duration = recovery_end - recovery_start
            
            # 验证文件完整性
            file_id = result['id']
            integrity_check = self.verify_file_integrity(file_id, original_md5)
            
            test_end_time = time.time()
            total_duration = test_end_time - test_start_time
            
            return {
                "test_type": "upload_interruption_recovery",
                "file_size_label": file_size_label,
                "file_size_bytes": file_size,
                "original_md5": original_md5,
                "total_chunks": total_chunks,
                "interruption_point": interruption_point,
                "interruption_duration": interruption_duration,
                "recovery_duration": recovery_duration,
                "total_duration": total_duration,
                "integrity_check": integrity_check,
                "upload_session_id": upload_session_id,
                "file_id": file_id,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"上传中断恢复测试失败: {e}")
            return {
                "test_type": "upload_interruption_recovery",
                "file_size_label": file_size_label,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def test_download_interruption_recovery(self, file_id: int, expected_size: int, expected_md5: str) -> Dict:
        """测试下载中断恢复"""
        self.logger.info(f"开始下载中断恢复测试 (文件ID: {file_id})")
        
        download_path = os.path.join(TEST_FILES_DIR, f"download_resume_test_{file_id}_{int(time.time())}.bin")
        
        test_start_time = time.time()
        
        try:
            headers = self.auth_manager.get_auth_headers(self.test_user["email"])
            
            # 第一次下载（部分）
            partial_size = expected_size // 2
            headers['Range'] = f'bytes=0-{partial_size-1}'
            
            response = requests.get(
                f"{API_BASE_URL}/files/{file_id}/download/",
                headers=headers,
                stream=True,
                timeout=300
            )
            
            if response.status_code not in [200, 206]:
                raise Exception(f"部分下载失败: {response.status_code}")
            
            # 保存部分数据
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            partial_downloaded = os.path.getsize(download_path)
            self.logger.info(f"第一次下载了 {partial_downloaded / (1024*1024):.1f} MB")
            
            # 模拟中断
            interruption_start = time.time()
            self.simulate_network_interruption(10)
            interruption_duration = time.time() - interruption_start
            
            # 恢复下载（断点续传）
            recovery_start = time.time()
            
            headers = self.auth_manager.get_auth_headers(self.test_user["email"])
            headers['Range'] = f'bytes={partial_downloaded}-'
            
            response = requests.get(
                f"{API_BASE_URL}/files/{file_id}/download/",
                headers=headers,
                stream=True,
                timeout=300
            )
            
            if response.status_code not in [200, 206]:
                raise Exception(f"断点续传下载失败: {response.status_code}")
            
            # 追加剩余数据
            with open(download_path, 'ab') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            recovery_end = time.time()
            recovery_duration = recovery_end - recovery_start
            
            # 验证文件完整性
            final_size = os.path.getsize(download_path)
            downloaded_md5 = self.file_generator.calculate_md5(download_path)
            
            integrity_check = {
                "size_match": final_size == expected_size,
                "md5_match": downloaded_md5 == expected_md5,
                "expected_size": expected_size,
                "actual_size": final_size,
                "expected_md5": expected_md5,
                "actual_md5": downloaded_md5
            }
            
            # 清理下载文件
            os.remove(download_path)
            
            test_end_time = time.time()
            total_duration = test_end_time - test_start_time
            
            return {
                "test_type": "download_interruption_recovery",
                "file_id": file_id,
                "expected_size_bytes": expected_size,
                "partial_downloaded_bytes": partial_downloaded,
                "interruption_duration": interruption_duration,
                "recovery_duration": recovery_duration,
                "total_duration": total_duration,
                "integrity_check": integrity_check,
                "success": integrity_check["size_match"] and integrity_check["md5_match"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"下载中断恢复测试失败: {e}")
            return {
                "test_type": "download_interruption_recovery",
                "file_id": file_id,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def verify_file_integrity(self, file_id: int, expected_md5: str) -> Dict:
        """验证文件完整性"""
        try:
            headers = self.auth_manager.get_auth_headers(self.test_user["email"])
            
            # 下载文件进行验证
            response = requests.get(
                f"{API_BASE_URL}/files/{file_id}/download/",
                headers=headers,
                stream=True,
                timeout=300
            )
            
            if response.status_code != 200:
                return {"valid": False, "error": f"下载失败: {response.status_code}"}
            
            # 计算下载文件的MD5
            hash_md5 = hashlib.md5()
            downloaded_size = 0
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    hash_md5.update(chunk)
                    downloaded_size += len(chunk)
            
            actual_md5 = hash_md5.hexdigest()
            
            return {
                "valid": actual_md5 == expected_md5,
                "expected_md5": expected_md5,
                "actual_md5": actual_md5,
                "downloaded_size": downloaded_size
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def run_all_resume_tests(self) -> Dict:
        """运行所有断点续传测试"""
        self.logger.info("开始断点续传健壮性测试")
        
        all_results = {}
        
        # 测试不同文件大小
        test_sizes = ["100MB", "1GB"]  # 选择中等和大文件
        
        for size_label in test_sizes:
            self.logger.info(f"测试文件大小: {size_label}")
            
            try:
                # 上传中断恢复测试
                upload_result = self.test_upload_interruption_recovery(size_label)
                
                if upload_result.get("success") and "file_id" in upload_result:
                    # 下载中断恢复测试
                    download_result = self.test_download_interruption_recovery(
                        upload_result["file_id"],
                        upload_result["file_size_bytes"],
                        upload_result["original_md5"]
                    )
                else:
                    download_result = {
                        "test_type": "download_interruption_recovery",
                        "success": False,
                        "error": "Upload test failed",
                        "timestamp": datetime.now().isoformat()
                    }
                
                all_results[size_label] = {
                    "upload_resume": upload_result,
                    "download_resume": download_result
                }
                
                # 保存单个测试结果
                self.result_saver.save_test_result(
                    f"resume_test_{size_label.lower()}",
                    all_results[size_label]
                )
                
            except Exception as e:
                self.logger.error(f"{size_label} 断点续传测试失败: {e}")
                all_results[size_label] = {"error": str(e)}
            
            # 测试间隔
            time.sleep(10)
        
        # 生成汇总统计
        summary_stats = {}
        for size, results in all_results.items():
            if "error" not in results:
                upload_success = results["upload_resume"].get("success", False)
                download_success = results["download_resume"].get("success", False)
                
                summary_stats[size] = {
                    "upload_resume_success": upload_success,
                    "download_resume_success": download_success,
                    "overall_success": upload_success and download_success
                }
                
                if upload_success:
                    summary_stats[size]["upload_recovery_time"] = results["upload_resume"]["recovery_duration"]
                
                if download_success:
                    summary_stats[size]["download_recovery_time"] = results["download_resume"]["recovery_duration"]
        
        final_result = {
            "test_type": "resume_robustness",
            "test_session_id": TEST_SESSION_ID,
            "test_config": {
                "test_sizes": test_sizes,
                "interruption_duration": 15,
                "chunk_size_mb": 5
            },
            "results": all_results,
            "summary_stats": summary_stats,
            "test_completed": datetime.now().isoformat()
        }
        
        # 保存最终结果
        self.result_saver.save_test_result("resume_robustness_complete", final_result)
        
        self.logger.info("断点续传健壮性测试完成")
        return final_result

def main():
    """主函数"""
    try:
        # 设置测试环境
        setup_test_environment()
        
        # 运行测试
        test = ResumeTest()
        results = test.run_all_resume_tests()
        
        # 打印汇总结果
        print("\n" + "="*60)
        print("断点续传健壮性测试结果汇总")
        print("="*60)
        
        for size, stats in results.get('summary_stats', {}).items():
            print(f"\n{size}:")
            print(f"  上传断点续传: {'✓' if stats['upload_resume_success'] else '✗'}")
            print(f"  下载断点续传: {'✓' if stats['download_resume_success'] else '✗'}")
            print(f"  整体成功: {'✓' if stats['overall_success'] else '✗'}")
            
            if 'upload_recovery_time' in stats:
                print(f"  上传恢复时间: {stats['upload_recovery_time']:.2f}s")
            if 'download_recovery_time' in stats:
                print(f"  下载恢复时间: {stats['download_recovery_time']:.2f}s")
        
        print("\n测试完成！详细结果已保存到 results 目录。")
        
    except Exception as e:
        print(f"测试失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())