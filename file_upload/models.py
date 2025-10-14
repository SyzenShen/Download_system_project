from django.db import models
from django.contrib.auth.models import User
import os
import uuid

# Create your models here.
# Define user directory path


def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid.uuid4().hex[:10], ext)
    return os.path.join("files", str(instance.user.id), filename)


class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to=user_directory_path, null=True)
    upload_method = models.CharField(max_length=20, verbose_name="Upload Method")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(default=0)
    original_filename = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            if not self.original_filename:
                self.original_filename = self.file.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.original_filename} - {self.user.username}"

    class Meta:
        ordering = ['-uploaded_at']


class UploadSession(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    )

    session_id = models.CharField(max_length=64, unique=True, default=lambda: uuid.uuid4().hex)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upload_sessions')
    original_filename = models.CharField(max_length=255)
    total_size = models.BigIntegerField(default=0)
    chunk_size = models.IntegerField(default=2 * 1024 * 1024)  # 2MB 默认分片
    uploaded_size = models.BigIntegerField(default=0)
    temp_path = models.CharField(max_length=512)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_id} ({self.original_filename}) - {self.status}"