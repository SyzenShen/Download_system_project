from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import MLTask
from .serializers import MLTaskSerializer


class MLTaskViewSet(viewsets.ModelViewSet):
  """
  Unified entrypoint for ML-powered background jobs.
  Currently records requests only; execution can be wired later.
  """

  serializer_class = MLTaskSerializer
  permission_classes = [permissions.IsAuthenticated]

  def get_queryset(self):
    base_qs = MLTask.objects.select_related('file', 'created_by').order_by('-created_at')
    if self.request.user and self.request.user.is_staff:
      return base_qs
    return base_qs.filter(created_by=self.request.user)

  def perform_create(self, serializer):
    serializer.save(created_by=self.request.user)

  @action(detail=False, methods=['post'])
  def trigger(self, request):
    task_type = request.data.get('task_type')
    file_id = request.data.get('file_id')

    valid_types = {choice[0] for choice in MLTask.TASK_TYPES}

    if task_type not in valid_types:
      return Response(
        {'detail': 'Invalid task_type. Expected one of: {}'.format(', '.join(sorted(valid_types)))},
        status=status.HTTP_400_BAD_REQUEST,
      )

    if not file_id:
      return Response({'detail': 'file_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    task = MLTask.objects.create(
      file_id=file_id,
      task_type=task_type,
      status='queued',
      created_by=request.user,
    )

    # Future hook: enqueue job for Celery / external worker here
    return Response({'task_id': task.id, 'status': task.status}, status=status.HTTP_202_ACCEPTED)
