from django.contrib import admin

from .models import MLTask


@admin.register(MLTask)
class MLTaskAdmin(admin.ModelAdmin):
  list_display = ('id', 'task_type', 'file', 'status', 'created_by', 'created_at')
  list_filter = ('task_type', 'status', 'created_at')
  search_fields = ('file__original_filename', 'file__title', 'created_by__username')
