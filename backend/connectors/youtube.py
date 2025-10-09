import feedparser
from datetime import datetime
import asyncio

async def fetch_posts(channel_ids):
    """Fetch posts from YouTube channels via RSS"""
    posts = []
    
    for channel_id in channel_ids:
        try:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, url)
            
            for entry in feed.entries:
                posts.append({
                    "id": entry.get('yt_videoid', entry.link),
                    "title": entry.title,
                    "link": entry.link,
                    "platform": "YouTube",
                    "source": entry.get('author', 'Unknown'),
                    "date": datetime(*entry.published_parsed[:6]).isoformat() if hasattr(entry, 'published_parsed') else datetime.now().isoformat(),
                    "description": entry.get('summary', '')[:200]
                })
        except Exception as e:
            print(f"Error fetching YouTube channel {channel_id}: {e}")
            
    return posts
