#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全性检测和分析
Security Analysis and Testing
"""

import os
import sys
import time
import requests
import ssl
import socket
import subprocess
import json
from urllib.parse import urlparse
from typing import Dict, List, Optional

# 添加工具路径
sys.path.append(os.path.dirname(__file__))
from utils import *

class SecurityAnalyzer:
    """安全性分析器"""
    
    def __init__(self):
        self.logger = TestLogger("SecurityAnalyzer")
        self.auth_manager = AuthManager()
        self.result_saver = ResultSaver()
        
        # 解析API基础URL
        self.parsed_url = urlparse(API_BASE_URL)
        self.host = self.parsed_url.hostname
        self.port = self.parsed_url.port or (443 if self.parsed_url.scheme == 'https' else 80)
        self.is_https = self.parsed_url.scheme == 'https'
    
    def test_https_configuration(self) -> Dict:
        """测试HTTPS配置"""
        self.logger.info("检查HTTPS配置")
        
        result = {
            "test_name": "https_configuration",
            "url": API_BASE_URL,
            "is_https": self.is_https,
            "timestamp": datetime.now().isoformat()
        }
        
        if not self.is_https:
            result.update({
                "status": "FAIL",
                "issue": "未启用HTTPS",
                "risk_level": "HIGH",
                "recommendation": "启用HTTPS以保护数据传输安全"
            })
            return result
        
        try:
            # 检查SSL证书
            context = ssl.create_default_context()
            
            with socket.create_connection((self.host, self.port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.host) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()
                    
                    result.update({
                        "status": "PASS",
                        "ssl_version": version,
                        "cipher_suite": cipher[0] if cipher else None,
                        "certificate": {
                            "subject": dict(x[0] for x in cert.get('subject', [])),
                            "issuer": dict(x[0] for x in cert.get('issuer', [])),
                            "version": cert.get('version'),
                            "serial_number": cert.get('serialNumber'),
                            "not_before": cert.get('notBefore'),
                            "not_after": cert.get('notAfter')
                        }
                    })
                    
                    # 检查证书有效期
                    import datetime as dt
                    not_after = dt.datetime.strptime(cert.get('notAfter'), '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (not_after - dt.datetime.now()).days
                    
                    if days_until_expiry < 30:
                        result["warning"] = f"证书将在{days_until_expiry}天后过期"
                    
                    result["certificate"]["days_until_expiry"] = days_until_expiry
        
        except Exception as e:
            result.update({
                "status": "ERROR",
                "error": str(e),
                "risk_level": "MEDIUM"
            })
        
        return result
    
    def test_authentication_flow(self) -> Dict:
        """测试认证流程"""
        self.logger.info("测试认证流程")
        
        result = {
            "test_name": "authentication_flow",
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # 测试用户注册
        test_email = f"security_test_{int(time.time())}@example.com"
        test_password = "SecurePassword123!"
        
        try:
            # 1. 测试用户注册
            register_result = self.test_user_registration(test_email, test_password)
            result["tests"]["registration"] = register_result
            
            # 2. 测试用户登录
            login_result = self.test_user_login(test_email, test_password)
            result["tests"]["login"] = login_result
            
            # 3. 测试token验证
            if login_result.get("success"):
                token = login_result.get("token")
                token_validation_result = self.test_token_validation(token)
                result["tests"]["token_validation"] = token_validation_result
                
                # 4. 测试token生命周期
                token_lifecycle_result = self.test_token_lifecycle(token)
                result["tests"]["token_lifecycle"] = token_lifecycle_result
            
            # 5. 测试密码安全性
            password_security_result = self.test_password_security()
            result["tests"]["password_security"] = password_security_result
            
            # 6. 测试未授权访问
            unauthorized_access_result = self.test_unauthorized_access()
            result["tests"]["unauthorized_access"] = unauthorized_access_result
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def test_user_registration(self, email: str, password: str) -> Dict:
        """测试用户注册"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/register/",
                json={"email": email, "password": password},
                timeout=30
            )
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_user_login(self, email: str, password: str) -> Dict:
        """测试用户登录"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/login/",
                json={"email": email, "password": password},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token') or data.get('token')
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "token": token,
                    "has_refresh_token": 'refresh_token' in data,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_token_validation(self, token: str) -> Dict:
        """测试token验证"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试访问受保护的端点
            response = requests.get(
                f"{API_BASE_URL}/auth/user/",
                headers=headers,
                timeout=30
            )
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "token_accepted": response.status_code == 200
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_token_lifecycle(self, token: str) -> Dict:
        """测试token生命周期"""
        result = {
            "token_format_analysis": self.analyze_token_format(token),
            "token_expiry_test": self.test_token_expiry(token)
        }
        
        return result
    
    def analyze_token_format(self, token: str) -> Dict:
        """分析token格式"""
        try:
            # 检查是否是JWT
            parts = token.split('.')
            
            if len(parts) == 3:
                # 可能是JWT
                import base64
                import json
                
                # 解码header
                header_data = base64.b64decode(parts[0] + '==').decode('utf-8')
                header = json.loads(header_data)
                
                # 解码payload（不验证签名）
                payload_data = base64.b64decode(parts[1] + '==').decode('utf-8')
                payload = json.loads(payload_data)
                
                return {
                    "format": "JWT",
                    "algorithm": header.get('alg'),
                    "type": header.get('typ'),
                    "issued_at": payload.get('iat'),
                    "expires_at": payload.get('exp'),
                    "issuer": payload.get('iss'),
                    "subject": payload.get('sub'),
                    "audience": payload.get('aud')
                }
            else:
                return {
                    "format": "OPAQUE",
                    "length": len(token),
                    "character_set": "alphanumeric" if token.isalnum() else "mixed"
                }
                
        except Exception as e:
            return {
                "format": "UNKNOWN",
                "error": str(e)
            }
    
    def test_token_expiry(self, token: str) -> Dict:
        """测试token过期"""
        # 这里可以实现token过期测试
        # 由于实际测试中token可能不会立即过期，我们模拟测试
        return {
            "test_type": "simulated",
            "note": "Token过期测试需要等待实际过期时间或修改系统时间"
        }
    
    def test_password_security(self) -> Dict:
        """测试密码安全性"""
        result = {
            "weak_password_tests": [],
            "password_policy_check": {}
        }
        
        weak_passwords = [
            "123456",
            "password",
            "admin",
            "test",
            "qwerty",
            "abc123"
        ]
        
        for weak_password in weak_passwords:
            test_email = f"weak_test_{int(time.time())}_{weak_password}@example.com"
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/auth/register/",
                    json={"email": test_email, "password": weak_password},
                    timeout=30
                )
                
                result["weak_password_tests"].append({
                    "password": weak_password,
                    "accepted": response.status_code == 201,
                    "status_code": response.status_code,
                    "response": response.text if response.status_code != 201 else "Accepted"
                })
                
            except Exception as e:
                result["weak_password_tests"].append({
                    "password": weak_password,
                    "error": str(e)
                })
        
        # 检查是否有密码策略
        accepted_weak = sum(1 for test in result["weak_password_tests"] if test.get("accepted", False))
        result["password_policy_check"] = {
            "weak_passwords_accepted": accepted_weak,
            "total_tested": len(weak_passwords),
            "has_password_policy": accepted_weak == 0
        }
        
        return result
    
    def test_unauthorized_access(self) -> Dict:
        """测试未授权访问"""
        result = {
            "endpoints_tested": [],
            "summary": {}
        }
        
        # 测试的端点
        test_endpoints = [
            {"url": f"{API_BASE_URL}/files/", "method": "GET"},
            {"url": f"{API_BASE_URL}/files/upload/", "method": "POST"},
            {"url": f"{API_BASE_URL}/folders/", "method": "GET"},
            {"url": f"{API_BASE_URL}/auth/user/", "method": "GET"}
        ]
        
        for endpoint in test_endpoints:
            try:
                if endpoint["method"] == "GET":
                    response = requests.get(endpoint["url"], timeout=30)
                elif endpoint["method"] == "POST":
                    response = requests.post(endpoint["url"], timeout=30)
                else:
                    continue
                
                test_result = {
                    "url": endpoint["url"],
                    "method": endpoint["method"],
                    "status_code": response.status_code,
                    "requires_auth": response.status_code in [401, 403],
                    "accessible_without_auth": response.status_code == 200
                }
                
                result["endpoints_tested"].append(test_result)
                
            except Exception as e:
                result["endpoints_tested"].append({
                    "url": endpoint["url"],
                    "method": endpoint["method"],
                    "error": str(e)
                })
        
        # 汇总
        accessible_count = sum(1 for test in result["endpoints_tested"] 
                             if test.get("accessible_without_auth", False))
        protected_count = sum(1 for test in result["endpoints_tested"] 
                            if test.get("requires_auth", False))
        
        result["summary"] = {
            "total_endpoints": len(test_endpoints),
            "accessible_without_auth": accessible_count,
            "properly_protected": protected_count,
            "security_score": protected_count / len(test_endpoints) if test_endpoints else 0
        }
        
        return result
    
    def test_permission_isolation(self) -> Dict:
        """测试权限隔离"""
        self.logger.info("测试权限隔离")
        
        result = {
            "test_name": "permission_isolation",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 创建两个测试用户
            user1_email = f"user1_{int(time.time())}@example.com"
            user2_email = f"user2_{int(time.time())}@example.com"
            password = "TestPassword123!"
            
            # 注册用户
            self.auth_manager.register_user(user1_email, password)
            self.auth_manager.register_user(user2_email, password)
            
            # 登录获取token
            token1 = self.auth_manager.login_user(user1_email, password)
            token2 = self.auth_manager.login_user(user2_email, password)
            
            if not token1 or not token2:
                result["error"] = "无法获取用户token"
                return result
            
            # 用户1上传文件
            headers1 = {"Authorization": f"Bearer {token1}"}
            
            # 创建测试文件
            test_content = b"This is a test file for permission isolation"
            files = {'file': ('test_isolation.txt', test_content, 'text/plain')}
            
            upload_response = requests.post(
                f"{API_BASE_URL}/files/upload/",
                files=files,
                headers=headers1,
                timeout=30
            )
            
            if upload_response.status_code != 201:
                result["error"] = f"文件上传失败: {upload_response.status_code}"
                return result
            
            file_id = upload_response.json().get('id')
            
            # 用户2尝试访问用户1的文件
            headers2 = {"Authorization": f"Bearer {token2}"}
            
            access_response = requests.get(
                f"{API_BASE_URL}/files/{file_id}/",
                headers=headers2,
                timeout=30
            )
            
            download_response = requests.get(
                f"{API_BASE_URL}/files/{file_id}/download/",
                headers=headers2,
                timeout=30
            )
            
            result.update({
                "user1_upload_success": True,
                "file_id": file_id,
                "user2_can_access_metadata": access_response.status_code == 200,
                "user2_can_download": download_response.status_code == 200,
                "access_status_code": access_response.status_code,
                "download_status_code": download_response.status_code,
                "isolation_working": access_response.status_code in [403, 404] and download_response.status_code in [403, 404]
            })
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def run_security_scan(self) -> Dict:
        """运行完整的安全扫描"""
        self.logger.info("开始安全性检测")
        
        scan_results = {
            "scan_type": "comprehensive_security_analysis",
            "test_session_id": TEST_SESSION_ID,
            "scan_started": datetime.now().isoformat(),
            "tests": {}
        }
        
        # 1. HTTPS配置检查
        self.logger.info("检查HTTPS配置...")
        scan_results["tests"]["https_configuration"] = self.test_https_configuration()
        
        # 2. 认证流程测试
        self.logger.info("测试认证流程...")
        scan_results["tests"]["authentication_flow"] = self.test_authentication_flow()
        
        # 3. 权限隔离测试
        self.logger.info("测试权限隔离...")
        scan_results["tests"]["permission_isolation"] = self.test_permission_isolation()
        
        # 4. 生成安全评分
        security_score = self.calculate_security_score(scan_results["tests"])
        scan_results["security_assessment"] = security_score
        
        scan_results["scan_completed"] = datetime.now().isoformat()
        
        # 保存结果
        self.result_saver.save_test_result("security_analysis_complete", scan_results)
        
        self.logger.info("安全性检测完成")
        return scan_results
    
    def calculate_security_score(self, test_results: Dict) -> Dict:
        """计算安全评分"""
        score = 0
        max_score = 0
        issues = []
        recommendations = []
        
        # HTTPS配置评分
        https_test = test_results.get("https_configuration", {})
        max_score += 20
        if https_test.get("status") == "PASS":
            score += 20
        elif https_test.get("status") == "FAIL":
            issues.append("未启用HTTPS")
            recommendations.append("启用HTTPS以保护数据传输")
        
        # 认证流程评分
        auth_test = test_results.get("authentication_flow", {})
        auth_tests = auth_test.get("tests", {})
        
        # 密码策略
        max_score += 15
        password_test = auth_tests.get("password_security", {})
        password_policy = password_test.get("password_policy_check", {})
        if password_policy.get("has_password_policy", False):
            score += 15
        else:
            issues.append("缺少密码强度策略")
            recommendations.append("实施强密码策略")
        
        # 未授权访问保护
        max_score += 20
        unauth_test = auth_tests.get("unauthorized_access", {})
        security_score_ratio = unauth_test.get("summary", {}).get("security_score", 0)
        score += int(20 * security_score_ratio)
        
        if security_score_ratio < 1.0:
            issues.append("部分端点未受保护")
            recommendations.append("确保所有敏感端点都需要认证")
        
        # 权限隔离
        max_score += 25
        isolation_test = test_results.get("permission_isolation", {})
        if isolation_test.get("isolation_working", False):
            score += 25
        else:
            issues.append("用户权限隔离不完善")
            recommendations.append("加强用户数据访问控制")
        
        # Token安全性
        max_score += 20
        token_test = auth_tests.get("token_lifecycle", {})
        token_format = token_test.get("token_format_analysis", {})
        if token_format.get("format") == "JWT":
            score += 15  # JWT相对安全
            if token_format.get("algorithm") in ["HS256", "RS256"]:
                score += 5
        elif token_format.get("format") == "OPAQUE":
            score += 10  # 不透明token也可以
        
        # 计算最终评分
        final_score = (score / max_score) * 100 if max_score > 0 else 0
        
        # 确定安全等级
        if final_score >= 90:
            security_level = "EXCELLENT"
        elif final_score >= 75:
            security_level = "GOOD"
        elif final_score >= 60:
            security_level = "FAIR"
        elif final_score >= 40:
            security_level = "POOR"
        else:
            security_level = "CRITICAL"
        
        return {
            "overall_score": round(final_score, 1),
            "security_level": security_level,
            "score_breakdown": {
                "https_configuration": 20,
                "password_policy": 15,
                "endpoint_protection": 20,
                "permission_isolation": 25,
                "token_security": 20
            },
            "achieved_score": score,
            "max_possible_score": max_score,
            "issues_found": issues,
            "recommendations": recommendations
        }

def main():
    """主函数"""
    try:
        # 设置测试环境
        setup_test_environment()
        
        # 运行安全扫描
        analyzer = SecurityAnalyzer()
        results = analyzer.run_security_scan()
        
        # 打印汇总结果
        print("\n" + "="*60)
        print("安全性检测结果汇总")
        print("="*60)
        
        assessment = results.get('security_assessment', {})
        print(f"\n总体安全评分: {assessment.get('overall_score', 0)}/100")
        print(f"安全等级: {assessment.get('security_level', 'UNKNOWN')}")
        
        issues = assessment.get('issues_found', [])
        if issues:
            print(f"\n发现的安全问题 ({len(issues)}):")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        
        recommendations = assessment.get('recommendations', [])
        if recommendations:
            print(f"\n安全建议 ({len(recommendations)}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        # 详细测试结果
        tests = results.get('tests', {})
        print(f"\n详细测试结果:")
        
        # HTTPS配置
        https_test = tests.get('https_configuration', {})
        print(f"  HTTPS配置: {https_test.get('status', 'UNKNOWN')}")
        
        # 认证流程
        auth_test = tests.get('authentication_flow', {})
        auth_tests = auth_test.get('tests', {})
        print(f"  用户注册: {'✓' if auth_tests.get('registration', {}).get('success') else '✗'}")
        print(f"  用户登录: {'✓' if auth_tests.get('login', {}).get('success') else '✗'}")
        print(f"  Token验证: {'✓' if auth_tests.get('token_validation', {}).get('success') else '✗'}")
        
        # 权限隔离
        isolation_test = tests.get('permission_isolation', {})
        print(f"  权限隔离: {'✓' if isolation_test.get('isolation_working') else '✗'}")
        
        print("\n测试完成！详细结果已保存到 results 目录。")
        
    except Exception as e:
        print(f"测试失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())