#!/usr/bin/env python3
"""
Backend API Testing for My Unified Feed
Tests all backend endpoints thoroughly
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import os

# Get backend URL from frontend environment
BACKEND_URL = "https://feedhub-5.preview.emergentagent.com/api"

class UnifiedFeedTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_health_endpoint(self):
        """Test GET /api/health"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "healthy":
                    self.log_test("Health Check", True, "Health endpoint working correctly", 
                                {"status_code": response.status_code, "response": data})
                else:
                    self.log_test("Health Check", False, "Invalid health response format", 
                                {"status_code": response.status_code, "response": data})
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}", 
                            {"status_code": response.status_code, "response": response.text})
                
        except Exception as e:
            self.log_test("Health Check", False, f"Request failed: {str(e)}")
    
    def test_feed_endpoint_basic(self):
        """Test GET /api/feed without parameters"""
        try:
            response = self.session.get(f"{self.base_url}/feed", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    if len(data) > 0:
                        # Check post structure
                        post = data[0]
                        required_fields = ["id", "title", "link", "platform", "source", "date"]
                        missing_fields = [field for field in required_fields if field not in post]
                        
                        if not missing_fields:
                            platforms = set(post["platform"] for post in data)
                            self.log_test("Feed Basic", True, f"Retrieved {len(data)} posts from platforms: {platforms}", 
                                        {"post_count": len(data), "platforms": list(platforms), "sample_post": data[0]})
                        else:
                            self.log_test("Feed Basic", False, f"Posts missing required fields: {missing_fields}", 
                                        {"missing_fields": missing_fields, "sample_post": post})
                    else:
                        self.log_test("Feed Basic", False, "No posts returned from feed", 
                                    {"response": data})
                else:
                    self.log_test("Feed Basic", False, "Feed response is not a list", 
                                {"response_type": type(data), "response": data})
            else:
                self.log_test("Feed Basic", False, f"HTTP {response.status_code}", 
                            {"status_code": response.status_code, "response": response.text})
                
        except Exception as e:
            self.log_test("Feed Basic", False, f"Request failed: {str(e)}")
    
    def test_feed_platform_filter(self):
        """Test GET /api/feed with platform filter"""
        platforms_to_test = ["Reddit", "YouTube", "Instagram", "Threads", "Twitter", "Placeholder"]
        
        for platform in platforms_to_test:
            try:
                response = self.session.get(f"{self.base_url}/feed?platform={platform}", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        if len(data) > 0:
                            # Verify all posts are from the requested platform
                            wrong_platform = [post for post in data if post["platform"] != platform]
                            if not wrong_platform:
                                self.log_test(f"Feed Filter - {platform}", True, 
                                            f"Retrieved {len(data)} posts from {platform}", 
                                            {"post_count": len(data), "platform": platform})
                            else:
                                self.log_test(f"Feed Filter - {platform}", False, 
                                            f"Found {len(wrong_platform)} posts from wrong platform", 
                                            {"wrong_posts": wrong_platform[:3]})
                        else:
                            # Empty result is acceptable for some platforms
                            self.log_test(f"Feed Filter - {platform}", True, 
                                        f"No posts found for {platform} (acceptable)", 
                                        {"post_count": 0, "platform": platform})
                    else:
                        self.log_test(f"Feed Filter - {platform}", False, "Response is not a list", 
                                    {"response_type": type(data), "response": data})
                else:
                    self.log_test(f"Feed Filter - {platform}", False, f"HTTP {response.status_code}", 
                                {"status_code": response.status_code, "response": response.text})
                    
            except Exception as e:
                self.log_test(f"Feed Filter - {platform}", False, f"Request failed: {str(e)}")
    
    def test_feed_keyword_filter(self):
        """Test GET /api/feed with keyword filter"""
        keywords_to_test = ["python", "programming", "technology"]
        
        for keyword in keywords_to_test:
            try:
                response = self.session.get(f"{self.base_url}/feed?keyword={keyword}", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        if len(data) > 0:
                            # Verify all posts contain the keyword in title
                            no_keyword = [post for post in data if keyword.lower() not in post["title"].lower()]
                            if not no_keyword:
                                self.log_test(f"Feed Keyword - {keyword}", True, 
                                            f"Retrieved {len(data)} posts containing '{keyword}'", 
                                            {"post_count": len(data), "keyword": keyword})
                            else:
                                self.log_test(f"Feed Keyword - {keyword}", False, 
                                            f"Found {len(no_keyword)} posts without keyword", 
                                            {"posts_without_keyword": no_keyword[:3]})
                        else:
                            self.log_test(f"Feed Keyword - {keyword}", True, 
                                        f"No posts found for keyword '{keyword}' (acceptable)", 
                                        {"post_count": 0, "keyword": keyword})
                    else:
                        self.log_test(f"Feed Keyword - {keyword}", False, "Response is not a list", 
                                    {"response_type": type(data), "response": data})
                else:
                    self.log_test(f"Feed Keyword - {keyword}", False, f"HTTP {response.status_code}", 
                                {"status_code": response.status_code, "response": response.text})
                    
            except Exception as e:
                self.log_test(f"Feed Keyword - {keyword}", False, f"Request failed: {str(e)}")
    
    def test_feed_refresh_parameter(self):
        """Test GET /api/feed with refresh=true"""
        try:
            response = self.session.get(f"{self.base_url}/feed?refresh=true", timeout=45)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Feed Refresh Parameter", True, 
                                f"Refresh parameter working, retrieved {len(data)} posts", 
                                {"post_count": len(data)})
                else:
                    self.log_test("Feed Refresh Parameter", False, "Response is not a list", 
                                {"response_type": type(data), "response": data})
            else:
                self.log_test("Feed Refresh Parameter", False, f"HTTP {response.status_code}", 
                            {"status_code": response.status_code, "response": response.text})
                
        except Exception as e:
            self.log_test("Feed Refresh Parameter", False, f"Request failed: {str(e)}")
    
    def test_rss_endpoint(self):
        """Test GET /api/feed/rss"""
        try:
            response = self.session.get(f"{self.base_url}/feed/rss", timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'xml' in content_type.lower() or 'rss' in content_type.lower():
                    try:
                        # Parse XML to verify it's valid RSS
                        root = ET.fromstring(response.text)
                        
                        # Check RSS structure
                        if root.tag == 'rss' and root.get('version') == '2.0':
                            channel = root.find('channel')
                            if channel is not None:
                                title = channel.find('title')
                                items = channel.findall('item')
                                
                                self.log_test("RSS Export", True, 
                                            f"Valid RSS 2.0 XML with {len(items)} items", 
                                            {"item_count": len(items), "title": title.text if title is not None else "No title"})
                            else:
                                self.log_test("RSS Export", False, "RSS missing channel element", 
                                            {"xml_preview": response.text[:500]})
                        else:
                            self.log_test("RSS Export", False, f"Invalid RSS format: {root.tag}", 
                                        {"root_tag": root.tag, "version": root.get('version')})
                            
                    except ET.ParseError as e:
                        self.log_test("RSS Export", False, f"Invalid XML: {str(e)}", 
                                    {"xml_preview": response.text[:500]})
                else:
                    self.log_test("RSS Export", False, f"Wrong content type: {content_type}", 
                                {"content_type": content_type, "response_preview": response.text[:200]})
            else:
                self.log_test("RSS Export", False, f"HTTP {response.status_code}", 
                            {"status_code": response.status_code, "response": response.text})
                
        except Exception as e:
            self.log_test("RSS Export", False, f"Request failed: {str(e)}")
    
    def test_rss_with_filters(self):
        """Test GET /api/feed/rss with platform and keyword filters"""
        test_cases = [
            {"platform": "Reddit"},
            {"keyword": "python"},
            {"platform": "YouTube", "keyword": "programming"}
        ]
        
        for i, params in enumerate(test_cases):
            try:
                param_str = "&".join([f"{k}={v}" for k, v in params.items()])
                response = self.session.get(f"{self.base_url}/feed/rss?{param_str}", timeout=30)
                
                if response.status_code == 200:
                    try:
                        root = ET.fromstring(response.text)
                        if root.tag == 'rss':
                            channel = root.find('channel')
                            items = channel.findall('item') if channel is not None else []
                            
                            self.log_test(f"RSS Filter {i+1}", True, 
                                        f"RSS with filters working, {len(items)} items", 
                                        {"filters": params, "item_count": len(items)})
                        else:
                            self.log_test(f"RSS Filter {i+1}", False, "Invalid RSS format", 
                                        {"filters": params, "root_tag": root.tag})
                    except ET.ParseError as e:
                        self.log_test(f"RSS Filter {i+1}", False, f"Invalid XML: {str(e)}", 
                                    {"filters": params})
                else:
                    self.log_test(f"RSS Filter {i+1}", False, f"HTTP {response.status_code}", 
                                {"filters": params, "status_code": response.status_code})
                    
            except Exception as e:
                self.log_test(f"RSS Filter {i+1}", False, f"Request failed: {str(e)}", 
                            {"filters": params})
    
    def test_refresh_endpoint(self):
        """Test POST /api/feed/refresh"""
        try:
            response = self.session.post(f"{self.base_url}/feed/refresh", timeout=45)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "count" in data:
                    self.log_test("Feed Refresh", True, 
                                f"Refresh successful, {data['count']} posts", 
                                {"response": data})
                else:
                    self.log_test("Feed Refresh", False, "Invalid refresh response format", 
                                {"response": data})
            else:
                self.log_test("Feed Refresh", False, f"HTTP {response.status_code}", 
                            {"status_code": response.status_code, "response": response.text})
                
        except Exception as e:
            self.log_test("Feed Refresh", False, f"Request failed: {str(e)}")
    
    def test_config_get(self):
        """Test GET /api/config"""
        try:
            response = self.session.get(f"{self.base_url}/config", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["reddit_subreddits", "youtube_channels", "instagram_users", "threads_users", "twitter_users", "last_updated"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Config Get", True, "Configuration retrieved successfully", 
                                {"config": data})
                else:
                    self.log_test("Config Get", False, f"Config missing fields: {missing_fields}", 
                                {"missing_fields": missing_fields, "config": data})
            else:
                self.log_test("Config Get", False, f"HTTP {response.status_code}", 
                            {"status_code": response.status_code, "response": response.text})
                
        except Exception as e:
            self.log_test("Config Get", False, f"Request failed: {str(e)}")
    
    def test_config_post(self):
        """Test POST /api/config"""
        test_config = {
            "id": "default",
            "reddit_subreddits": ["python", "programming", "webdev"],
            "youtube_channels": ["UC_x5XG1OV2P6uZZ5FSM9Ttw"],
            "instagram_users": ["natgeo", "nasa"],
            "threads_users": ["zuck"],
            "twitter_users": ["elonmusk", "openai"],
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            response = self.session.post(f"{self.base_url}/config", 
                                       json=test_config, 
                                       headers={"Content-Type": "application/json"},
                                       timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "config" in data:
                    self.log_test("Config Update", True, "Configuration updated successfully", 
                                {"response": data})
                else:
                    self.log_test("Config Update", False, "Invalid config update response", 
                                {"response": data})
            else:
                self.log_test("Config Update", False, f"HTTP {response.status_code}", 
                            {"status_code": response.status_code, "response": response.text})
                
        except Exception as e:
            self.log_test("Config Update", False, f"Request failed: {str(e)}")
    
    def test_feed_metadata_endpoint(self):
        """Test GET /api/feed/metadata"""
        try:
            response = self.session.get(f"{self.base_url}/feed/metadata", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_posts", "last_updated", "cache_ttl_minutes", "config_updated"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Feed Metadata", True, "Metadata endpoint working correctly", 
                                {"metadata": data})
                else:
                    self.log_test("Feed Metadata", False, f"Metadata missing fields: {missing_fields}", 
                                {"missing_fields": missing_fields, "metadata": data})
            else:
                self.log_test("Feed Metadata", False, f"HTTP {response.status_code}", 
                            {"status_code": response.status_code, "response": response.text})
                
        except Exception as e:
            self.log_test("Feed Metadata", False, f"Request failed: {str(e)}")
    
    def test_feed_pagination(self):
        """Test GET /api/feed with pagination parameters"""
        test_cases = [
            {"page": 1, "limit": 20},
            {"page": 2, "limit": 10},
            {"page": 1, "limit": 5}
        ]
        
        for i, params in enumerate(test_cases):
            try:
                param_str = "&".join([f"{k}={v}" for k, v in params.items()])
                response = self.session.get(f"{self.base_url}/feed?{param_str}", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        expected_max = params["limit"]
                        actual_count = len(data)
                        
                        if actual_count <= expected_max:
                            self.log_test(f"Feed Pagination {i+1}", True, 
                                        f"Pagination working, got {actual_count} posts (limit: {expected_max})", 
                                        {"params": params, "post_count": actual_count})
                        else:
                            self.log_test(f"Feed Pagination {i+1}", False, 
                                        f"Too many posts returned: {actual_count} > {expected_max}", 
                                        {"params": params, "post_count": actual_count})
                    else:
                        self.log_test(f"Feed Pagination {i+1}", False, "Response is not a list", 
                                    {"params": params, "response_type": type(data)})
                else:
                    self.log_test(f"Feed Pagination {i+1}", False, f"HTTP {response.status_code}", 
                                {"params": params, "status_code": response.status_code})
                    
            except Exception as e:
                self.log_test(f"Feed Pagination {i+1}", False, f"Request failed: {str(e)}", 
                            {"params": params})
    
    def test_rsshub_connectors(self):
        """Test RSSHub connector endpoints directly"""
        rsshub_tests = [
            ("Instagram RSSHub", "https://rsshub.app/instagram/user/natgeo"),
            ("Threads RSSHub", "https://rsshub.app/threads/user/zuck"),
            ("Twitter RSSHub", "https://rsshub.app/twitter/user/elonmusk")
        ]
        
        for name, url in rsshub_tests:
            try:
                response = requests.get(url, timeout=20)
                if response.status_code == 200:
                    # Try to parse as RSS/XML
                    try:
                        root = ET.fromstring(response.text)
                        if 'rss' in root.tag.lower() or 'feed' in root.tag.lower():
                            self.log_test(f"RSSHub - {name}", True, "RSSHub endpoint accessible and returns valid feed", 
                                        {"url": url, "status_code": response.status_code})
                        else:
                            self.log_test(f"RSSHub - {name}", False, f"Invalid feed format: {root.tag}", 
                                        {"url": url, "root_tag": root.tag})
                    except ET.ParseError:
                        # Some RSSHub endpoints might return JSON or other formats
                        self.log_test(f"RSSHub - {name}", True, "RSSHub endpoint accessible (non-XML response)", 
                                    {"url": url, "status_code": response.status_code, "note": "May be rate limited or different format"})
                else:
                    self.log_test(f"RSSHub - {name}", False, f"HTTP {response.status_code}", 
                                {"url": url, "status_code": response.status_code, "note": "RSSHub may be rate limited"})
            except Exception as e:
                self.log_test(f"RSSHub - {name}", False, f"Request failed: {str(e)}", 
                            {"url": url, "note": "RSSHub public instance may be unavailable"})
    
    def test_external_feed_sources(self):
        """Test if external RSS feeds (Reddit, YouTube) are accessible"""
        external_tests = [
            ("Reddit RSS", "https://www.reddit.com/r/python/.rss"),
            ("YouTube RSS", "https://www.youtube.com/feeds/videos.xml?channel_id=UC_x5XG1OV2P6uZZ5FSM9Ttw")
        ]
        
        for name, url in external_tests:
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    self.log_test(f"External - {name}", True, "External feed accessible", 
                                {"url": url, "status_code": response.status_code})
                else:
                    self.log_test(f"External - {name}", False, f"HTTP {response.status_code}", 
                                {"url": url, "status_code": response.status_code})
            except Exception as e:
                self.log_test(f"External - {name}", False, f"Request failed: {str(e)}", 
                            {"url": url})
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"🧪 Starting My Unified Feed Backend Tests")
        print(f"🔗 Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Test in order of priority
        self.test_health_endpoint()
        self.test_external_feed_sources()
        self.test_rsshub_connectors()
        self.test_feed_endpoint_basic()
        self.test_feed_platform_filter()
        self.test_feed_keyword_filter()
        self.test_feed_refresh_parameter()
        self.test_feed_pagination()
        self.test_feed_metadata_endpoint()
        self.test_rss_endpoint()
        self.test_rss_with_filters()
        self.test_refresh_endpoint()
        self.test_config_get()
        self.test_config_post()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        failed = len(self.test_results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['message']}")
        
        return self.test_results

if __name__ == "__main__":
    tester = UnifiedFeedTester()
    results = tester.run_all_tests()