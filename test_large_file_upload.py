#!/usr/bin/env python3
"""
大文件上传测试脚本
测试3GB文件上传功能
"""

import requests
import os
import tempfile
import time

# 配置
BASE_URL = 'http://localhost:8000'
LOGIN_URL = f'{BASE_URL}/api/auth/login/'
UPLOAD_URL = f'{BASE_URL}/api/files/upload/'

# 测试用户凭据
EMAIL = 'test@example.com'
PASSWORD = 'testpassword123'

def get_auth_token():
    """获取认证token"""
    print("正在获取认证token...")
    
    response = requests.post(LOGIN_URL, data={
        'email': EMAIL,
        'password': PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"✅ 认证成功，token: {token[:20]}...")
        return token
    else:
        print(f"❌ 认证失败: {response.status_code}")
        print(f"响应: {response.text}")
        return None

def create_test_file(size_mb=10):
    """创建测试文件"""
    print(f"正在创建 {size_mb}MB 测试文件...")
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.fa')
    
    # 写入FASTA格式的内容
    chunk_size = 1024 * 1024  # 1MB chunks
    content_pattern = ">sequence_header\nATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG\n" * 100
    
    bytes_written = 0
    target_bytes = size_mb * 1024 * 1024
    
    while bytes_written < target_bytes:
        remaining = target_bytes - bytes_written
        write_size = min(len(content_pattern.encode()), remaining)
        temp_file.write(content_pattern.encode()[:write_size])
        bytes_written += write_size
        
        # 显示进度
        if bytes_written % (10 * 1024 * 1024) == 0:  # 每10MB显示一次
            progress = (bytes_written / target_bytes) * 100
            print(f"创建进度: {progress:.1f}%")
    
    temp_file.close()
    print(f"✅ 测试文件创建完成: {temp_file.name}")
    print(f"文件大小: {os.path.getsize(temp_file.name) / (1024*1024):.2f} MB")
    
    return temp_file.name

def test_upload(token, file_path):
    """测试文件上传"""
    print("开始上传测试...")
    
    file_size = os.path.getsize(file_path)
    print(f"文件大小: {file_size / (1024*1024):.2f} MB")
    
    headers = {
        'Authorization': f'Token {token}'
    }
    
    # 准备上传数据
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
        data = {
            'title': 'Large File Test',
            'project': '大文件测试项目',
            'file_format': 'FASTA',
            'document_type': 'Dataset',
            'access_level': 'Internal',
            'upload_method': 'Python Test Script',  # 现在应该不会超过50字符限制
            'organism': 'Test Organism',
            'experiment_type': 'WGS',
            'tags': 'test,large-file,fasta',
            'description': '这是一个大文件上传测试'
        }
        
        print("正在上传文件...")
        start_time = time.time()
        
        try:
            response = requests.post(
                UPLOAD_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=300  # 5分钟超时
            )
            
            end_time = time.time()
            upload_time = end_time - start_time
            
            print(f"上传耗时: {upload_time:.2f} 秒")
            print(f"上传速度: {(file_size / (1024*1024)) / upload_time:.2f} MB/s")
            
            if response.status_code == 201:
                result = response.json()
                print("✅ 上传成功!")
                print(f"文件ID: {result.get('id')}")
                print(f"文件名: {result.get('original_filename')}")
                print(f"文件大小: {result.get('file_size')} bytes")
                return True
            else:
                print(f"❌ 上传失败: {response.status_code}")
                print(f"响应: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ 上传超时")
            return False
        except Exception as e:
            print(f"❌ 上传异常: {e}")
            return False

def main():
    """主函数"""
    print("=== 大文件上传测试 ===")
    
    # 获取认证token
    token = get_auth_token()
    if not token:
        return
    
    # 创建测试文件 (先用较小的文件测试，比如100MB)
    test_file_size = 100  # MB
    print(f"\n创建 {test_file_size}MB 测试文件...")
    test_file = create_test_file(test_file_size)
    
    try:
        # 测试上传
        print(f"\n开始上传测试...")
        success = test_upload(token, test_file)
        
        if success:
            print("\n🎉 大文件上传测试成功!")
            print("现在可以尝试上传真正的3GB文件了。")
        else:
            print("\n❌ 大文件上传测试失败")
            
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.unlink(test_file)
            print(f"已清理测试文件: {test_file}")

if __name__ == '__main__':
    main()