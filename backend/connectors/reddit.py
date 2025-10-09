import feedparser
from datetime import datetime
import asyncio

async def fetch_posts(subreddits):
    """Fetch posts from Reddit subreddits via RSS"""
    posts = []
    
    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/.rss"
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, url)
            
            for entry in feed.entries:
                posts.append({
                    "id": entry.get('id', entry.link),
                    "title": entry.title,
                    "link": entry.link,
                    "platform": "Reddit",
                    "source": f"r/{sub}",
                    "date": datetime(*entry.published_parsed[:6]).isoformat() if hasattr(entry, 'published_parsed') else datetime.now().isoformat(),
                    "description": entry.get('summary', '')[:200]
                })
        except Exception as e:
            print(f"Error fetching Reddit r/{sub}: {e}")
            
    return posts
