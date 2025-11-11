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
    """Locate the cellxgene executable via settings or PATH"""
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
    """Ensure the .h5ad file contains the 2D layout Cellxgene expects"""
    python_bin = getattr(
        settings,
        'CELLXGENE_PYTHON',
        os.path.join(os.path.dirname(getattr(settings, 'CELLXGENE_CMD', 'cellxgene')), 'python'),
    )
    if not python_bin or not os.path.exists(python_bin):
        return {
            'status': 'skipped',
            'message': 'Cellxgene Python interpreter not found; skipping layout generation.'
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
        return {'status': 'error', 'message': f'Failed to generate layout: {exc}'}

    if result.returncode != 0:
        logger.error(
            "Cellxgene layout script failed (code=%s): stdout=%s stderr=%s",
            result.returncode,
            result.stdout.strip(),
            result.stderr.strip(),
        )
        return {
            'status': 'error',
            'message': result.stderr.strip() or 'Cellxgene layout generation failed'
        }

    if result.stdout:
        logger.info("Cellxgene layout script output: %s", result.stdout.strip())
    return {'status': 'prepared', 'message': 'Default 2D layout generated'}


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
    """Attempt to restart Cellxgene with a new dataset"""
    if not getattr(settings, 'CELLXGENE_AUTO_RESTART', True):
        return {'status': 'skipped', 'message': 'Cellxgene auto restart is disabled; start the service manually.'}

    command = _resolve_cellxgene_command()
    if not command:
        return {'status': 'error', 'message': 'cellxgene executable not found; install it or set CELLXGENE_CMD.'}

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
        return {'status': 'error', 'message': f'Unable to start Cellxgene: {exc}'}

    pid_path.write_text(str(proc.pid))
    logger.info("Cellxgene restarted with dataset %s (pid=%s)", dataset_path, proc.pid)
    return {'status': 'started', 'message': 'Cellxgene is reloading the dataset; refresh the page shortly.', 'pid': proc.pid}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def file_list(request):
    """Return the current user's files, optionally filtered by folder"""
    folder_id = request.GET.get('folder_id')
    
    # Resolve folder metadata if provided
    current_folder = None
    if folder_id:
        try:
            current_folder = Folder.objects.get(id=folder_id, user=request.user)
        except Folder.DoesNotExist:
            return Response({'error': 'Folder not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Fetch children for the active folder
    if current_folder:
        folders = Folder.objects.filter(user=request.user, parent=current_folder).order_by('name')
        files = File.objects.filter(user=request.user, parent_folder=current_folder).order_by('-uploaded_at')
    else:
        # Root level: only items without parents
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
    """Upload a file via multipart form data"""
    # Debug logging (intentionally noisy)
    logger.error(f"Upload request data: {dict(request.data)}")
    logger.error(f"Upload request files: {dict(request.FILES)}")
    logger.error(f"Upload request user: {request.user}")
    
    serializer = FileUploadSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        file_obj = serializer.save()
        response_serializer = FileSerializer(file_obj, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    # Dump detailed validation errors for debugging
    logger.error(f"Serializer validation errors: {serializer.errors}")
    
    # Normalize the response payload for the frontend
    errors = serializer.errors
    message = None
    if isinstance(errors, dict):
        # Prioritize feedback for the file field
        file_errors = errors.get('file')
        if isinstance(file_errors, list) and file_errors:
            message = str(file_errors[0])
    if not message:
        message = 'File upload failed'
    return Response({'message': message, 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ncbi_import(request):
    """Download an NCBI resource and store it for the authenticated user"""
    url = request.data.get('url')
    parent_folder_id = request.data.get('parent_folder')
    project = request.data.get('project') or 'NCBI Import'
    access_level = request.data.get('access_level') or 'Internal'

    if not url:
        return Response({'message': 'Provide a valid NCBI link'}, status=status.HTTP_400_BAD_REQUEST)

    parent_folder = None
    if parent_folder_id is not None:
        try:
            parent_folder = Folder.objects.get(id=parent_folder_id, user=request.user)
        except Folder.DoesNotExist:
            return Response({'message': 'Folder not found or not accessible'}, status=status.HTTP_404_NOT_FOUND)

    try:
        download_result: NCBIDownloadResult = download_ncbi_resource(url)
    except NCBIDownloadTooLarge as exc:
        return Response({'message': str(exc)}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    except NCBIDownloadError as exc:
        return Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except requests.RequestException as exc:
        logger.exception("NCBI request failed: %s", exc)
        return Response({'message': f'Unable to reach NCBI: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as exc:
        logger.exception("Unexpected NCBI import failure: %s", exc)
        return Response({'message': f'Download failed: {exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    """Delete a file owned by the current user"""
    try:
        file_obj = File.objects.get(id=file_id, user=request.user)
        # Remove the physical file if present
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
    """Download or partially download an existing file"""
    try:
        # Fetch the file record
        try:
            file_obj = File.objects.get(id=file_id, user=request.user)
        except File.DoesNotExist:
            logger.warning(f"File not found: id={file_id}, user={request.user.id}")
            raise Http404("File not found")

        # Validate the physical file
        if not file_obj.file:
            logger.error(f"File object has no file: id={file_id}")
            raise Http404("File not found")
            
        file_path = file_obj.file.path
        if not os.path.exists(file_path):
            logger.error(f"Physical file not found: path={file_path}, id={file_id}")
            raise Http404("File not found")

        # Ensure the file is readable
        try:
            with open(file_path, 'rb') as test_file:
                test_file.read(1)  # Probe one byte
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Cannot read file: path={file_path}, error={str(e)}")
            raise Http404("File not accessible")

        file_name = file_obj.original_filename or os.path.basename(file_path)
        
        # Produce a safe filename for Content-Disposition
        import urllib.parse
        safe_filename = urllib.parse.quote(file_name.encode('utf-8'))

        # Detect MIME type
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
            # Parse Range: bytes=start-end
            try:
                units, rng = range_header.split('=')
                if units.strip() != 'bytes':
                    raise ValueError('Invalid units')
                start_str, end_str = rng.split('-')
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1
                
                # Validate the requested range
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
            # Full download streaming
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
    """Copy an .h5ad file into the Cellxgene data directory for preview"""
    try:
        # Only allow the owner to publish
        try:
            file_obj = File.objects.get(id=file_id, user=request.user)
        except File.DoesNotExist:
            return Response({'message': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        # Ensure the physical artifact exists
        if not file_obj.file or not os.path.exists(file_obj.file.path):
            return Response({'message': 'Source file is missing'}, status=status.HTTP_404_NOT_FOUND)

        # Enforce .h5ad extension
        original = file_obj.original_filename or os.path.basename(file_obj.file.name)
        if not str(original).lower().endswith('.h5ad'):
            return Response({'message': 'Only .h5ad files can be published to Cellxgene'}, status=status.HTTP_400_BAD_REQUEST)

        # Target directory (configurable via CELLXGENE_DATA_DIR)
        from django.conf import settings
        target_dir = getattr(settings, 'CELLXGENE_DATA_DIR', os.path.join(settings.BASE_DIR, 'cellxgene_data'))
        os.makedirs(target_dir, exist_ok=True)

        # Sanitize filename to avoid traversal
        safe_basename = re.sub(r'[^A-Za-z0-9\._-]', '_', os.path.basename(original))
        target_filename = f"{file_obj.id}__{safe_basename}"
        target_path = os.path.join(target_dir, target_filename)

        try:
            shutil.copy2(file_obj.file.path, target_path)
        except Exception as e:
            return Response({'message': f'Failed to copy file: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        prepare_info = prepare_h5ad_for_cellxgene(target_path)
        if prepare_info.get('status') == 'error':
            message = f"Copied to the Cellxgene data directory but failed to create embeddings: {prepare_info.get('message')}"
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
        message = 'File published to the Cellxgene data directory'

        status_text = restart_info.get('status')
        if status_text == 'started':
            message += '; Cellxgene is reloading the dataset.'
        elif status_text == 'skipped':
            message += '. Automatic restart is disabled; start Cellxgene manually.'
        elif status_text == 'error':
            detail = restart_info.get('message') or 'Cellxgene failed to start'
            message += f'; unable to auto-start Cellxgene: {detail}'
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
        return Response({'message': f'Publishing failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """Return aggregate stats for the authenticated user"""
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
    """List folders or create a new folder"""
    if request.method == 'GET':
        parent_id = request.GET.get('parent_id')
        
        if parent_id:
            try:
                parent_folder = Folder.objects.get(id=parent_id, user=request.user)
                folders = Folder.objects.filter(user=request.user, parent=parent_folder).order_by('name')
            except Folder.DoesNotExist:
                return Response({'error': 'Parent folder not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Return root-level folders
            folders = Folder.objects.filter(user=request.user, parent=None).order_by('name')
        
        serializer = FolderSerializer(folders, many=True, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = FolderCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Ensure the user can create under the parent
            parent_folder = serializer.validated_data.get('parent')
            if parent_folder and parent_folder.user != request.user:
                return Response({'error': 'You do not have permission to create under this folder'}, status=status.HTTP_403_FORBIDDEN)
            
            folder = serializer.save()
            response_serializer = FolderSerializer(folder, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def folder_detail(request, folder_id):
    """Retrieve, update, or delete a folder"""
    try:
        folder = Folder.objects.get(id=folder_id, user=request.user)
    except Folder.DoesNotExist:
        return Response({'error': 'Folder not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = FolderSerializer(folder, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = FolderCreateSerializer(folder, data=request.data, context={'request': request})
        if serializer.is_valid():
            # Validate permissions for the destination parent
            parent_folder = serializer.validated_data.get('parent')
            if parent_folder and parent_folder.user != request.user:
                return Response({'error': 'You do not have permission to move into that folder'}, status=status.HTTP_403_FORBIDDEN)
            
            folder = serializer.save()
            response_serializer = FolderSerializer(folder, context={'request': request})
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Ensure the folder is empty
        if folder.subfolders.exists() or folder.files.exists():
            return Response({'error': 'Folder must be empty before deletion'}, status=status.HTTP_400_BAD_REQUEST)
        
        folder.delete()
        return Response({'message': 'Folder deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def folder_breadcrumb(request, folder_id):
    """Return breadcrumb metadata for a folder"""
    try:
        folder = Folder.objects.get(id=folder_id, user=request.user)
    except Folder.DoesNotExist:
        return Response({'error': 'Folder not found'}, status=status.HTTP_404_NOT_FOUND)
    
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
    """Return all folders owned by the current user"""
    folders = Folder.objects.filter(user=request.user).order_by('name')
    folder_serializer = FolderSerializer(folders, many=True, context={'request': request})
    
    return Response({
        'folders': folder_serializer.data
    })