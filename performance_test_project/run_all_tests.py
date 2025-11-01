#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主测试脚本 - 运行所有性能测试
Main Test Runner - Execute All Performance Tests
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

# 添加脚本路径
scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.append(scripts_dir)

from scripts.utils import TestLogger, ResultSaver, setup_test_environment, cleanup_test_environment

class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.logger = TestLogger("TestRunner")
        self.result_saver = ResultSaver()
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
        # 测试脚本配置
        self.test_scripts = [
            {
                "name": "单文件上传下载速度测试",
                "script": "single_file_test.py",
                "description": "测试不同大小文件的上传下载性能",
                "estimated_time": "30分钟"
            },
            {
                "name": "并发测试",
                "script": "concurrent_test.py", 
                "description": "测试不同并发级别下的系统性能",
                "estimated_time": "45分钟"
            },
            {
                "name": "断点续传测试",
                "script": "resume_test.py",
                "description": "测试断点续传功能的健壮性",
                "estimated_time": "20分钟"
            },
            {
                "name": "资源监控测试",
                "script": "resource_monitor.py",
                "description": "监控系统资源消耗",
                "estimated_time": "15分钟"
            },
            {
                "name": "基线对比测试",
                "script": "baseline_comparison.py",
                "description": "与传统工具进行性能对比",
                "estimated_time": "25分钟"
            },
            {
                "name": "安全性分析",
                "script": "security_analysis.py",
                "description": "进行安全性检测和分析",
                "estimated_time": "10分钟"
            },
            {
                "name": "部署案例模拟",
                "script": "deployment_simulation.py",
                "description": "模拟真实部署场景的使用统计",
                "estimated_time": "5分钟"
            }
        ]
    
    def run_single_test(self, test_config: Dict) -> Dict:
        """运行单个测试"""
        test_name = test_config["name"]
        script_name = test_config["script"]
        script_path = os.path.join(scripts_dir, script_name)
        
        self.logger.info(f"开始运行测试: {test_name}")
        self.logger.info(f"脚本路径: {script_path}")
        self.logger.info(f"预计耗时: {test_config['estimated_time']}")
        
        if not os.path.exists(script_path):
            error_msg = f"测试脚本不存在: {script_path}"
            self.logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": 0
            }
        
        # 记录开始时间
        test_start = time.time()
        start_time = datetime.now()
        
        try:
            # 运行测试脚本
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=3600,  # 1小时超时
                cwd=os.path.dirname(script_path)
            )
            
            # 记录结束时间
            test_end = time.time()
            end_time = datetime.now()
            duration = test_end - test_start
            
            if result.returncode == 0:
                self.logger.info(f"测试完成: {test_name} (耗时: {duration:.1f}秒)")
                
                # 尝试加载测试结果
                test_result_data = self.load_test_result_data(test_name)
                
                return {
                    "status": "success",
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": round(duration, 2),
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "test_data": test_result_data
                }
            else:
                error_msg = f"测试失败: {test_name}, 返回码: {result.returncode}"
                self.logger.error(error_msg)
                self.logger.error(f"错误输出: {result.stderr}")
                
                return {
                    "status": "failed",
                    "error": error_msg,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": round(duration, 2),
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            error_msg = f"测试超时: {test_name}"
            self.logger.error(error_msg)
            return {
                "status": "timeout",
                "error": error_msg,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": 3600
            }
            
        except Exception as e:
            error_msg = f"测试异常: {test_name}, 错误: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": time.time() - test_start
            }
    
    def load_test_result_data(self, test_name: str) -> Optional[Dict]:
        """加载测试结果数据"""
        try:
            # 根据测试名称推断结果文件
            result_files = {
                "单文件上传下载速度测试": "single_file_speed_test_complete",
                "并发测试": "concurrent_test_complete",
                "断点续传测试": "resume_test_complete", 
                "资源监控测试": "resource_monitor_complete",
                "基线对比测试": "baseline_comparison_complete",
                "安全性分析": "security_analysis_complete",
                "部署案例模拟": "deployment_simulation_complete"
            }
            
            result_key = result_files.get(test_name)
            if result_key:
                return self.result_saver.load_test_result(result_key)
            
        except Exception as e:
            self.logger.warning(f"无法加载测试结果数据: {test_name}, 错误: {e}")
        
        return None
    
    def run_all_tests(self) -> Dict:
        """运行所有测试"""
        self.logger.info("开始运行所有性能测试")
        self.start_time = datetime.now()
        
        # 设置测试环境
        try:
            setup_test_environment()
            self.logger.info("测试环境设置完成")
        except Exception as e:
            self.logger.error(f"测试环境设置失败: {e}")
            return {"status": "failed", "error": f"环境设置失败: {e}"}
        
        # 运行每个测试
        for i, test_config in enumerate(self.test_scripts, 1):
            test_name = test_config["name"]
            
            print(f"\n{'='*60}")
            print(f"运行测试 {i}/{len(self.test_scripts)}: {test_name}")
            print(f"描述: {test_config['description']}")
            print(f"预计耗时: {test_config['estimated_time']}")
            print(f"{'='*60}")
            
            # 运行测试
            test_result = self.run_single_test(test_config)
            self.test_results[test_name] = {
                **test_config,
                **test_result
            }
            
            # 打印测试结果摘要
            if test_result["status"] == "success":
                print(f"✅ {test_name} - 成功 (耗时: {test_result['duration_seconds']:.1f}秒)")
            else:
                print(f"❌ {test_name} - {test_result['status']}: {test_result.get('error', '未知错误')}")
        
        self.end_time = datetime.now()
        
        # 生成测试汇总
        test_summary = self.generate_test_summary()
        
        # 保存完整结果
        complete_results = {
            "test_summary": test_summary,
            "individual_tests": self.test_results,
            "execution_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "total_duration_seconds": (self.end_time - self.start_time).total_seconds(),
                "python_version": sys.version,
                "platform": sys.platform
            }
        }
        
        self.result_saver.save_test_result("all_tests_complete", complete_results)
        
        # 清理测试环境
        try:
            cleanup_test_environment()
            self.logger.info("测试环境清理完成")
        except Exception as e:
            self.logger.warning(f"测试环境清理失败: {e}")
        
        self.logger.info("所有测试运行完成")
        return complete_results
    
    def generate_test_summary(self) -> Dict:
        """生成测试汇总"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result.get("status") == "success")
        failed_tests = total_tests - successful_tests
        
        total_duration = (self.end_time - self.start_time).total_seconds()
        
        # 统计各测试的耗时
        test_durations = {}
        for test_name, result in self.test_results.items():
            test_durations[test_name] = result.get("duration_seconds", 0)
        
        return {
            "overview": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": round((successful_tests / total_tests) * 100, 1) if total_tests > 0 else 0,
                "total_duration_seconds": round(total_duration, 2),
                "total_duration_formatted": self.format_duration(total_duration)
            },
            "test_durations": test_durations,
            "failed_tests": [
                {
                    "name": name,
                    "error": result.get("error", "未知错误"),
                    "status": result.get("status", "unknown")
                }
                for name, result in self.test_results.items()
                if result.get("status") != "success"
            ]
        }
    
    def format_duration(self, seconds: float) -> str:
        """格式化持续时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟{secs}秒"
        elif minutes > 0:
            return f"{minutes}分钟{secs}秒"
        else:
            return f"{secs}秒"
    
    def print_final_summary(self, results: Dict):
        """打印最终汇总"""
        print(f"\n{'='*80}")
        print("测试运行完成 - 最终汇总")
        print(f"{'='*80}")
        
        summary = results["test_summary"]["overview"]
        print(f"\n📊 总体统计:")
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  成功测试: {summary['successful_tests']}")
        print(f"  失败测试: {summary['failed_tests']}")
        print(f"  成功率: {summary['success_rate']}%")
        print(f"  总耗时: {summary['total_duration_formatted']}")
        
        if summary['failed_tests'] > 0:
            print(f"\n❌ 失败的测试:")
            for failed_test in results["test_summary"]["failed_tests"]:
                print(f"  - {failed_test['name']}: {failed_test['error']}")
        
        print(f"\n⏱️  各测试耗时:")
        for test_name, duration in results["test_summary"]["test_durations"].items():
            status = "✅" if self.test_results[test_name].get("status") == "success" else "❌"
            print(f"  {status} {test_name}: {self.format_duration(duration)}")
        
        print(f"\n📁 详细结果已保存到: {self.result_saver.results_dir}")
        print(f"📋 测试报告将生成到: readme_test 文件")

def main():
    """主函数"""
    try:
        print("🚀 开始运行文件传输系统性能测试套件")
        print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 创建测试运行器
        runner = TestRunner()
        
        # 运行所有测试
        results = runner.run_all_tests()
        
        # 打印最终汇总
        runner.print_final_summary(results)
        
        return 0 if results["test_summary"]["overview"]["failed_tests"] == 0 else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        return 130
    except Exception as e:
        print(f"\n\n💥 测试运行失败: {e}")
        return 1

if __name__ == "__main__":
    exit(main())