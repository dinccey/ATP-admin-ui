from django.urls import path
from .views import VideoListView, VideoUpdateView

urlpatterns = [
    path('', VideoListView.as_view(), name='video_list'),
    path('<int:pk>/', VideoUpdateView.as_view(), name='video_update'),
]
