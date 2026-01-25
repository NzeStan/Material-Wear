# feed/admin.py
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.html import format_html
from .models import Image, YouTubeCache
from .youtube_service import YouTubeService
from .cache_utils import VideoCache


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("thumbnail_preview", "id", "upload_date", "active")
    list_filter = ("active", "upload_date")
    list_editable = ("active",)
    ordering = ("-upload_date",)
    readonly_fields = ("upload_date", "large_thumbnail_preview")
    
    fieldsets = (
        ('Image', {
            'fields': ('large_thumbnail_preview', 'url', 'active'),
            'classes': ('wide',),
        }),
        ('Metadata', {
            'fields': ('upload_date',),
            'classes': ('collapse',),
        }),
    )
    
    def thumbnail_preview(self, obj):
        """Display thumbnail in list view"""
        if obj.url:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; '
                'border-radius: 4px; border: 2px solid #064E3B;" />',
                obj.url.url
            )
        return format_html(
            '<div style="width: 50px; height: 50px; background: #F3F4F6; '
            'border-radius: 4px; display: flex; align-items: center; '
            'justify-content: center; color: #9CA3AF;">No Image</div>'
        )
    thumbnail_preview.short_description = 'Preview'
    
    def large_thumbnail_preview(self, obj):
        """Display larger thumbnail in detail view"""
        if obj.url:
            return format_html(
                '<img src="{}" style="max-width: 400px; height: auto; '
                'border-radius: 8px; border: 3px solid #064E3B;" />',
                obj.url.url
            )
        return format_html(
            '<div style="width: 400px; height: 300px; background: #F3F4F6; '
            'border-radius: 8px; display: flex; align-items: center; '
            'justify-content: center; color: #9CA3AF; font-size: 18px;">No Image Available</div>'
        )
    large_thumbnail_preview.short_description = 'Current Image'


@admin.register(YouTubeCache)
class YouTubeCacheAdmin(admin.ModelAdmin):
    change_list_template = "admin/feed/youtubecache/change_list.html"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return YouTubeCache.objects.none()

    def changelist_view(self, request, extra_context=None):
        cache = VideoCache()
        last_updated = cache.get_last_updated()
        videos = cache.get_cached_videos() or []

        # Get the first few videos with thumbnails for display
        video_examples = []
        if videos:
            for video in videos[:8]:  # Show 8 videos instead of 5
                video_examples.append(
                    {
                        "id": video.get("id", "Unknown"),
                        "title": video.get("title", "Untitled"),
                        "thumbnail": video.get("thumbnail", ""),
                        "published_at": video.get("published_at", ""),
                        "url": video.get("url", ""),
                    }
                )

        context = {
            "title": "YouTube Cache Management",
            "last_cache_update": last_updated,
            "videos_count": len(videos),
            "video_examples": video_examples,
            "module_name": "YouTube Cache",
            "cl": {"opts": self.model._meta},
        }

        return TemplateResponse(request, self.change_list_template, context)

    def get_urls(self):
        urls = [
            path(
                "",
                self.admin_site.admin_view(self.changelist_view),
                name="feed_youtubecache_changelist",
            ),
            path(
                "refresh-cache/",
                self.admin_site.admin_view(self.refresh_cache),
                name="refresh-youtube-cache",
            ),
        ]
        return urls

    def refresh_cache(self, request):
        try:
            youtube_service = YouTubeService()

            # Force a fresh fetch from the API
            videos = youtube_service.get_channel_videos(force_refresh=True)

            if videos:
                cache = VideoCache()
                cache.update_cache(videos)
                messages.success(
                    request,
                    f'Successfully cached {len(videos)} videos! First video: {videos[0].get("title", "Untitled")}',
                )
            else:
                messages.warning(
                    request,
                    "No videos were fetched from YouTube API. Please check your API key and channel ID.",
                )

        except Exception as e:
            messages.error(
                request,
                f"Error updating cache: {str(e)}. Please check your YouTube API configuration.",
            )

        return redirect("admin:feed_youtubecache_changelist")