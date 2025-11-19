# videos/views.py
import os
import json
from datetime import datetime
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect
from django.db.models.fields import CharField, TextField, IntegerField, BigIntegerField
from django.db.models import Count
from collections import defaultdict
from django.contrib import messages
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

        if self.request.GET.get('duplicates'):
            # Find duplicates based on video_id, group by video_id, sort groups by newest created_at in each
            duplicates_qs = Video.objects.values('video_id').annotate(count=Count('video_id')).filter(count__gt=1)
            duplicate_ids = [d['video_id'] for d in duplicates_qs]
            duplicates = Video.objects.filter(video_id__in=duplicate_ids).order_by('video_id', '-created_at')
            grouped_duplicates = defaultdict(list)
            for video in duplicates:
                grouped_duplicates[video.video_id].append(video)
            context['grouped_duplicates'] = dict(grouped_duplicates)
            context['show_duplicates'] = True
        else:
            context['show_duplicates'] = False

        return context

class VideoUpdateView(UpdateView):
    model = Video
    form_class = VideoForm
    template_name = 'videos/edit.html'
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'delete_video' in request.POST:
            return self.delete_file('mp4')
        elif 'delete_audio' in request.POST:
            return self.delete_file('mp3')
        elif 'delete_vtt' in request.POST:
            return self.delete_file('vtt')
        elif 'delete_thumb' in request.POST:
            return self.delete_file('jpg')
        elif 'delete_json' in request.POST:
            return self.delete_file('json')
        elif 'delete_all' in request.POST:
            return self.delete_all()
        elif 'delete_db_only' in request.POST:
            return self.delete_db_only()
        else:
            return super().post(request, *args, **kwargs)

    def delete_file(self, ext):
        try:
            path = get_fs_path(self.object, ext)
            messages.info(self.request, f"Attempting to delete {ext.upper()} file at: {path}")
            if os.path.exists(path):
                os.remove(path)
                messages.success(self.request, f"{ext.upper()} file deleted successfully from: {path}")
            else:
                messages.warning(self.request, f"{ext.upper()} file not found at: {path}")
            if ext == 'jpg':
                self.object.thumb_url = None
                self.object.save()
                messages.success(self.request, "Thumbnail URL cleared in database.")
        except Exception as e:
            messages.error(self.request, f"Error deleting {ext.upper()} file: {str(e)}")
        return redirect(self.get_success_url())

    def delete_all(self):
        try:
            extensions = ['mp4', 'mp3', 'vtt', 'jpg', 'json']
            for ext in extensions:
                path = get_fs_path(self.object, ext)
                messages.info(self.request, f"Attempting to delete {ext.upper()} file at: {path}")
                if os.path.exists(path):
                    os.remove(path)
                    messages.success(self.request, f"{ext.upper()} file deleted successfully from: {path}")
                else:
                    messages.warning(self.request, f"{ext.upper()} file not found at: {path}")
            messages.info(self.request, f"Deleting database entry for video ID: {self.object.id}")
            self.object.delete()
            messages.success(self.request, "All files and database entry deleted successfully.")
        except Exception as e:
            messages.error(self.request, f"Error deleting all files and entry: {str(e)}")
        return redirect(self.get_success_url())

    def delete_db_only(self):
        try:
            messages.info(self.request, f"Deleting database entry for video ID: {self.object.id} (files remain intact)")
            self.object.delete()
            messages.success(self.request, "Database entry deleted successfully.")
        except Exception as e:
            messages.error(self.request, f"Error deleting database entry: {str(e)}")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('video_list')

    def form_valid(self, form):
        try:
            instance = form.save(commit=False)
            # Handle uploads first if any
            if 'json_file' in self.request.FILES:
                json_file = self.request.FILES['json_file']
                json_path = get_fs_path(instance, 'json')
                messages.info(self.request, f"Uploading JSON file to: {json_path}")
                with open(json_path, 'wb+') as destination:
                    for chunk in json_file.chunks():
                        destination.write(chunk)
                messages.success(self.request, f"JSON file uploaded successfully to: {json_path}")
                # Update DB from JSON
                with open(json_path, 'r') as f:
                    data = json.load(f)
                sql_params = data.get('sql_params', {})
                for k, v in sql_params.items():
                    if k != 'id' and k in DB_FIELDS:
                        setattr(instance, k, v)
                messages.success(self.request, "Database updated from uploaded JSON.")
            if 'thumb_file' in self.request.FILES:
                thumb_file = self.request.FILES['thumb_file']
                thumb_path = get_fs_path(instance, 'jpg')
                messages.info(self.request, f"Uploading thumbnail to: {thumb_path}")
                with open(thumb_path, 'wb+') as destination:
                    for chunk in thumb_file.chunks():
                        destination.write(chunk)
                messages.success(self.request, f"Thumbnail uploaded successfully to: {thumb_path}")
                instance.thumb_url = instance.vid_url.rsplit('.mp4', 1)[0] + '.jpg'
                messages.success(self.request, f"Thumbnail URL updated in database to: {instance.thumb_url}")
            if 'video_file' in self.request.FILES:
                video_file = self.request.FILES['video_file']
                video_path = get_fs_path(instance, 'mp4')
                messages.info(self.request, f"Replacing video file at: {video_path}")
                try:
                    with open(video_path, 'wb') as destination:  # ← 'wb' instead of 'wb+'
                            for chunk in video_file.chunks():
                                destination.write(chunk)
                    messages.success(self.request, f"Video file successfully replaced at: {video_path}")
                except Exception as e:
                    messages.error(self.request, f"Failed to write video file: {str(e)}")
            
            if 'audio_file' in self.request.FILES:
                audio_file = self.request.FILES['audio_file']
                audio_path = get_fs_path(instance, 'mp3')
                messages.info(self.request, f"Replacing audio file → {audio_path}")
                try:
                    with open(audio_path, 'wb') as f:  # ← 'wb' instead of 'wb+' → truncates old file
                        for chunk in audio_file.chunks():
                            f.write(chunk)
                    messages.success(
                        self.request,
                        f"✓ Audio file successfully replaced at: {audio_path} "
                        f"({audio_file.size} bytes written)"
                    )
                except Exception as e:
                    messages.error(self.request, f"✗ Failed to replace audio file: {str(e)}")
            elif form.cleaned_data['audio_delete']:
                audio_path = get_fs_path(instance, 'mp3')
                messages.info(self.request, f"Deleting audio file at: {audio_path}")
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    messages.success(self.request, f"Audio file deleted successfully from: {audio_path}")
                else:
                    messages.warning(self.request, f"Audio file not found at: {audio_path}")
            if 'vtt_file' in self.request.FILES:
                vtt_file = self.request.FILES['vtt_file']
                vtt_path = get_fs_path(instance, 'vtt')
                messages.info(self.request, f"Replacing VTT file at: {vtt_path}")
                with open(vtt_path, 'wb+') as destination:
                    for chunk in vtt_file.chunks():
                        destination.write(chunk)
                messages.success(self.request, f"VTT file replaced successfully at: {vtt_path}")
            elif form.cleaned_data['vtt_delete']:
                vtt_path = get_fs_path(instance, 'vtt')
                messages.info(self.request, f"Deleting VTT file at: {vtt_path}")
                if os.path.exists(vtt_path):
                    os.remove(vtt_path)
                    messages.success(self.request, f"VTT file deleted successfully from: {vtt_path}")
                else:
                    messages.warning(self.request, f"VTT file not found at: {vtt_path}")
            messages.info(self.request, "Saving changes to database...")
            instance.save()
            messages.success(self.request, "Database changes saved successfully.")
            # Now update or create JSON
            json_path = get_fs_path(instance, 'json')
            messages.info(self.request, f"Updating/Creating JSON file at: {json_path}")
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    data = json.load(f)
                data['sql_params'] = {f: getattr(instance, f) for f in DB_FIELDS}
                with open(json_path, 'w') as f:
                    json.dump(data, f, indent=4)
                messages.success(self.request, f"JSON file updated successfully at: {json_path}")
            else:
                rel_path = instance.vid_url.replace(os.getenv('BASE_SITE_URL', 'https://www.kjv1611only.com/'), '')
                target_filename = os.path.basename(instance.vid_url)
                try:
                    dt = datetime.strptime(instance.date, '%Y-%m-%d %H:%M:%S') if instance.date else None
                    us_mdY = dt.strftime('%m/%d/%Y') if dt else None
                except ValueError:
                    us_mdY = None
                data = {
                    "original_filename": target_filename,
                    "target_filename": target_filename,
                    "target_directory_relative": os.path.dirname(rel_path),
                    "original_vtt_filename": None,
                    "uploader": instance.main_category.split('(')[-1].rstrip(')') if instance.main_category else "Unknown",
                    "target_vtt_filename": target_filename.rsplit('.mp4', 1)[0] + '.vtt',
                    "sql_params": {f: getattr(instance, f) for f in DB_FIELDS},
                    "title": instance.name,
                    "us_mdY": us_mdY,
                    "error": None
                }
                with open(json_path, 'w') as f:
                    json.dump(data, f, indent=4)
                messages.success(self.request, f"JSON file created successfully at: {json_path}")
        except Exception as e:
            messages.error(self.request, f"Error during form validation or file operations: {str(e)}")
            return self.form_invalid(form)
        return super().form_valid(form)