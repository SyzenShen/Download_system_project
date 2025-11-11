#!/usr/bin/env python3
"""
Utility script for testing large (multi-GB) file uploads.
"""

import requests
import os
import tempfile
import time

# Configuration
BASE_URL = 'http://localhost:8000'
LOGIN_URL = f'{BASE_URL}/api/auth/login/'
UPLOAD_URL = f'{BASE_URL}/api/files/upload/'

# Test user credentials
EMAIL = 'test@example.com'
PASSWORD = 'testpassword123'

def get_auth_token():
    """Obtain an auth token"""
    print("Requesting auth token...")
    
    response = requests.post(LOGIN_URL, data={
        'email': EMAIL,
        'password': PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"✅ Auth success, token preview: {token[:20]}...")
        return token
    else:
        print(f"❌ Auth failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def create_test_file(size_mb=10):
    """Generate a temporary FASTA file for testing"""
    print(f"Creating a {size_mb} MB test file...")
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.fa')
    
    # Write pseudo FASTA records
    chunk_size = 1024 * 1024  # 1MB chunks
    content_pattern = ">sequence_header\nATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG\n" * 100
    
    bytes_written = 0
    target_bytes = size_mb * 1024 * 1024
    
    while bytes_written < target_bytes:
        remaining = target_bytes - bytes_written
        write_size = min(len(content_pattern.encode()), remaining)
        temp_file.write(content_pattern.encode()[:write_size])
        bytes_written += write_size
        
        # Show progress for every 10 MB
        if bytes_written % (10 * 1024 * 1024) == 0:
            progress = (bytes_written / target_bytes) * 100
            print(f"Creation progress: {progress:.1f}%")
    
    temp_file.close()
    print(f"✅ Test file ready: {temp_file.name}")
    print(f"Size: {os.path.getsize(temp_file.name) / (1024*1024):.2f} MB")
    
    return temp_file.name

def test_upload(token, file_path):
    """Upload the generated file"""
    print("Starting upload...")
    
    file_size = os.path.getsize(file_path)
    print(f"File size: {file_size / (1024*1024):.2f} MB")
    
    headers = {
        'Authorization': f'Token {token}'
    }
    
    # Prepare payload
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
        data = {
            'title': 'Large File Test',
            'project': 'Large File Validation',
            'file_format': 'FASTA',
            'document_type': 'Dataset',
            'access_level': 'Internal',
            'upload_method': 'Python Test Script',  # stays within 50-char limit
            'organism': 'Test Organism',
            'experiment_type': 'WGS',
            'tags': 'test,large-file,fasta',
            'description': 'Automated large-file upload validation'
        }
        
        print("Uploading file...")
        start_time = time.time()
        
        try:
            response = requests.post(
                UPLOAD_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=300  # 5 minute timeout
            )
            
            end_time = time.time()
            upload_time = end_time - start_time
            
            print(f"Elapsed: {upload_time:.2f} s")
            print(f"Throughput: {(file_size / (1024*1024)) / upload_time:.2f} MB/s")
            
            if response.status_code == 201:
                result = response.json()
                print("✅ Upload succeeded!")
                print(f"File ID: {result.get('id')}")
                print(f"Filename: {result.get('original_filename')}")
                print(f"Backend size: {result.get('file_size')} bytes")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Upload timed out")
            return False
        except Exception as e:
            print(f"❌ Upload exception: {e}")
            return False

def main():
    """Entry point"""
    print("=== Large File Upload Smoke Test ===")
    
    # Authenticate
    token = get_auth_token()
    if not token:
        return
    
    # Create a smaller test file (e.g., 100 MB) before jumping to 3 GB
    test_file_size = 100  # MB
    print(f"\nCreating {test_file_size} MB test file...")
    test_file = create_test_file(test_file_size)
    
    try:
        # Upload
        print(f"\nRunning upload test...")
        success = test_upload(token, test_file)
        
        if success:
            print("\n🎉 Large file upload test passed!")
            print("You can now attempt a full 3 GB upload.")
        else:
            print("\n❌ Large file upload test failed")
            
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.unlink(test_file)
            print(f"Cleaned up test file: {test_file}")

if __name__ == '__main__':
    main()
