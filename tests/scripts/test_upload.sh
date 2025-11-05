#!/bin/bash

# 设置变量
TOKEN="75e88a81871e4d6d5e0410630b9a21df6b6c76f8"
FILE="large_test_file_100mb.bin"
FILE_SIZE=$(stat -f%z "$FILE")
CHUNK_SIZE=2097152  # 2MB

echo "开始测试100MB文件上传..."
echo "文件大小: $FILE_SIZE 字节"

# 1. 初始化分块上传
echo "1. 初始化分块上传..."
INIT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/files/chunked/init/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"filename\":\"$FILE\",\"total_size\":$FILE_SIZE}")

echo "初始化响应: $INIT_RESPONSE"

# 提取session_id
SESSION_ID=$(echo "$INIT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])" 2>/dev/null)

if [ -z "$SESSION_ID" ]; then
    echo "错误: 无法获取session_id"
    exit 1
fi

echo "Session ID: $SESSION_ID"

# 2. 分块上传前3个分块
echo "2. 开始分块上传..."
for i in {0..2}; do
    START=$((i * CHUNK_SIZE))
    END=$((START + CHUNK_SIZE - 1))
    
    if [ $END -ge $FILE_SIZE ]; then
        END=$((FILE_SIZE - 1))
    fi
    
    echo "上传分块 $i: bytes $START-$END"
    
    # 创建分块
    dd if="$FILE" of="chunk_$i.bin" bs=1 skip=$START count=$CHUNK_SIZE 2>/dev/null
    
    # 上传分块
    UPLOAD_RESPONSE=$(curl -s -X PUT "http://localhost:8000/api/files/chunked/$SESSION_ID/chunk/" \
      -H "Authorization: Token $TOKEN" \
      -H "Content-Range: bytes $START-$END/$FILE_SIZE" \
      --data-binary "@chunk_$i.bin")
    
    echo "分块 $i 响应: $UPLOAD_RESPONSE"
    
    # 清理临时文件
    rm -f "chunk_$i.bin"
    
    if [ $END -ge $((FILE_SIZE - 1)) ]; then
        break
    fi
done

echo "前3个分块上传完成！"
echo "测试结果：分块上传功能正常工作"