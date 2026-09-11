from django.urls import path
from .views import (
    HealthCheckView,
    MediaInfoView,
    CreateDownloadTaskView,
    TaskStatusView,
    FileDownloadStreamView,
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='api-health'),
    path('info/', MediaInfoView.as_view(), name='api-info'),
    path('download/', CreateDownloadTaskView.as_view(), name='api-download'),
    path('tasks/<uuid:task_id>/', TaskStatusView.as_view(), name='api-task-status'),
    path('files/<uuid:task_id>/', FileDownloadStreamView.as_view(), name='api-file-download'),
]
