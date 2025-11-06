from django.conf import settings
from django.db import models


class MLTask(models.Model):
  """
  Placeholder task model for future ML-powered automations.
  """

  TASK_TYPES = [
    ('autotag', 'Auto Tagging'),
    ('qc', 'QC Check'),
    ('summary', 'Summary Generation'),
    ('embedding', 'Embedding Extraction'),
    ('h5ad_vis', 'h5ad Preprocessing'),
  ]

  STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('queued', 'Queued'),
    ('running', 'Running'),
    ('done', 'Done'),
    ('failed', 'Failed'),
  ]

  file = models.ForeignKey(
    'file_upload.File',
    on_delete=models.CASCADE,
    related_name='ml_tasks',
  )
  task_type = models.CharField(max_length=50, choices=TASK_TYPES)
  status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
  result = models.JSONField(default=dict, blank=True)
  created_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='ml_tasks',
  )
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['-created_at']

  def __str__(self):
    return f"{self.get_task_type_display()} for {self.file_id} ({self.status})"
