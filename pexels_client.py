"""
Pexels API client for fetching open source videos
"""
import requests
import os
from typing import Dict, Optional


class PexelsClient:
    """Client for interacting with the Pexels API"""
    
    BASE_URL = "https://api.pexels.com/videos"
    
    def __init__(self, api_key: str):
        """
        Initialize the Pexels client
        
        Args:
            api_key: Your Pexels API key
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": api_key
        }
    
    def search_videos(self, query: str, per_page: int = 15, page: int = 1,
                     orientation: str = "landscape", size: str = "medium") -> Optional[Dict]:
        """
        Search for videos on Pexels
        
        Args:
            query: Search query (e.g., "nature", "city", "ocean")
            per_page: Number of results per page (default: 15, max: 80)
            page: Page number (default: 1)
            orientation: Video orientation - "landscape", "portrait", or "square"
            size: Minimum video size - "large", "medium", or "small"
        
        Returns:
            Dictionary containing search results or None if error
        """
        params = {
            "query": query,
            "per_page": per_page,
            "page": page,
            "orientation": orientation,
            "size": size
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/search",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error searching videos: {e}")
            return None
    
    def get_popular_videos(self, per_page: int = 15, page: int = 1) -> Optional[Dict]:
        """
        Get popular videos from Pexels
        
        Args:
            per_page: Number of results per page (default: 15, max: 80)
            page: Page number (default: 1)
        
        Returns:
            Dictionary containing popular videos or None if error
        """
        params = {
            "per_page": per_page,
            "page": page
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/popular",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching popular videos: {e}")
            return None
    
    def download_video(self, video_url: str, output_path: str) -> bool:
        """
        Download a video from Pexels
        
        Args:
            video_url: URL of the video to download
            output_path: Path where the video will be saved
        
        Returns:
            True if download successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create if there's a directory component
                os.makedirs(output_dir, exist_ok=True)
            
            response = requests.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True
        except (requests.exceptions.RequestException, OSError, IOError) as e:
            print(f"Error downloading video: {e}")
            return False
    
    @staticmethod
    def get_video_file(video_data: Dict, quality: str = "hd") -> Optional[str]:
        """
        Extract video file URL from video data
        
        Args:
            video_data: Video data from Pexels API
            quality: Preferred quality - "hd" or "sd"
        
        Returns:
            Video file URL or None if not found
        """
        video_files = video_data.get("video_files", [])
        
        # Try to find the requested quality
        for video_file in video_files:
            if quality == "hd" and video_file.get("quality") == "hd":
                return video_file.get("link")
            elif quality == "sd" and video_file.get("quality") == "sd":
                return video_file.get("link")
        
        # Fallback to first available video
        if video_files:
            return video_files[0].get("link")
        
        return None
