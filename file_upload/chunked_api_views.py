from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from django.conf import settings
from django.utils.encoding import smart_str
from django.core.files import File as DjangoFile
import os
import uuid

from .models import UploadSession, File
from .serializers import FileSerializer


def _get_tmp_dir(user_id):
    base = getattr(settings, 'MEDIA_ROOT', None) or settings.BASE_DIR
    tmp_dir = os.path.join(base, 'tmp', 'uploads', str(user_id))
    os.makedirs(tmp_dir, exist_ok=True)
    return tmp_dir


@csrf_exempt
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def chunked_upload_init(request):
    data = request.data if hasattr(request, 'data') else {}
    filename = smart_str(data.get('filename') or '')
    total_size = int(data.get('total_size') or 0)
    chunk_size = int(data.get('chunk_size') or (2 * 1024 * 1024))

    if not filename or total_size <= 0:
        return Response({'message': '缺少必要参数'}, status=status.HTTP_400_BAD_REQUEST)

    tmp_dir = _get_tmp_dir(request.user.id)
    session_id = uuid.uuid4().hex
    temp_path = os.path.join(tmp_dir, f'{session_id}.part')

    session = UploadSession.objects.create(
        session_id=session_id,
        user=request.user,
        original_filename=filename,
        total_size=total_size,
        chunk_size=chunk_size,
        uploaded_size=0,
        temp_path=temp_path,
        status='active'
    )

    with open(temp_path, 'wb') as f:
        pass

    return Response({'session_id': session.session_id, 'chunk_size': session.chunk_size}, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['PUT', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def chunked_upload_chunk(request, session_id):
    try:
        session = UploadSession.objects.get(session_id=session_id, user=request.user)
    except UploadSession.DoesNotExist:
        return Response({'message': '会话不存在'}, status=status.HTTP_404_NOT_FOUND)

    if session.status != 'active':
        return Response({'message': '会话不可用'}, status=status.HTTP_400_BAD_REQUEST)

    range_header = request.headers.get('Content-Range') or request.META.get('HTTP_CONTENT_RANGE')
    if not range_header:
        return Response({'message': '缺少 Content-Range 头'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        units, rng_total = range_header.split(' ')
        if units.strip().lower() != 'bytes':
            raise ValueError('units')
        range_part, total_part = rng_total.split('/')
        start_str, end_str = range_part.split('-')
        start = int(start_str)
        end = int(end_str)
        total = int(total_part)
    except Exception:
        return Response({'message': 'Content-Range 格式错误'}, status=status.HTTP_400_BAD_REQUEST)

    if total != session.total_size:
        return Response({'message': '总大小不一致'}, status=status.HTTP_400_BAD_REQUEST)

    chunk = request.body
    if not isinstance(chunk, (bytes, bytearray)) or len(chunk) != (end - start + 1):
        return Response({'message': '分片大小不匹配'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with open(session.temp_path, 'r+b') as f:
            f.seek(start)
            f.write(chunk)
    except FileNotFoundError:
        with open(session.temp_path, 'wb') as f:
            f.seek(start)
            f.write(chunk)

    session.uploaded_size = max(session.uploaded_size, end + 1)
    session.save(update_fields=['uploaded_size'])
    return Response({'uploaded_size': session.uploaded_size}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def chunked_upload_complete(request, session_id):
    try:
        session = UploadSession.objects.get(session_id=session_id, user=request.user)
    except UploadSession.DoesNotExist:
        return Response({'message': '会话不存在'}, status=status.HTTP_404_NOT_FOUND)

    if session.status != 'active':
        return Response({'message': '会话不可用'}, status=status.HTTP_400_BAD_REQUEST)

    if session.uploaded_size != session.total_size:
        return Response({'message': '上传未完成'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with open(session.temp_path, 'rb') as fp:
            django_file = DjangoFile(fp, name=session.original_filename)
            file_obj = File(user=request.user, upload_method='Chunked Upload', original_filename=session.original_filename)
            file_obj.file.save(session.original_filename, django_file, save=True)
    except Exception:
        return Response({'message': '写入文件失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    session.status = 'completed'
    session.save(update_fields=['status'])
    try:
        if os.path.exists(session.temp_path):
            os.remove(session.temp_path)
    except Exception:
        pass

    serializer = FileSerializer(file_obj, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def chunked_upload_cancel(request, session_id):
    try:
        session = UploadSession.objects.get(session_id=session_id, user=request.user)
    except UploadSession.DoesNotExist:
        return Response({'message': '会话不存在'}, status=status.HTTP_404_NOT_FOUND)

    session.status = 'canceled'
    session.save(update_fields=['status'])
    try:
        if os.path.exists(session.temp_path):
            os.remove(session.temp_path)
    except Exception:
        pass

    return Response({'message': '已取消上传'}, status=status.HTTP_200_OK)