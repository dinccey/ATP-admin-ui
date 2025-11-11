# videos/models.py
from django.db import models

class Video(models.Model):
    id = models.IntegerField(primary_key=True)
    vid_category = models.CharField(max_length=255)
    search_category = models.CharField(max_length=255)
    vid_preacher = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    vid_title = models.CharField(max_length=255)
    vid_code = models.TextField()
    date = models.CharField(max_length=19)  # Changed from DateTimeField to handle string values from DB
    vid_url = models.CharField(max_length=512)
    video_id = models.CharField(max_length=50)
    main_category = models.CharField(max_length=255)
    profile_id = models.IntegerField(null=True, blank=True)
    created_at = models.CharField(max_length=19)  # Changed from DateTimeField to handle string values from DB
    clicks = models.IntegerField(default=0)
    shorts = models.IntegerField(default=0)
    language = models.CharField(max_length=10)
    thumb_url = models.CharField(max_length=512, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'videos'