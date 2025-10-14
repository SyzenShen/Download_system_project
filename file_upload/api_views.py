from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import Http404, StreamingHttpResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import File
from .serializers import FileSerializer, FileUploadSerializer
import os
import mimetypes


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def file_list(request):
    """获取当前用户的文件列表"""
    files = File.objects.filter(user=request.user).order_by('-uploaded_at')
    serializer = FileSerializer(files, many=True, context={'request': request})
    return Response(serializer.data)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def file_upload(request):
    """文件上传"""
    serializer = FileUploadSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        file_obj = serializer.save()
        response_serializer = FileSerializer(file_obj, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    # 统一错误消息格式，便于前端展示
    errors = serializer.errors
    message = None
    if isinstance(errors, dict):
        # 优先返回 file 字段的错误
        file_errors = errors.get('file')
        if isinstance(file_errors, list) and file_errors:
            message = str(file_errors[0])
    if not message:
        message = '文件上传失败'
    return Response({'message': message, 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def file_delete(request, file_id):
    """删除文件"""
    try:
        file_obj = File.objects.get(id=file_id, user=request.user)
        # 删除物理文件
        if file_obj.file and os.path.exists(file_obj.file.path):
            os.remove(file_obj.file.path)
        file_obj.delete()
        return Response({'message': 'File deleted successfully'}, status=status.HTTP_200_OK)
    except File.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def file_download(request, file_id):
    """文件下载"""
    try:
        file_obj = File.objects.get(id=file_id, user=request.user)
        if not file_obj.file or not os.path.exists(file_obj.file.path):
            raise Http404("File not found")

        file_path = file_obj.file.path
        file_name = file_obj.original_filename or os.path.basename(file_path)

        # MIME类型
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'

        file_size = os.path.getsize(file_path)
        range_header = request.headers.get('Range') or request.META.get('HTTP_RANGE')

        if range_header:
            # 解析 Range: bytes=start-end
            try:
                units, rng = range_header.split('=')
                if units.strip() != 'bytes':
                    raise ValueError('Invalid units')
                start_str, end_str = rng.split('-')
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1
                if start > end or end >= file_size:
                    start = 0
                    end = file_size - 1
            except Exception:
                start = 0
                end = file_size - 1

            length = end - start + 1

            def file_iterator(path, offset, length, chunk_size=8192):
                with open(path, 'rb') as f:
                    f.seek(offset)
                    remaining = length
                    while remaining > 0:
                        chunk = f.read(min(chunk_size, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            response = StreamingHttpResponse(
                file_iterator(file_path, start, length), content_type=content_type, status=206
            )
            response['Content-Length'] = str(length)
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response['Accept-Ranges'] = 'bytes'
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
        else:
            # 全量下载，流式传输
            response = FileResponse(open(file_path, 'rb'), content_type=content_type)
            response['Content-Length'] = str(file_size)
            response['Accept-Ranges'] = 'bytes'
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
            
    except File.DoesNotExist:
        raise Http404("File not found")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """获取用户文件统计信息"""
    user_files = File.objects.filter(user=request.user)
    total_files = user_files.count()
    total_size = sum(f.file_size for f in user_files)
    
    return Response({
        'total_files': total_files,
        'total_size': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2) if total_size > 0 else 0
    })