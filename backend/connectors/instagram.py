import feedparser
from datetime import datetime
import asyncio

RSSHUB_BASE = "https://rsshub.app"

async def fetch_posts(usernames):
    """Fetch posts from Instagram users via RSSHub"""
    posts = []
    
    for username in usernames:
        try:
            url = f"{RSSHUB_BASE}/instagram/user/{username}"
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, url)
            
            for entry in feed.entries:
                posts.append({
                    "id": entry.get('id', entry.link),
                    "title": entry.title,
                    "link": entry.link,
                    "platform": "Instagram",
                    "source": f"@{username}",
                    "date": datetime(*entry.published_parsed[:6]).isoformat() if hasattr(entry, 'published_parsed') else datetime.now().isoformat(),
                    "description": entry.get('summary', '')[:200]
                })
        except Exception as e:
            print(f"Error fetching Instagram @{username}: {e}")
    
    return posts
