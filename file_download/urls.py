from django.urls import path, re_path
from . import views

# namespace
app_name = 'file_download'

urlpatterns = [

    # Legacy path download via file path (kept for compatibility)
    re_path(r'^download/(?P<file_path>.*)/$', views.file_response_download, name='file_download'),

    # New: safer download via file ID with UTF-8 filename headers
    path('download/<int:file_id>/', views.file_download_by_id, name='file_download_by_id'),

]
