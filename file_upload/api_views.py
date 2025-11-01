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
from .models import File, Folder
from .serializers import FileSerializer, FileUploadSerializer, FolderSerializer, FolderCreateSerializer
import os
import mimetypes


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def file_list(request):
    """获取当前用户的文件列表，支持按文件夹过滤"""
    folder_id = request.GET.get('folder_id')
    
    # 获取文件夹信息
    current_folder = None
    if folder_id:
        try:
            current_folder = Folder.objects.get(id=folder_id, user=request.user)
        except Folder.DoesNotExist:
            return Response({'error': '文件夹不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    # 获取当前文件夹下的子文件夹
    if current_folder:
        folders = Folder.objects.filter(user=request.user, parent=current_folder).order_by('name')
        files = File.objects.filter(user=request.user, parent_folder=current_folder).order_by('-uploaded_at')
    else:
        # 根目录：获取没有父文件夹的文件夹和文件
        folders = Folder.objects.filter(user=request.user, parent=None).order_by('name')
        files = File.objects.filter(user=request.user, parent_folder=None).order_by('-uploaded_at')
    
    folder_serializer = FolderSerializer(folders, many=True, context={'request': request})
    file_serializer = FileSerializer(files, many=True, context={'request': request})
    
    return Response({
        'current_folder': FolderSerializer(current_folder, context={'request': request}).data if current_folder else None,
        'folders': folder_serializer.data,
        'files': file_serializer.data
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def file_upload(request):
    """文件上传"""
    import logging
    logger = logging.getLogger(__name__)
    
    # 记录请求数据
    logger.error(f"Upload request data: {dict(request.data)}")
    logger.error(f"Upload request files: {dict(request.FILES)}")
    logger.error(f"Upload request user: {request.user}")
    
    serializer = FileUploadSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        file_obj = serializer.save()
        response_serializer = FileSerializer(file_obj, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    # 记录详细的验证错误
    logger.error(f"Serializer validation errors: {serializer.errors}")
    
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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # 获取文件对象
        try:
            file_obj = File.objects.get(id=file_id, user=request.user)
        except File.DoesNotExist:
            logger.warning(f"File not found: id={file_id}, user={request.user.id}")
            raise Http404("File not found")

        # 验证文件是否存在
        if not file_obj.file:
            logger.error(f"File object has no file: id={file_id}")
            raise Http404("File not found")
            
        file_path = file_obj.file.path
        if not os.path.exists(file_path):
            logger.error(f"Physical file not found: path={file_path}, id={file_id}")
            raise Http404("File not found")

        # 验证文件可读性
        try:
            with open(file_path, 'rb') as test_file:
                test_file.read(1)  # 尝试读取1字节
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Cannot read file: path={file_path}, error={str(e)}")
            raise Http404("File not accessible")

        file_name = file_obj.original_filename or os.path.basename(file_path)
        
        # 安全的文件名处理
        import urllib.parse
        safe_filename = urllib.parse.quote(file_name.encode('utf-8'))

        # MIME类型
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'

        try:
            file_size = os.path.getsize(file_path)
        except OSError as e:
            logger.error(f"Cannot get file size: path={file_path}, error={str(e)}")
            raise Http404("File not accessible")

        range_header = request.headers.get('Range') or request.META.get('HTTP_RANGE')
        
        logger.info(f"Download request: file_id={file_id}, user={request.user.id}, "
                   f"size={file_size}, range={range_header}")

        if range_header:
            # 解析 Range: bytes=start-end
            try:
                units, rng = range_header.split('=')
                if units.strip() != 'bytes':
                    raise ValueError('Invalid units')
                start_str, end_str = rng.split('-')
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1
                
                # 验证范围
                if start < 0 or end >= file_size or start > end:
                    logger.warning(f"Invalid range: start={start}, end={end}, size={file_size}")
                    start = 0
                    end = file_size - 1
            except Exception as e:
                logger.warning(f"Range parsing error: {str(e)}")
                start = 0
                end = file_size - 1

            length = end - start + 1

            def file_iterator(path, offset, length, chunk_size=8192):
                try:
                    with open(path, 'rb') as f:
                        f.seek(offset)
                        remaining = length
                        while remaining > 0:
                            chunk_to_read = min(chunk_size, remaining)
                            chunk = f.read(chunk_to_read)
                            if not chunk:
                                logger.warning(f"Unexpected EOF: path={path}, offset={offset}, remaining={remaining}")
                                break
                            remaining -= len(chunk)
                            yield chunk
                except (IOError, OSError) as e:
                    logger.error(f"Error reading file during streaming: path={path}, error={str(e)}")
                    raise

            response = StreamingHttpResponse(
                file_iterator(file_path, start, length), content_type=content_type, status=206
            )
            response['Content-Length'] = str(length)
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response['Accept-Ranges'] = 'bytes'
            response['Content-Disposition'] = f'attachment; filename="{file_name}"; filename*=UTF-8\'\'{safe_filename}'
            
            logger.info(f"Partial download started: file_id={file_id}, range={start}-{end}")
            return response
        else:
            # 全量下载，流式传输
            try:
                file_handle = open(file_path, 'rb')
                response = FileResponse(file_handle, content_type=content_type)
                response['Content-Length'] = str(file_size)
                response['Accept-Ranges'] = 'bytes'
                response['Content-Disposition'] = f'attachment; filename="{file_name}"; filename*=UTF-8\'\'{safe_filename}'
                
                logger.info(f"Full download started: file_id={file_id}, size={file_size}")
                return response
            except (IOError, OSError) as e:
                logger.error(f"Error opening file for download: path={file_path}, error={str(e)}")
                raise Http404("File not accessible")
            
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in file download: file_id={file_id}, error={str(e)}")
        raise Http404("Download failed")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """获取用户文件统计信息"""
    user_files = File.objects.filter(user=request.user)
    user_folders = Folder.objects.filter(user=request.user)
    total_files = user_files.count()
    total_folders = user_folders.count()
    total_size = sum(f.file_size for f in user_files)
    
    return Response({
        'total_files': total_files,
        'total_folders': total_folders,
        'total_size': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2) if total_size > 0 else 0
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def folder_list_create(request):
    """获取文件夹列表或创建新文件夹"""
    if request.method == 'GET':
        parent_id = request.GET.get('parent_id')
        
        if parent_id:
            try:
                parent_folder = Folder.objects.get(id=parent_id, user=request.user)
                folders = Folder.objects.filter(user=request.user, parent=parent_folder).order_by('name')
            except Folder.DoesNotExist:
                return Response({'error': '父文件夹不存在'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # 获取根目录下的文件夹
            folders = Folder.objects.filter(user=request.user, parent=None).order_by('name')
        
        serializer = FolderSerializer(folders, many=True, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = FolderCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # 验证父文件夹权限
            parent_folder = serializer.validated_data.get('parent')
            if parent_folder and parent_folder.user != request.user:
                return Response({'error': '无权限在此文件夹下创建子文件夹'}, status=status.HTTP_403_FORBIDDEN)
            
            folder = serializer.save()
            response_serializer = FolderSerializer(folder, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def folder_detail(request, folder_id):
    """获取、更新或删除文件夹"""
    try:
        folder = Folder.objects.get(id=folder_id, user=request.user)
    except Folder.DoesNotExist:
        return Response({'error': '文件夹不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = FolderSerializer(folder, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = FolderCreateSerializer(folder, data=request.data, context={'request': request})
        if serializer.is_valid():
            # 验证父文件夹权限
            parent_folder = serializer.validated_data.get('parent')
            if parent_folder and parent_folder.user != request.user:
                return Response({'error': '无权限移动到此文件夹'}, status=status.HTTP_403_FORBIDDEN)
            
            folder = serializer.save()
            response_serializer = FolderSerializer(folder, context={'request': request})
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # 检查文件夹是否为空
        if folder.subfolders.exists() or folder.files.exists():
            return Response({'error': '文件夹不为空，无法删除'}, status=status.HTTP_400_BAD_REQUEST)
        
        folder.delete()
        return Response({'message': '文件夹删除成功'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def folder_breadcrumb(request, folder_id):
    """获取文件夹的面包屑导航路径"""
    try:
        folder = Folder.objects.get(id=folder_id, user=request.user)
    except Folder.DoesNotExist:
        return Response({'error': '文件夹不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    breadcrumb = []
    current = folder
    while current:
        breadcrumb.insert(0, {
            'id': current.id,
            'name': current.name,
            'path': current.get_path()
        })
        current = current.parent
    
    return Response(breadcrumb)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def folder_all(request):
    """获取当前用户的所有文件夹"""
    folders = Folder.objects.filter(user=request.user).order_by('name')
    folder_serializer = FolderSerializer(folders, many=True, context={'request': request})
    
    return Response({
        'folders': folder_serializer.data
    })