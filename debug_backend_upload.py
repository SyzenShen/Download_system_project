#!/usr/bin/env python3
"""
后端上传调试脚本
"""
import os
import sys
import django
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'file_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from file_upload.serializers import FileUploadSerializer
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

def test_serializer():
    print("=== 测试FileUploadSerializer ===")
    
    # 获取测试用户
    try:
        user = User.objects.get(email='test@example.com')
        print(f"使用用户: {user.username}")
    except User.DoesNotExist:
        print("错误: 未找到测试用户")
        return
    
    # 创建测试文件
    test_content = b"This is a test file for backend debugging"
    test_file = SimpleUploadedFile(
        "backend_test.txt",
        test_content,
        content_type="text/plain"
    )
    
    # 测试数据
    test_data = {
        'title': '后端调试测试文件',
        'project': '调试项目',
        'file_format': 'txt',
        'document_type': 'Dataset',
        'access_level': 'Internal',
        'upload_method': 'Backend Debug Script'
    }
    
    print(f"测试数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    # 测试序列化器
    serializer = FileUploadSerializer(data=test_data)
    
    print("\n=== 验证结果 ===")
    if serializer.is_valid():
        print("✅ 序列化器验证通过")
        print(f"验证后的数据: {json.dumps(serializer.validated_data, indent=2, ensure_ascii=False)}")
        
        # 尝试保存
        try:
            # 手动设置文件和用户
            instance = serializer.save(file=test_file, uploader=user)
            print(f"✅ 保存成功! 文件ID: {instance.id}")
        except Exception as e:
            print(f"❌ 保存失败: {e}")
    else:
        print("❌ 序列化器验证失败")
        print(f"错误详情: {json.dumps(serializer.errors, indent=2, ensure_ascii=False)}")
    
    # 测试空字符串情况
    print("\n=== 测试空字符串情况 ===")
    empty_data = {
        'title': '',
        'project': '',
        'file_format': '',
        'document_type': '',
        'access_level': '',
        'upload_method': 'Backend Debug Script'
    }
    
    print(f"空字符串数据: {json.dumps(empty_data, indent=2, ensure_ascii=False)}")
    
    empty_serializer = FileUploadSerializer(data=empty_data)
    if empty_serializer.is_valid():
        print("✅ 空字符串验证通过")
        print(f"验证后的数据: {json.dumps(empty_serializer.validated_data, indent=2, ensure_ascii=False)}")
    else:
        print("❌ 空字符串验证失败")
        print(f"错误详情: {json.dumps(empty_serializer.errors, indent=2, ensure_ascii=False)}")

def test_api_view():
    print("\n=== 测试API视图 ===")
    
    from django.test import RequestFactory
    from file_upload.api_views import file_upload
    from django.contrib.auth import get_user_model
    from rest_framework.authtoken.models import Token
    from rest_framework.test import force_authenticate
    
    User = get_user_model()
    
    # 获取测试用户和token
    try:
        user = User.objects.get(email='test@example.com')
        token, created = Token.objects.get_or_create(user=user)
        print(f"使用用户: {user.username}, Token: {token.key[:10]}...")
    except User.DoesNotExist:
        print("错误: 未找到测试用户")
        return
    
    # 创建请求工厂
    factory = RequestFactory()
    
    # 创建测试文件
    test_content = b"This is a test file for API view debugging"
    
    # 模拟POST请求
    request = factory.post('/api/files/upload/', {
        'title': 'API调试测试文件',
        'project': '调试项目',
        'file_format': 'txt',
        'document_type': 'Dataset',
        'access_level': 'Internal',
        'upload_method': 'API Debug Script',
        'file': SimpleUploadedFile("api_test.txt", test_content, content_type="text/plain")
    })
    
    # 设置用户认证和Token认证
    request.user = user
    request.META['HTTP_AUTHORIZATION'] = f'Token {token.key}'
    
    try:
        response = file_upload(request)
        print(f"API响应状态: {response.status_code}")
        # 渲染响应内容后再访问
        response.render()
        print(f"API响应内容: {response.content.decode('utf-8')}")
    except Exception as e:
        print(f"API调用错误: {e}")

if __name__ == '__main__':
    test_serializer()
    test_api_view()