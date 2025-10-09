# My Unified Feed 🛰️

**A lightweight, privacy-focused personal social media aggregator**

Combine feeds from Reddit, YouTube, and other platforms into a single unified feed with RSS export support for use in Brave News or any RSS reader.

## ✨ Features

- **Unified Feed**: View all your social media content in one place
- **Multiple Platforms**: Reddit, YouTube (with placeholders for Threads, Instagram, X/Twitter, Facebook)
- **Smart Filtering**: Filter by platform or search by keyword
- **RSS Export**: Generate RSS feeds compatible with Brave News and other RSS readers
- **Privacy-First**: No data collection, all tokens stored locally in MongoDB
- **Fast Caching**: 10-minute intelligent caching for optimal performance
- **Beautiful UI**: Clean, dark-themed, responsive interface
- **Modular Architecture**: Easy to add new platform connectors

## 🏗️ Architecture

```
my_unified_feed/
├── backend/
│   ├── server.py              # FastAPI application
│   ├── connectors/
│   │   ├── reddit.py          # Reddit RSS connector
│   │   ├── youtube.py         # YouTube RSS connector
│   │   └── placeholder.py     # Future platforms placeholder
│   └── rss_utils.py           # RSS 2.0 XML generator
├── frontend/
│   └── src/
│       ├── App.js             # React main component
│       └── App.css            # Dark theme styles
├── Dockerfile                 # Container deployment
└── README.md                  # This file
```

## 🚀 Quick Start

### Option 1: Local Development (Already Running)

The app is already running in this environment:

- **Frontend**: https://feedhub-5.preview.emergentagent.com
- **Backend API**: https://feedhub-5.preview.emergentagent.com/api
- **RSS Feed**: https://feedhub-5.preview.emergentagent.com/api/feed/rss

### Option 2: Docker Deployment

```bash
# Build the Docker image
docker build -t my-unified-feed .

# Run the container
docker run -d -p 8080:8080 -p 3000:3000 --name unified-feed my-unified-feed

# Access the app
open http://localhost:3000
```

### Option 3: Manual Setup

**Prerequisites:**
- Python 3.12+
- Node.js 18+
- MongoDB

**Backend Setup:**
```bash
cd backend
pip install -r requirements.txt
python server.py
```

**Frontend Setup:**
```bash
cd frontend
yarn install
yarn start
```

## 📡 API Endpoints

### Get Unified Feed
```bash
GET /api/feed

# Query parameters:
# - platform: Filter by platform (Reddit, YouTube, etc.)
# - keyword: Search in post titles
# - refresh: Force refresh from sources (true/false)

Example: /api/feed?platform=Reddit&keyword=python
```

### Export RSS Feed
```bash
GET /api/feed/rss

# Generates RSS 2.0 XML
# Supports same filters as /api/feed

Example: /api/feed/rss?platform=YouTube
```

### Refresh Feed
```bash
POST /api/feed/refresh

# Force refresh from all sources and clear cache
```

### Configuration
```bash
GET /api/config          # Get current configuration
POST /api/config         # Update configuration

# Configuration structure:
{
  "reddit_subreddits": ["python", "programming", "technology"],
  "youtube_channels": ["UC_x5XG1OV2P6uZZ5FSM9Ttw"]
}
```

## 🔌 Adding New Sources

### Adding Reddit Subreddits

**Via API:**
```bash
curl -X POST https://feedhub-5.preview.emergentagent.com/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "id": "default",
    "reddit_subreddits": ["python", "webdev", "machinelearning"],
    "youtube_channels": ["UC_x5XG1OV2P6uZZ5FSM9Ttw"]
  }'
```

**Via Code:**
Edit `/app/backend/server.py` and modify the default configuration in `FeedConfig` class.

### Adding YouTube Channels

1. Get the channel ID from YouTube channel URL:
   - Example: `https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw`
   - Channel ID: `UC_x5XG1OV2P6uZZ5FSM9Ttw`

2. Add to configuration via API or code (same as Reddit above)

### Creating New Platform Connectors

Create a new file in `/app/backend/connectors/` following this template:

```python
import feedparser
from datetime import datetime
import asyncio

async def fetch_posts(source_ids):
    """Fetch posts from your platform"""
    posts = []
    
    for source_id in source_ids:
        try:
            # Fetch from RSS feed or API
            url = f"https://example.com/feeds/{source_id}"
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, url)
            
            for entry in feed.entries:
                posts.append({
                    "id": entry.get('id', entry.link),
                    "title": entry.title,
                    "link": entry.link,
                    "platform": "YourPlatform",
                    "source": f"Source: {source_id}",
                    "date": datetime(*entry.published_parsed[:6]).isoformat(),
                    "description": entry.get('summary', '')[:200]
                })
        except Exception as e:
            print(f"Error fetching from {source_id}: {e}")
    
    return posts
```

Then add it to `server.py`:

```python
from connectors import reddit, youtube, placeholder, yourplatform

# In fetch_and_cache_posts function:
try:
    new_posts = await yourplatform.fetch_posts(config.your_platform_ids)
    all_posts.extend(new_posts)
except Exception as e:
    print(f"Error fetching YourPlatform: {e}")
```

## 🌐 Using RSS Bridge Services

For platforms without public RSS feeds (Instagram, Twitter/X, Threads, Facebook), you can use:

### RSSHub

1. **Self-hosted:**
   ```bash
   docker run -d --name rsshub -p 1200:1200 diygod/rsshub
   ```

2. **Use in connector:**
   ```python
   url = f"http://localhost:1200/instagram/user/{username}"
   ```

### RSSBridge

1. **Self-hosted:**
   ```bash
   docker run -d --name rssbridge -p 3000:80 rssbridge/rss-bridge
   ```

2. **Use in connector:**
   ```python
   url = f"http://localhost:3000/?action=display&bridge=Twitter&username={username}&format=Atom"
   ```

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```bash
MONGO_URL=mongodb://localhost:27017
```

**Frontend (.env):**
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

### MongoDB Collections

- `posts`: Cached feed posts (10-minute TTL)
- `config`: Feed configuration (subreddits, channels)
- `user_sessions`: (Future) User authentication data

## 📱 Use with Brave News

1. Open Brave browser
2. Go to `brave://news`
3. Click "Customize sources"
4. Add your RSS feed URL:
   ```
   https://feedhub-5.preview.emergentagent.com/api/feed/rss
   ```
5. Optionally filter by platform or keyword:
   ```
   https://feedhub-5.preview.emergentagent.com/api/feed/rss?platform=Reddit
   ```

## 🎨 Customization

### Changing the Theme

Edit `/app/frontend/src/App.css`:

```css
/* Main background */
body {
  background-color: #0f1419;  /* Change to your color */
}

/* Primary accent color */
.btn-primary {
  background-color: #1d9bf0;  /* Change to your brand color */
}
```

### Adding Platform Icons

Edit `/app/frontend/src/App.js`:

```javascript
const platformIcons = {
  'Reddit': '🔴',
  'YouTube': '📺',
  'YourPlatform': '🆕',  // Add your icon
  // ...
};

const platformColors = {
  'Reddit': '#FF4500',
  'YouTube': '#FF0000',
  'YourPlatform': '#00FF00',  // Add your color
  // ...
};
```

## 🐛 Troubleshooting

### Feed not updating
```bash
# Force refresh
curl -X POST https://feedhub-5.preview.emergentagent.com/api/feed/refresh

# Or click "Refresh" button in UI
```

### External feeds not accessible
```bash
# Test Reddit RSS feed directly
curl https://www.reddit.com/r/python/.rss

# Test YouTube RSS feed
curl https://www.youtube.com/feeds/videos.xml?channel_id=UC_x5XG1OV2P6uZZ5FSM9Ttw
```

### Backend errors
```bash
# Check backend logs
tail -f /var/log/supervisor/backend.*.log

# Restart backend
sudo supervisorctl restart backend
```

### Frontend not loading
```bash
# Check frontend logs
tail -f /var/log/supervisor/frontend.*.log

# Restart frontend
sudo supervisorctl restart frontend
```

## 📊 Current Status

✅ **Working:**
- Reddit feed integration (77+ posts)
- YouTube feed integration (15+ posts)
- Unified feed aggregation
- Platform and keyword filtering
- RSS 2.0 XML export
- MongoDB caching (10-minute TTL)
- Beautiful dark-themed UI
- Responsive design
- Configuration management

🚧 **Coming Soon:**
- Instagram integration (via RSSHub)
- Threads integration (via RSSHub)
- X/Twitter integration (via RSSBridge)
- Facebook integration (via RSSBridge)
- User authentication (multi-user support)
- Favorites/bookmarks
- Read/unread status
- Custom feed sorting options

## 🔒 Privacy & Security

- **No data collection**: All data stays local
- **No tracking**: No analytics or telemetry
- **No third-party cookies**: Pure RSS aggregation
- **Local storage**: MongoDB runs locally
- **Open source**: Full transparency

## 🤝 Contributing

### Adding a new platform connector:

1. Create connector file in `/app/backend/connectors/`
2. Follow the template above
3. Import in `server.py`
4. Update `fetch_and_cache_posts()` function
5. Test with the testing agent

### Improving the UI:

1. Edit `/app/frontend/src/App.js` or `App.css`
2. Test responsiveness on mobile
3. Ensure dark theme consistency

## 📄 License

MIT License - feel free to use, modify, and distribute!

## 💡 Tips

- **Performance**: Increase cache TTL in `server.py` if feeds update slowly
- **Privacy**: Run locally or on a private VPS
- **RSS Readers**: Works with Feedly, Inoreader, NewsBlur, Brave News
- **Mobile**: Fully responsive design works on all devices
- **API**: Use the API to integrate with other tools

## 🙏 Acknowledgments

- Built with FastAPI, React, and MongoDB
- RSS parsing via feedparser
- Icons from Unicode emoji set
- Dark theme inspired by Twitter/X

---

**Made with ❤️ using React + FastAPI + MongoDB**

*Privacy-focused • Local caching • No data collection*
