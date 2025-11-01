#!/usr/bin/env python3
"""
调试文件上传问题的脚本
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
from rest_framework.authtoken.models import Token

User = get_user_model()

def test_upload():
    # 使用现有用户
    try:
        user = User.objects.get(email='test@example.com')
    except User.DoesNotExist:
        print("未找到测试用户，请先创建用户")
        return
    
    # 获取或创建token
    token, created = Token.objects.get_or_create(user=user)
    
    print(f"用户: {user.username}")
    print(f"Token: {token.key}")
    
    # 准备上传数据
    url = 'http://127.0.0.1:8000/api/files/upload/'
    headers = {
        'Authorization': f'Token {token.key}'
    }
    
    # 创建测试文件
    test_file_path = 'test_upload_debug.txt'
    with open(test_file_path, 'w') as f:
        f.write('这是一个调试上传的测试文件')
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_upload_debug.txt', f, 'text/plain')}
            data = {
                'title': '测试文件',
                'project': '测试项目',
                'file_format': 'txt',
                'document_type': 'Dataset',
                'access_level': 'Internal',
                'upload_method': 'Debug Script'
            }
            
            print("发送上传请求...")
            print(f"URL: {url}")
            print(f"Headers: {headers}")
            print(f"Data: {data}")
            
            response = requests.post(url, files=files, data=data, headers=headers)
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 201:
                print("✅ 上传成功!")
                result = response.json()
                print(f"文件ID: {result.get('id')}")
            else:
                print("❌ 上传失败!")
                try:
                    error_data = response.json()
                    print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"错误内容: {response.text}")
    
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == '__main__':
    test_upload()