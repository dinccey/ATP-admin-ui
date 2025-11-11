import os
import json
from datetime import datetime
from django.views.generic import ListView, UpdateView
from django.shortcuts import get_object_or_404
from django.db.models.fields import CharField, TextField, IntegerField, BigIntegerField, DateTimeField
from .models import Video
from .forms import VideoForm
from .mappings import DB_FIELDS


def get_fs_path(video, ext='mp4'):
    base_url = os.getenv('BASE_SITE_URL', 'https://www.kjv1611only.com/')
    rel_path = video.vid_url.replace(base_url, '')
    base_fs = os.getenv('FS_PATH', '/data')
    full_path = os.path.join(base_fs, rel_path)
    if ext != 'mp4':
        full_path = os.path.splitext(full_path)[0] + '.' + ext
    dir_path = os.path.dirname(full_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return full_path


class VideoListView(ListView):
    model = Video
    template_name = 'videos/list.html'
    paginate_by = 50
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        field = self.request.GET.get('field', 'video_id')
        if q and field in DB_FIELDS:
            try:
                model_field = Video._meta.get_field(field)
                if isinstance(model_field, (CharField, TextField)):
                    filter_kwargs = {f'{field}__icontains': q}
                elif isinstance(model_field, (IntegerField, BigIntegerField)):
                    filter_kwargs = {field: int(q)}
                elif isinstance(model_field, DateTimeField):
                    dt = datetime.strptime(q, '%Y-%m-%d %H:%M:%S')
                    filter_kwargs = {field: dt}
                else:
                    return queryset
                queryset = queryset.filter(**filter_kwargs)
            except:
                pass
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields'] = DB_FIELDS
        context['selected_field'] = self.request.GET.get('field', 'video_id')
        context['q'] = self.request.GET.get('q', '')
        return context


class VideoUpdateView(UpdateView):
    model = Video
    form_class = VideoForm
    template_name = 'videos/edit.html'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        instance = form.save(commit=False)
        # Handle uploads first if any
        if 'json_file' in self.request.FILES:
            json_file = self.request.FILES['json_file']
            json_path = get_fs_path(instance, 'json')
            with open(json_path, 'wb+') as destination:
                for chunk in json_file.chunks():
                    destination.write(chunk)
            # Update DB from JSON
            with open(json_path, 'r') as f:
                data = json.load(f)
            sql_params = data.get('sql_params', {})
            for k, v in sql_params.items():
                if k != 'id' and k in DB_FIELDS:
                    setattr(instance, k, v)
        if 'thumb_file' in self.request.FILES:
            thumb_file = self.request.FILES['thumb_file']
            thumb_path = get_fs_path(instance, 'jpg')
            with open(thumb_path, 'wb+') as destination:
                for chunk in thumb_file.chunks():
                    destination.write(chunk)
            instance.thumb_url = instance.vid_url.rsplit('.mp4', 1)[0] + '.jpg'
        if 'video_file' in self.request.FILES:
            video_file = self.request.FILES['video_file']
            video_path = get_fs_path(instance, 'mp4')
            with open(video_path, 'wb+') as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)
        if 'audio_file' in self.request.FILES:
            audio_file = self.request.FILES['audio_file']
            audio_path = get_fs_path(instance, 'mp3')
            with open(audio_path, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)
        elif form.cleaned_data['audio_delete']:
            audio_path = get_fs_path(instance, 'mp3')
            if os.path.exists(audio_path):
                os.remove(audio_path)
        if 'vtt_file' in self.request.FILES:
            vtt_file = self.request.FILES['vtt_file']
            vtt_path = get_fs_path(instance, 'vtt')
            with open(vtt_path, 'wb+') as destination:
                for chunk in vtt_file.chunks():
                    destination.write(chunk)
        elif form.cleaned_data['vtt_delete']:
            vtt_path = get_fs_path(instance, 'vtt')
            if os.path.exists(vtt_path):
                os.remove(vtt_path)
        instance.save()
        # Now update or create JSON
        json_path = get_fs_path(instance, 'json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
            data['sql_params'] = {f: getattr(instance, f) for f in DB_FIELDS}
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=4)
        else:
            rel_path = instance.vid_url.replace(os.getenv('BASE_SITE_URL', 'https://www.kjv1611only.com/'), '')
            target_filename = os.path.basename(instance.vid_url)
            data = {
                "original_filename": target_filename,
                "target_filename": target_filename,
                "target_directory_relative": os.path.dirname(rel_path),
                "original_vtt_filename": None,
                "uploader": instance.main_category.split('(')[-1].rstrip(')') if instance.main_category else "Unknown",
                "target_vtt_filename": target_filename.rsplit('.mp4', 1)[0] + '.vtt',
                "sql_params": {f: getattr(instance, f) for f in DB_FIELDS},
                "title": instance.name,
                "us_mdY": instance.date.strftime('%m/%d/%Y') if instance.date else None,
                "error": None
            }
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=4)
        return super().form_valid(form)
