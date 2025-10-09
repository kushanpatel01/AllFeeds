import React, { useState, useEffect } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

function App() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPlatform, setSelectedPlatform] = useState('all');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [metadata, setMetadata] = useState(null);
  const [showCopyToast, setShowCopyToast] = useState(false);

  const platformIcons = {
    'Reddit': '🔴',
    'YouTube': '📺',
    'Twitter': '🐦',
    'Instagram': '📷',
    'Threads': '🧵',
    'Facebook': '👥',
    'Placeholder': '⚙️'
  };

  const platformColors = {
    'Reddit': '#FF4500',
    'YouTube': '#FF0000',
    'Twitter': '#1DA1F2',
    'Instagram': '#E4405F',
    'Threads': '#000000',
    'Facebook': '#1877F2',
    'Placeholder': '#6B7280'
  };

  useEffect(() => {
    fetchFeed();
    fetchMetadata();
  }, []);

  const fetchFeed = async (refresh = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (refresh) params.append('refresh', 'true');
      params.append('limit', '100'); // Fetch more posts
      
      const response = await fetch(`${BACKEND_URL}/api/feed?${params}`);
      if (!response.ok) throw new Error('Failed to fetch feed');
      
      const data = await response.json();
      setPosts(data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching feed:', err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  const fetchMetadata = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/feed/metadata`);
      if (!response.ok) throw new Error('Failed to fetch metadata');
      const data = await response.json();
      setMetadata(data);
    } catch (err) {
      console.error('Error fetching metadata:', err);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await fetch(`${BACKEND_URL}/api/feed/refresh`, { method: 'POST' });
      await fetchFeed(true);
    } catch (err) {
      setError('Failed to refresh feed');
      setIsRefreshing(false);
    }
  };

  const handleExportRSS = () => {
    const params = new URLSearchParams();
    if (selectedPlatform !== 'all') params.append('platform', selectedPlatform);
    if (searchKeyword) params.append('keyword', searchKeyword);
    
    window.open(`${BACKEND_URL}/api/feed/rss?${params}`, '_blank');
  };

  const filteredPosts = posts.filter(post => {
    const platformMatch = selectedPlatform === 'all' || post.platform === selectedPlatform;
    const keywordMatch = !searchKeyword || post.title.toLowerCase().includes(searchKeyword.toLowerCase());
    return platformMatch && keywordMatch;
  });

  const platforms = ['all', ...new Set(posts.map(p => p.platform))];

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    } catch {
      return 'Recently';
    }
  };

  return (
    <div className="App">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1 className="title">
            <span className="icon">📡</span>
            My Unified Feed
          </h1>
          <p className="subtitle">Your personalized social media aggregator</p>
        </div>
      </header>

      {/* Controls */}
      <div className="controls">
        <div className="controls-left">
          {/* Platform Filter */}
          <div className="filter-group">
            <label htmlFor="platform-filter">Platform:</label>
            <select
              id="platform-filter"
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(e.target.value)}
              className="filter-select"
            >
              {platforms.map(platform => (
                <option key={platform} value={platform}>
                  {platform === 'all' ? 'All Platforms' : platform}
                </option>
              ))}
            </select>
          </div>

          {/* Search */}
          <div className="filter-group">
            <label htmlFor="search">Search:</label>
            <input
              id="search"
              type="text"
              placeholder="Filter by keyword..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="search-input"
            />
          </div>
        </div>

        <div className="controls-right">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="btn btn-secondary"
          >
            {isRefreshing ? '🔄 Refreshing...' : '🔄 Refresh'}
          </button>
          <button
            onClick={handleExportRSS}
            className="btn btn-primary"
          >
            📰 Export RSS
          </button>
        </div>
      </div>

      {/* Feed */}
      <main className="feed-container">
        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading your feed...</p>
          </div>
        )}

        {error && (
          <div className="error">
            <p>❌ Error: {error}</p>
            <button onClick={() => fetchFeed()} className="btn btn-secondary">
              Try Again
            </button>
          </div>
        )}

        {!loading && !error && filteredPosts.length === 0 && (
          <div className="empty-state">
            <p className="empty-icon">📭</p>
            <h3>No posts found</h3>
            <p>Try adjusting your filters or refresh the feed</p>
          </div>
        )}

        {!loading && !error && filteredPosts.length > 0 && (
          <div className="posts">
            <div className="posts-header">
              <h2>{filteredPosts.length} posts</h2>
            </div>
            {filteredPosts.map((post, index) => (
              <article key={`${post.id}-${index}`} className="post-card">
                <div className="post-header">
                  <span
                    className="platform-badge"
                    style={{ borderColor: platformColors[post.platform] }}
                  >
                    <span className="platform-icon">
                      {platformIcons[post.platform] || '📄'}
                    </span>
                    {post.platform}
                  </span>
                  <span className="post-date">{formatDate(post.date)}</span>
                </div>
                
                <h3 className="post-title">
                  <a
                    href={post.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="post-link"
                  >
                    {post.title}
                  </a>
                </h3>
                
                {post.description && (
                  <p className="post-description">{post.description}</p>
                )}
                
                <div className="post-footer">
                  <span className="post-source">📍 {post.source}</span>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>Built with ❤️ using React + FastAPI + MongoDB</p>
        <p className="footer-note">
          Privacy-focused • Local caching • No data collection
        </p>
      </footer>
    </div>
  );
}

export default App;
