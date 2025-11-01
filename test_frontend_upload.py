#!/usr/bin/env python3
"""
简化的前端上传测试脚本
模拟前端发送的上传请求
"""

import requests
import json
import os

# 配置
BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"
UPLOAD_URL = f"{BASE_URL}/api/files/upload/"

# 测试用户凭据
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword123"
}

def get_auth_token():
    """获取认证token"""
    print("正在获取认证token...")
    response = requests.post(LOGIN_URL, data=TEST_USER)
    if response.status_code == 200:
        token = response.json().get('token')
        print(f"获取token成功: {token[:20]}...")
        return token
    else:
        print(f"获取token失败: {response.status_code} - {response.text}")
        return None

def test_upload_with_empty_metadata(token):
    """测试空元数据上传"""
    print("\n=== 测试空元数据上传 ===")
    
    # 创建测试文件
    test_file_path = "test_upload_debug.txt"
    if not os.path.exists(test_file_path):
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write("这是一个测试文件\n用于测试空元数据上传")
    
    headers = {
        'Authorization': f'Token {token}'
    }
    
    # 模拟前端发送的数据（空元数据）
    data = {
        'title': '',
        'project': '',
        'file_format': '',
        'document_type': '',
        'access_level': '',
        'upload_method': 'Frontend Test Empty'
    }
    
    files = {
        'file': open(test_file_path, 'rb')
    }
    
    try:
        print(f"发送请求到: {UPLOAD_URL}")
        print(f"请求数据: {data}")
        
        response = requests.post(UPLOAD_URL, headers=headers, data=data, files=files)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ 空元数据上传成功!")
            print(f"文件ID: {result.get('id')}")
            print(f"文件名: {result.get('name')}")
            print(f"文件格式: {result.get('file_format')}")
            print(f"文档类型: {result.get('document_type')}")
            print(f"访问级别: {result.get('access_level')}")
        else:
            print("❌ 空元数据上传失败")
            try:
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误内容: {response.text}")
                
    except Exception as e:
        print(f"请求异常: {e}")
    finally:
        files['file'].close()

def test_upload_with_minimal_metadata(token):
    """测试最小元数据上传"""
    print("\n=== 测试最小元数据上传 ===")
    
    test_file_path = "test_upload_debug.txt"
    
    headers = {
        'Authorization': f'Token {token}'
    }
    
    # 模拟前端发送的数据（最小元数据）
    data = {
        'title': 'Test File',
        'project': 'Test Project',
        'file_format': 'txt',
        'document_type': 'data',
        'access_level': 'public',
        'upload_method': 'Frontend Test Minimal'
    }
    
    files = {
        'file': open(test_file_path, 'rb')
    }
    
    try:
        print(f"发送请求到: {UPLOAD_URL}")
        print(f"请求数据: {data}")
        
        response = requests.post(UPLOAD_URL, headers=headers, data=data, files=files)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ 最小元数据上传成功!")
            print(f"文件ID: {result.get('id')}")
            print(f"文件名: {result.get('name')}")
        else:
            print("❌ 最小元数据上传失败")
            try:
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误内容: {response.text}")
                
    except Exception as e:
        print(f"请求异常: {e}")
    finally:
        files['file'].close()

def main():
    print("开始前端上传测试...")
    
    # 获取认证token
    token = get_auth_token()
    if not token:
        print("无法获取认证token，测试终止")
        return
    
    # 测试空元数据上传
    test_upload_with_empty_metadata(token)
    
    # 测试最小元数据上传
    test_upload_with_minimal_metadata(token)
    
    print("\n测试完成!")

if __name__ == "__main__":
    main()