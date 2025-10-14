from django.urls import path
from . import api_views
from . import chunked_api_views as chunk_api

urlpatterns = [
    path('', api_views.file_list, name='api_file_list'),
    path('upload/', api_views.file_upload, name='api_file_upload'),
    path('<int:file_id>/delete/', api_views.file_delete, name='api_file_delete'),
    path('<int:file_id>/download/', api_views.file_download, name='api_file_download'),
    # 兼容旧路径：/api/files/download/<id>/
    path('download/<int:file_id>/', api_views.file_download, name='api_file_download_legacy'),
    path('stats/', api_views.user_stats, name='api_user_stats'),
    # 分片上传接口
    path('chunked/init/', chunk_api.chunked_upload_init, name='api_chunked_upload_init'),
    path('chunked/<str:session_id>/chunk/', chunk_api.chunked_upload_chunk, name='api_chunked_upload_chunk'),
    path('chunked/<str:session_id>/complete/', chunk_api.chunked_upload_complete, name='api_chunked_upload_complete'),
    path('chunked/<str:session_id>/cancel/', chunk_api.chunked_upload_cancel, name='api_chunked_upload_cancel'),
]