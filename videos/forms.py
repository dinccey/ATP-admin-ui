from django import forms
from .models import Video
from .mappings import DB_FIELDS

class VideoForm(forms.ModelForm):
    json_file = forms.FileField(required=False, label="Upload JSON")
    thumb_file = forms.FileField(required=False, label="Upload Thumbnail (.jpg)")
    video_file = forms.FileField(required=False, label="Replace Video (.mp4)")
    audio_file = forms.FileField(required=False, label="Replace Audio (.mp3)")
    audio_delete = forms.BooleanField(required=False, label="Delete Audio")
    vtt_file = forms.FileField(required=False, label="Upload/Replace VTT (.vtt)")
    vtt_delete = forms.BooleanField(required=False, label="Delete VTT")

    class Meta:
        model = Video
        fields = [f for f in DB_FIELDS if f != 'id']
