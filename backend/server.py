from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import os
from contextlib import asynccontextmanager

# Import connectors
from connectors import reddit, youtube, instagram, threads, twitter
from rss_utils import generate_rss

# MongoDB setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client.unified_feed_db

# Models
class Post(BaseModel):
    id: str
    title: str
    link: str
    platform: str
    source: str
    date: str
    description: str = ""

class FeedConfig(BaseModel):
    id: str = Field(default="default")
    reddit_subreddits: List[str] = ["python", "programming", "technology"]
    youtube_channels: List[str] = ["UC_x5XG1OV2P6uZZ5FSM9Ttw"]  # Google Developers
    instagram_users: List[str] = ["natgeo"]  # Example: National Geographic
    threads_users: List[str] = ["zuck"]  # Example: Mark Zuckerberg
    twitter_users: List[str] = ["elonmusk"]  # Example: Elon Musk
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting My Unified Feed API...")
    yield
    # Shutdown
    print("👋 Shutting down...")

app = FastAPI(title="My Unified Feed API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "My Unified Feed"}

@app.get("/api/feed", response_model=List[Post])
async def get_feed(
    platform: Optional[str] = Query(None, description="Filter by platform (Reddit, YouTube, etc.)"),
    keyword: Optional[str] = Query(None, description="Search keyword in title"),
    refresh: bool = Query(False, description="Force refresh from sources"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(50, ge=1, le=200, description="Number of posts per page")
):
    """Get unified feed from all sources with pagination"""
    
    # Check if we have cached posts (less than 10 minutes old)
    if not refresh:
        cache_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        cached_posts = await db.posts.find({
            "cached_at": {"$gte": cache_time.isoformat()}
        }).to_list(length=None)
        
        if cached_posts:
            posts = [Post(**{k: v for k, v in post.items() if k != '_id'}) for post in cached_posts]
        else:
            posts = await fetch_and_cache_posts()
    else:
        posts = await fetch_and_cache_posts()
    
    # Apply filters
    if platform:
        posts = [p for p in posts if p.platform.lower() == platform.lower()]
    
    if keyword:
        posts = [p for p in posts if keyword.lower() in p.title.lower()]
    
    # Sort by date descending
    posts.sort(key=lambda x: x.date, reverse=True)
    
    # Apply pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_posts = posts[start_idx:end_idx]
    
    return paginated_posts

@app.get("/api/feed/metadata")
async def get_feed_metadata():
    """Get feed metadata (count, last updated, etc.)"""
    
    # Get latest cached post to determine last update time
    latest_post = await db.posts.find_one(sort=[("cached_at", -1)])
    
    # Count total posts in cache
    total_posts = await db.posts.count_documents({})
    
    # Get config for last updated time
    config = await get_config()
    
    return {
        "total_posts": total_posts,
        "last_updated": latest_post.get("cached_at") if latest_post else None,
        "cache_ttl_minutes": 10,
        "config_updated": config.last_updated
    }

@app.get("/api/feed/rss")
async def get_rss_feed(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    keyword: Optional[str] = Query(None, description="Search keyword")
):
    """Export unified feed as RSS XML"""
    
    # Get posts (without pagination for RSS)
    posts_data = await get_feed(platform=platform, keyword=keyword, refresh=False, page=1, limit=200)
    posts_dict = [post.dict() for post in posts_data]
    
    return generate_rss(posts_dict)

@app.get("/api/config")
async def get_config():
    """Get current feed configuration"""
    config = await db.config.find_one({"id": "default"})
    if not config:
        # Create default config
        default_config = FeedConfig()
        await db.config.insert_one(default_config.dict())
        return default_config
    
    return FeedConfig(**{k: v for k, v in config.items() if k != '_id'})

@app.post("/api/config")
async def update_config(config: FeedConfig):
    """Update feed configuration (subreddits, channels to follow)"""
    config.last_updated = datetime.now(timezone.utc).isoformat()
    
    await db.config.update_one(
        {"id": "default"},
        {"$set": config.dict()},
        upsert=True
    )
    
    # Clear cache to force refresh with new config
    await db.posts.delete_many({})
    
    return {"message": "Configuration updated", "config": config}

@app.post("/api/feed/refresh")
async def refresh_feed():
    """Force refresh feed from all sources"""
    posts = await fetch_and_cache_posts()
    return {"message": "Feed refreshed", "count": len(posts)}

# Helper functions
async def fetch_and_cache_posts():
    """Fetch posts from all connectors and cache them"""
    
    # Get config
    config = await get_config()
    
    all_posts = []
    
    # Fetch from all sources
    try:
        reddit_posts = await reddit.fetch_posts(config.reddit_subreddits)
        all_posts.extend(reddit_posts)
        print(f"✅ Fetched {len(reddit_posts)} posts from Reddit")
    except Exception as e:
        print(f"❌ Error fetching Reddit: {e}")
    
    try:
        youtube_posts = await youtube.fetch_posts(config.youtube_channels)
        all_posts.extend(youtube_posts)
        print(f"✅ Fetched {len(youtube_posts)} posts from YouTube")
    except Exception as e:
        print(f"❌ Error fetching YouTube: {e}")
    
    try:
        instagram_posts = await instagram.fetch_posts(config.instagram_users)
        all_posts.extend(instagram_posts)
        print(f"✅ Fetched {len(instagram_posts)} posts from Instagram")
    except Exception as e:
        print(f"❌ Error fetching Instagram: {e}")
    
    try:
        threads_posts = await threads.fetch_posts(config.threads_users)
        all_posts.extend(threads_posts)
        print(f"✅ Fetched {len(threads_posts)} posts from Threads")
    except Exception as e:
        print(f"❌ Error fetching Threads: {e}")
    
    try:
        twitter_posts = await twitter.fetch_posts(config.twitter_users)
        all_posts.extend(twitter_posts)
        print(f"✅ Fetched {len(twitter_posts)} posts from Twitter")
    except Exception as e:
        print(f"❌ Error fetching Twitter: {e}")
    
    # Clear old cache
    await db.posts.delete_many({})
    
    # Cache new posts
    if all_posts:
        cached_posts = []
        for post in all_posts:
            post_dict = post.copy()
            post_dict['cached_at'] = datetime.now(timezone.utc).isoformat()
            cached_posts.append(post_dict)
        
        await db.posts.insert_many(cached_posts)
    
    return [Post(**post) for post in all_posts]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
