from rest_framework import serializers
from .models import Image
from typing import Optional

class ImageSerializer(serializers.ModelSerializer):
    optimized_url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['id', 'url', 'upload_date', 'active', 'optimized_url']
        read_only_fields = ('id', 'upload_date')

    def get_optimized_url(self, obj: 'Image') -> Optional[str]:
        """Get optimized Cloudinary URL"""
        if obj.image:
            if hasattr(obj.image, 'build_url'):
                return obj.image.build_url(
                    width=800,
                    height=600,
                    crop='limit',
                    quality='auto',
                    fetch_format='auto'
                )
            return obj.image.url
        return None


class YouTubeVideoSerializer(serializers.Serializer):
    """Serializer for YouTube video data"""
    id = serializers.CharField(help_text="YouTube video ID")
    title = serializers.CharField(help_text="Video title")
    description = serializers.CharField(help_text="Video description")
    thumbnail = serializers.URLField(help_text="Video thumbnail URL")
    published_at = serializers.DateTimeField(help_text="Video publication date")
    url = serializers.URLField(help_text="YouTube video URL", required=False)