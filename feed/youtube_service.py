# feed/youtube_service.py
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.utils import timezone
import pytz
from datetime import datetime
import logging
from .cache_utils import VideoCache

logger = logging.getLogger(__name__)


class YouTubeService:
    def __init__(self):
        # FIX #1: Always initialize cache first, even if build() fails
        # This ensures service.cache is always available for tests
        self.cache = VideoCache()
        self.channel_id = getattr(settings, 'YOUTUBE_CHANNEL_ID', None)
        
        try:
            self.youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize YouTube service: {str(e)}")
            self.youtube = None

    def fetch_videos_from_api(self, max_results=None):
        """Fetch videos directly from YouTube API"""
        if not self.youtube:
            logger.error("YouTube service not initialized")
            return []

        try:
            videos = []
            next_page_token = None
            total_api_calls = 0  # Track API usage

            while True:
                total_api_calls += 1
                logger.info(f"Making API call #{total_api_calls}")

                # Prepare request parameters
                request_params = {
                    "part": "snippet",
                    "channelId": self.channel_id,
                    "order": "date",
                    "type": "video",
                    "maxResults": 50,  # Maximum allowed by YouTube API
                }

                if next_page_token:
                    request_params["pageToken"] = next_page_token

                # Execute request
                request = self.youtube.search().list(**request_params)
                response = request.execute()

                # Log the number of items received
                items_count = len(response.get("items", []))
                logger.info(f"Received {items_count} videos in this page")

                # Process videos from current page
                for item in response["items"]:
                    snippet = item["snippet"]
                    video_id = item["id"]["videoId"]
                    
                    upload_date = datetime.strptime(
                        snippet["publishedAt"], "%Y-%m-%dT%H:%M:%SZ"
                    )
                    upload_date = upload_date.replace(tzinfo=pytz.UTC)

                    # Get thumbnail URL (high quality preferred)
                    thumbnails = snippet.get("thumbnails", {})
                    thumbnail_url = (
                        thumbnails.get("high", {}).get("url") or
                        thumbnails.get("medium", {}).get("url") or
                        thumbnails.get("default", {}).get("url") or
                        ""
                    )

                    # FIX #3: Use strftime with 'Z' suffix instead of isoformat() 
                    # which produces '+00:00' format
                    video = {
                        "id": video_id,
                        "title": snippet["title"],
                        "description": snippet.get("description", ""),
                        "thumbnail": thumbnail_url,
                        "published_at": upload_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "upload_date": upload_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "type": "video",
                    }
                    videos.append(video)
                    logger.debug(f"Added video: {video['title']} ({video['id']})")

                # Check if we've reached the desired number of results
                if max_results and len(videos) >= max_results:
                    videos = videos[:max_results]
                    break

                # Get next page token
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    logger.info("No more pages available")
                    break

            logger.info(f"Total videos fetched from API: {len(videos)}")
            return videos

        except HttpError as e:
            if "quotaExceeded" in str(e):
                logger.warning("YouTube API quota exceeded")
            else:
                logger.error(f"YouTube API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching YouTube videos: {str(e)}")
            return []

    def get_channel_videos(self, max_results=None, force_refresh=False):
        """
        Get videos from cache or YouTube API

        Args:
            max_results (int, optional): Maximum number of videos to return
            force_refresh (bool): If True, bypass cache and fetch fresh from API
        """
        if not force_refresh:
            # FIX #2: Add exception handling around cache operations
            # If cache throws an error, fall back to API gracefully
            try:
                cached_videos = self.cache.get_cached_videos()
                if cached_videos:
                    logger.info(f"Returning {len(cached_videos)} videos from cache")
                    return cached_videos
            except Exception as e:
                # Cache error - log it but don't crash, fall through to API
                logger.warning(f"Cache error, falling back to API: {str(e)}")

        # Fetch from API
        logger.info("Fetching fresh videos from YouTube API")
        videos = self.fetch_videos_from_api(max_results)

        # Update cache with new videos
        if videos:
            logger.info(f"Updating cache with {len(videos)} videos")
            self.cache.update_cache(videos)
        else:
            logger.warning("No videos found to cache")

        return videos