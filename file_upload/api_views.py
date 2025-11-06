import os
import mimetypes
import shutil
import re
import logging
import signal
import subprocess
import textwrap
import time
import requests
from pathlib import Path

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, parser_classes, authentication_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.http import Http404, StreamingHttpResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from django.core.files import File as DjangoFile

from .models import File, Folder
from .serializers import FileSerializer, FileUploadSerializer, FolderSerializer, FolderCreateSerializer
from .ncbi_client import (
    NCBIDownloadError,
    NCBIDownloadResult,
    NCBIDownloadTooLarge,
    download_ncbi_resource,
)

logger = logging.getLogger(__name__)


def _resolve_cellxgene_command():
    """根据配置或 PATH 查找 cellxgene 可执行文件"""
    configured = getattr(settings, 'CELLXGENE_CMD', None)
    candidates = []
    if configured:
        if os.path.isabs(configured) and os.path.exists(configured):
            return configured
        candidates.append(configured)
    candidates.append('cellxgene')

    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _stop_existing_cellxgene(pid_path: Path):
    if not pid_path.exists():
        return
    try:
        pid = int(pid_path.read_text().strip())
    except (ValueError, OSError):
        pid_path.unlink(missing_ok=True)
        return

    if not _is_pid_running(pid):
        pid_path.unlink(missing_ok=True)
        return

    logger.info(f"Stopping existing Cellxgene process pid={pid}")
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pid_path.unlink(missing_ok=True)
        return

    for _ in range(20):
        if not _is_pid_running(pid):
            break
        time.sleep(0.25)
    else:
        logger.warning("Cellxgene process did not terminate after SIGTERM, sending SIGKILL")
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    pid_path.unlink(missing_ok=True)


def prepare_h5ad_for_cellxgene(dataset_path: str):
    """确保 .h5ad 文件包含 Cellxgene 需要的二维布局"""
    python_bin = getattr(
        settings,
        'CELLXGENE_PYTHON',
        os.path.join(os.path.dirname(getattr(settings, 'CELLXGENE_CMD', 'cellxgene')), 'python'),
    )
    if not python_bin or not os.path.exists(python_bin):
        return {
            'status': 'skipped',
            'message': '未找到 Cellxgene Python 解释器，跳过布局生成'
        }

    script = textwrap.dedent(f"""
        import sys
        import numpy as np
        from pathlib import Path
        import anndata as ad
        try:
            from sklearn.decomposition import TruncatedSVD
        except Exception as exc:
            print(f"Failed to import TruncatedSVD: {{exc}}", file=sys.stderr)
            raise

        path = Path(r\"{dataset_path}\")
        adata = ad.read_h5ad(path)
        needs_layout = "X_umap" not in adata.obsm or adata.obsm["X_umap"].shape[1] < 2
        if not needs_layout:
            sys.exit(0)

        matrix = adata.X
        if hasattr(matrix, "tocsr"):
            matrix = matrix.tocsr()
        svd = TruncatedSVD(n_components=2, random_state=0)
        coords = svd.fit_transform(matrix)
        adata.obsm["X_umap"] = coords.astype("float32")
        adata.uns["umap"] = {{"params": {{"method": "TruncatedSVD", "n_components": 2}}}}
        adata.uns["default_embedding"] = "umap"
        adata.write(path)
    """)

    env = os.environ.copy()
    env.setdefault('PYTHONUNBUFFERED', '1')

    try:
        result = subprocess.run(
            [python_bin, '-c', script],
            capture_output=True,
            text=True,
            cwd=settings.BASE_DIR,
            env=env,
            check=False,
        )
    except OSError as exc:
        logger.error("Failed to invoke Cellxgene python for layout generation: %s", exc)
        return {'status': 'error', 'message': f'无法生成布局：{exc}'}

    if result.returncode != 0:
        logger.error(
            "Cellxgene layout script failed (code=%s): stdout=%s stderr=%s",
            result.returncode,
            result.stdout.strip(),
            result.stderr.strip(),
        )
        return {
            'status': 'error',
            'message': result.stderr.strip() or 'Cellxgene 布局生成失败'
        }

    if result.stdout:
        logger.info("Cellxgene layout script output: %s", result.stdout.strip())
    return {'status': 'prepared', 'message': '已生成默认二维布局'}


def _kill_processes_on_port(port: int):
    try:
        result = subprocess.run(
            ['lsof', '-t', f'-iTCP:{port}', '-sTCP:LISTEN'],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return

    if result.returncode != 0 or not result.stdout:
        return

    for line in result.stdout.strip().splitlines():
        try:
            pid = int(line.strip())
        except ValueError:
            continue
        if _is_pid_running(pid):
            logger.warning("Killing process %s occupying port %s", pid, port)
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                continue
            # give it a moment
            for _ in range(10):
                if not _is_pid_running(pid):
                    break
                time.sleep(0.1)
            if _is_pid_running(pid):
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass


def restart_cellxgene_process(dataset_path: str):
    """尝试使用新的数据集重新启动 Cellxgene 服务"""
    if not getattr(settings, 'CELLXGENE_AUTO_RESTART', True):
        return {'status': 'skipped', 'message': 'Cellxgene 自动重启已关闭，请手动启动服务'}

    command = _resolve_cellxgene_command()
    if not command:
        return {'status': 'error', 'message': '未找到 cellxgene 命令，请安装或在 CELLXGENE_CMD 中配置路径'}

    log_path = Path(getattr(settings, 'CELLXGENE_LOG_FILE', os.path.join(settings.BASE_DIR, 'logs', 'cellxgene.log')))
    pid_path = Path(getattr(settings, 'CELLXGENE_PID_FILE', os.path.join(settings.BASE_DIR, '.pids', 'cellxgene.pid')))
    host = getattr(settings, 'CELLXGENE_HOST', '0.0.0.0')
    port = str(getattr(settings, 'CELLXGENE_PORT', 5005))

    log_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.parent.mkdir(parents=True, exist_ok=True)

    _stop_existing_cellxgene(pid_path)
    try:
        _kill_processes_on_port(int(port))
    except ValueError:
        pass

    env = os.environ.copy()
    env.setdefault('PYTHONUNBUFFERED', '1')

    try:
        with open(log_path, 'a', buffering=1) as log_file:
            proc = subprocess.Popen(
                [command, 'launch', dataset_path, '--host', host, '--port', port],
                stdout=log_file,
                stderr=log_file,
                cwd=settings.BASE_DIR,
                env=env,
            )
    except OSError as exc:
        logger.error("Failed to start Cellxgene: %s", exc)
        return {'status': 'error', 'message': f'无法启动 Cellxgene：{exc}'}

    pid_path.write_text(str(proc.pid))
    logger.info("Cellxgene restarted with dataset %s (pid=%s)", dataset_path, proc.pid)
    return {'status': 'started', 'message': 'Cellxgene 已重新加载数据，请稍候页面刷新', 'pid': proc.pid}


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ncbi_import(request):
    """从 NCBI 链接下载文件并保存到当前用户空间。"""
    url = request.data.get('url')
    parent_folder_id = request.data.get('parent_folder')
    project = request.data.get('project') or 'NCBI Import'
    access_level = request.data.get('access_level') or 'Internal'

    if not url:
        return Response({'message': '请提供 NCBI 链接'}, status=status.HTTP_400_BAD_REQUEST)

    parent_folder = None
    if parent_folder_id is not None:
        try:
            parent_folder = Folder.objects.get(id=parent_folder_id, user=request.user)
        except Folder.DoesNotExist:
            return Response({'message': '指定的文件夹不存在或无权限访问'}, status=status.HTTP_404_NOT_FOUND)

    try:
        download_result: NCBIDownloadResult = download_ncbi_resource(url)
    except NCBIDownloadTooLarge as exc:
        return Response({'message': str(exc)}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    except NCBIDownloadError as exc:
        return Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except requests.RequestException as exc:
        logger.exception("NCBI request failed: %s", exc)
        return Response({'message': f'无法连接 NCBI 服务：{exc}'}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as exc:
        logger.exception("Unexpected NCBI import failure: %s", exc)
        return Response({'message': f'下载失败：{exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    file_obj = None
    try:
        with open(download_result.file_path, 'rb') as handle:
            django_file = DjangoFile(handle, name=download_result.filename)

            raw_tags = request.data.get('tags')
            user_tags = []
            if isinstance(raw_tags, list):
                user_tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()]
            elif isinstance(raw_tags, str):
                user_tags = [tag.strip() for tag in raw_tags.split(',') if tag.strip()]
            base_tags = ['NCBI', download_result.db.upper()]
            combined_tags = []
            for tag in base_tags + user_tags:
                if tag and tag not in combined_tags:
                    combined_tags.append(tag)
            tag_string = ','.join(combined_tags)

            metadata = download_result.metadata or {}
            description = metadata.get('title') or metadata.get('extra') or ''
            if metadata.get('summary'):
                description = f"{description}\n{metadata['summary']}".strip()

            file_obj = File.objects.create(
                user=request.user,
                file=django_file,
                upload_method='NCBI Import',
                parent_folder=parent_folder,
                title=metadata.get('title') or download_result.filename,
                project=project,
                original_filename=download_result.filename,
                file_format=download_result.file_format,
                document_type=download_result.document_type,
                access_level=access_level,
                organism=metadata.get('organism') or '',
                experiment_type=metadata.get('experiment_type') or '',
                tags=tag_string,
                description=description,
            )
            file_obj.extracted_metadata = metadata
            file_obj.save()
    finally:
        if os.path.exists(download_result.file_path):
            os.remove(download_result.file_path)

    serializer = FileSerializer(file_obj, context={'request': request})
    return Response({'file': serializer.data, 'metadata': download_result.metadata}, status=status.HTTP_201_CREATED)


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def publish_cellxgene(request, file_id):
    """将指定文件发布到 Cellxgene 数据目录以便预览

    要求：文件为 .h5ad 格式；将物理文件复制到 settings.CELLXGENE_DATA_DIR 下，
    避免破坏用户原始文件结构。返回发布后的目标文件名及目录。
    """
    try:
        # 获取文件对象（仅限当前用户）
        try:
            file_obj = File.objects.get(id=file_id, user=request.user)
        except File.DoesNotExist:
            return Response({'message': '文件不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 验证物理文件存在
        if not file_obj.file or not os.path.exists(file_obj.file.path):
            return Response({'message': '物理文件不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 校验扩展名为 .h5ad
        original = file_obj.original_filename or os.path.basename(file_obj.file.name)
        if not str(original).lower().endswith('.h5ad'):
            return Response({'message': '仅支持 .h5ad 文件发布到 Cellxgene'}, status=status.HTTP_400_BAD_REQUEST)

        # 目标目录（可通过环境变量 CELLXGENE_DATA_DIR 配置）
        from django.conf import settings
        target_dir = getattr(settings, 'CELLXGENE_DATA_DIR', os.path.join(settings.BASE_DIR, 'cellxgene_data'))
        os.makedirs(target_dir, exist_ok=True)

        # 安全文件名：避免特殊字符与路径穿越
        safe_basename = re.sub(r'[^A-Za-z0-9\._-]', '_', os.path.basename(original))
        target_filename = f"{file_obj.id}__{safe_basename}"
        target_path = os.path.join(target_dir, target_filename)

        try:
            shutil.copy2(file_obj.file.path, target_path)
        except Exception as e:
            return Response({'message': f'复制文件失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        prepare_info = prepare_h5ad_for_cellxgene(target_path)
        if prepare_info.get('status') == 'error':
            message = f"已复制到 Cellxgene 数据目录，但无法生成可视化布局：{prepare_info.get('message')}"
            logger.error("Cellxgene layout preparation failed for %s: %s", target_filename, prepare_info)
            return Response(
                {
                    'message': message,
                    'published_file': target_filename,
                    'target_dir': target_dir,
                    'cellxgene': {'status': 'error', 'message': prepare_info.get('message')},
                    'layout': prepare_info,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        restart_info = restart_cellxgene_process(target_path)
        message = '已发布到 Cellxgene 数据目录'

        status_text = restart_info.get('status')
        if status_text == 'started':
            message += '，Cellxgene 正在重新加载该文件，请稍候片刻。'
        elif status_text == 'skipped':
            message += '。自动重启已关闭，请手动启动 Cellxgene 服务。'
        elif status_text == 'error':
            detail = restart_info.get('message') or 'Cellxgene 启动失败'
            message += f'，但无法自动启动 Cellxgene：{detail}'
            logger.error("Cellxgene restart failed for file %s: %s", target_filename, detail)

        response_payload = {
            'message': message,
            'published_file': target_filename,
            'target_dir': target_dir,
            'layout': prepare_info,
            'cellxgene': restart_info,
            'cellxgene_port': getattr(settings, 'CELLXGENE_PORT', 5005),
        }
        return Response(response_payload, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'message': f'发布过程中发生错误: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
