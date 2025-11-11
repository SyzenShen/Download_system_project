from django.urls import path
from . import api_views
from . import chunked_api_views as chunk_api
from . import search_views

urlpatterns = [
    # File APIs
    path('', api_views.file_list, name='api_file_list'),
    path('upload/', api_views.file_upload, name='api_file_upload'),
    path('ncbi/import/', api_views.ncbi_import, name='api_file_ncbi_import'),
    path('<int:file_id>/delete/', api_views.file_delete, name='api_file_delete'),
    path('<int:file_id>/download/', api_views.file_download, name='api_file_download'),
    # Backward-compatible path: /api/files/download/<id>/
    path('download/<int:file_id>/', api_views.file_download, name='api_file_download_legacy'),
    # Publish to Cellxgene (copy file into the Cellxgene data dir)
    path('<int:file_id>/publish-cellxgene/', api_views.publish_cellxgene, name='publish_cellxgene'),
    path('stats/', api_views.user_stats, name='api_user_stats'),
    
    # File search APIs
    path('search/', search_views.search_files, name='file-search'),
    path('facets/', search_views.get_facets, name='file-facets'),
    path('suggestions/', search_views.search_suggestions, name='search-suggestions'),
    path('<int:file_id>/preview/', search_views.file_preview, name='file-preview'),
    
    # Folder APIs
    path('folders/', api_views.folder_list_create, name='api_folder_list_create'),
    path('folders/all/', api_views.folder_all, name='api_folder_all'),
    path('folders/<int:folder_id>/', api_views.folder_detail, name='api_folder_detail'),
    path('folders/<int:folder_id>/breadcrumb/', api_views.folder_breadcrumb, name='api_folder_breadcrumb'),
    
    # Chunked upload endpoints
    path('chunked/init/', chunk_api.chunked_upload_init, name='api_chunked_upload_init'),
    path('chunked/<str:session_id>/chunk/', chunk_api.chunked_upload_chunk, name='api_chunked_upload_chunk'),
    path('chunked/<str:session_id>/complete/', chunk_api.chunked_upload_complete, name='api_chunked_upload_complete'),
    path('chunked/<str:session_id>/cancel/', chunk_api.chunked_upload_cancel, name='api_chunked_upload_cancel'),
]