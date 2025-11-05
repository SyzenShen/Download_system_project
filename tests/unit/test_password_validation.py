#!/usr/bin/env python3
"""
测试密码复杂度验证功能（移除特殊字符要求后）
"""

import os
import sys
import django
import requests
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'file_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.validators import ComplexPasswordValidator

User = get_user_model()

def test_backend_password_validation():
    """测试后端密码验证器"""
    print("=== 测试后端密码验证器 ===")
    validator = ComplexPasswordValidator()
    
    # 测试密码列表（移除特殊字符要求后）
    test_passwords = [
        ("12345678", False, "只有数字，缺少大小写字母"),
        ("abcdefgh", False, "只有小写字母，缺少大写字母和数字"),
        ("ABCDEFGH", False, "只有大写字母，缺少小写字母和数字"),
        ("Abc123", False, "长度不足8位"),
        ("Abcdefgh", False, "缺少数字"),
        ("ABC12345", False, "缺少小写字母"),
        ("abc12345", False, "缺少大写字母"),
        ("Abc12345", True, "符合要求：大小写字母+数字，8位以上"),
        ("MyPassword123", True, "符合要求：大小写字母+数字"),
        ("Test1234", True, "符合要求：大小写字母+数字"),
        ("Password1", True, "符合要求：大小写字母+数字"),
        ("Simple123", True, "符合要求：大小写字母+数字"),
    ]
    
    passed = 0
    total = len(test_passwords)
    
    for password, should_pass, description in test_passwords:
        try:
            validator.validate(password)
            result = True
            error_msg = "通过验证"
        except Exception as e:
            result = False
            error_msg = str(e)
        
        status = "✓" if result == should_pass else "✗"
        print(f"{status} {password:<15} | {description:<30} | {error_msg}")
        
        if result == should_pass:
            passed += 1
    
    print(f"\n后端验证测试结果: {passed}/{total} 通过")
    return passed == total

def test_api_registration():
    """测试API注册功能"""
    print("\n=== 测试API注册功能 ===")
    
    # 清理测试用户
    test_email = "test_no_special@example.com"
    try:
        User.objects.filter(email=test_email).delete()
    except:
        pass
    
    # 测试不符合要求的密码
    print("测试不符合要求的密码...")
    response = requests.post('http://localhost:8000/api/auth/register/', {
        'email': test_email,
        'password': 'simple123',  # 缺少大写字母
        'confirm_password': 'simple123'
    })
    
    if response.status_code != 201:
        print(f"✓ 正确拒绝了不符合要求的密码: {response.json()}")
    else:
        print("✗ 错误：接受了不符合要求的密码")
        return False
    
    # 测试符合要求的密码（无特殊字符）
    print("测试符合要求的密码（无特殊字符）...")
    response = requests.post('http://localhost:8000/api/auth/register/', {
        'email': test_email,
        'password': 'TestPassword123',  # 符合新要求：大小写字母+数字
        'confirm_password': 'TestPassword123'
    })
    
    if response.status_code == 201:
        print("✓ 成功接受了符合要求的密码（无特殊字符）")
        # 清理测试用户
        try:
            User.objects.filter(email=test_email).delete()
            print("✓ 测试用户已清理")
        except Exception as e:
            print(f"清理测试用户时出错: {e}")
        return True
    else:
        print(f"✗ 错误：拒绝了符合要求的密码: {response.json()}")
        return False

def main():
    print("开始测试修改后的密码复杂度验证功能...")
    print("新要求：至少8个字符，包含大写字母、小写字母和数字（不需要特殊字符）\n")
    
    backend_ok = test_backend_password_validation()
    api_ok = test_api_registration()
    
    print(f"\n=== 测试总结 ===")
    print(f"后端验证器: {'✓ 通过' if backend_ok else '✗ 失败'}")
    print(f"API注册功能: {'✓ 通过' if api_ok else '✗ 失败'}")
    
    if backend_ok and api_ok:
        print("\n🎉 所有测试通过！密码复杂度要求已成功修改为不包含特殊字符。")
    else:
        print("\n❌ 部分测试失败，请检查配置。")

if __name__ == "__main__":
    main()