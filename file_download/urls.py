from django.urls import path, re_path
from . import views

# namespace
app_name = 'file_download'

urlpatterns = [

    # Folder download as ZIP (must be before the generic file_path pattern)
    path('download/folder/<int:folder_id>/', views.folder_download_by_id, name='folder_download_by_id'),

    # New: safer download via file ID with UTF-8 filename headers
    path('download/<int:file_id>/', views.file_download_by_id, name='file_download_by_id'),

    # Legacy path download via file path (kept for compatibility, must be last)
    re_path(r'^download/(?P<file_path>.*)/$', views.file_response_download, name='file_download'),

]
