"""
Example usage of the Pexels client programmatically
This demonstrates how to use the PexelsClient class without the GUI
"""
from pexels_client import PexelsClient
import os


def example_search_and_download():
    """Example: Search for videos and download them"""
    
    # Initialize client with your API key
    # Get your free API key from https://www.pexels.com/api/
    api_key = os.getenv("PEXELS_API_KEY", "your_api_key_here")
    
    if api_key == "your_api_key_here":
        print("Please set PEXELS_API_KEY environment variable or edit this script")
        print("Get your free API key from https://www.pexels.com/api/")
        return
    
    client = PexelsClient(api_key)
    
    # Search for videos
    print("Searching for nature videos...")
    results = client.search_videos(
        query="nature landscape",
        per_page=5,
        orientation="landscape",
        size="medium"
    )
    
    if results and "videos" in results:
        videos = results["videos"]
        print(f"\nFound {len(videos)} videos:")
        
        for idx, video in enumerate(videos, 1):
            print(f"\n{idx}. Video ID: {video['id']}")
            print(f"   Duration: {video['duration']} seconds")
            print(f"   Dimensions: {video['width']}x{video['height']}")
            print(f"   User: {video['user']['name']}")
            
            # Get video file URL
            video_url = client.get_video_file(video, quality="hd")
            if video_url:
                print(f"   Download URL: {video_url}")
                
                # Uncomment to download the video
                # output_path = f"downloads/video_{video['id']}.mp4"
                # if client.download_video(video_url, output_path):
                #     print(f"   Downloaded to: {output_path}")
    else:
        print("No videos found or error occurred")


def example_popular_videos():
    """Example: Get popular videos"""
    
    api_key = os.getenv("PEXELS_API_KEY", "your_api_key_here")
    
    if api_key == "your_api_key_here":
        print("Please set PEXELS_API_KEY environment variable")
        return
    
    client = PexelsClient(api_key)
    
    print("Fetching popular videos...")
    results = client.get_popular_videos(per_page=10)
    
    if results and "videos" in results:
        videos = results["videos"]
        print(f"\nFound {len(videos)} popular videos:")
        
        for idx, video in enumerate(videos, 1):
            print(f"{idx}. {video['user']['name']} - {video['duration']}s")


if __name__ == "__main__":
    print("="*60)
    print("Pexels Client Examples")
    print("="*60)
    print()
    
    # Run examples
    example_search_and_download()
    print("\n" + "="*60 + "\n")
    example_popular_videos()
    
    print("\n" + "="*60)
    print("For GUI interface, run: python3 videer_gui.py")
    print("="*60)
