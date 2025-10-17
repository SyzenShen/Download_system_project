from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import os
import uuid

# Create your models here.
# Define user directory path


def generate_session_id():
    """生成唯一的会话ID"""
    return uuid.uuid4().hex


def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid.uuid4().hex[:10], ext)
    return os.path.join("files", str(instance.user.id), filename)


class Folder(models.Model):
    """文件夹模型，支持层级结构"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=255, verbose_name="文件夹名称")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        # 确保同一用户在同一父目录下不能有重名文件夹
        unique_together = ['user', 'parent', 'name']

    def clean(self):
        """验证文件夹不能成为自己的子文件夹（防止循环引用）"""
        if self.parent:
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError("文件夹不能成为自己的子文件夹")
                current = current.parent

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_path(self):
        """获取文件夹的完整路径"""
        path_parts = []
        current = self
        while current:
            path_parts.append(current.name)
            current = current.parent
        return '/'.join(reversed(path_parts))

    def get_all_subfolders(self):
        """递归获取所有子文件夹"""
        subfolders = list(self.subfolders.all())
        for subfolder in self.subfolders.all():
            subfolders.extend(subfolder.get_all_subfolders())
        return subfolders

    def __str__(self):
        return f"{self.get_path()} - {self.user.username}"


class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to=user_directory_path, null=True)
    upload_method = models.CharField(max_length=20, verbose_name="Upload Method")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(default=0)
    original_filename = models.CharField(max_length=255, blank=True)
    # 添加文件夹关联，支持目录结构
    parent_folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='files')

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            if not self.original_filename:
                self.original_filename = self.file.name
        super().save(*args, **kwargs)

    def get_path(self):
        """获取文件的完整路径"""
        if self.parent_folder:
            return f"{self.parent_folder.get_path()}/{self.original_filename}"
        return self.original_filename

    def __str__(self):
        return f"{self.get_path()} - {self.user.username}"

    class Meta:
        ordering = ['-uploaded_at']
        # 确保同一用户在同一文件夹下不能有重名文件
        unique_together = ['user', 'parent_folder', 'original_filename']


class UploadSession(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    )

    session_id = models.CharField(max_length=64, unique=True, default=generate_session_id)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upload_sessions')
    original_filename = models.CharField(max_length=255)
    total_size = models.BigIntegerField(default=0)
    chunk_size = models.IntegerField(default=2 * 1024 * 1024)  # 2MB 默认分片
    uploaded_size = models.BigIntegerField(default=0)
    temp_path = models.CharField(max_length=512)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    parent_folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='upload_sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_id} ({self.original_filename}) - {self.status}"