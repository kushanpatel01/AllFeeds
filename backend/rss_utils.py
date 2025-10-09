from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from fastapi.responses import Response

def generate_rss(posts, title="My Unified Feed", description="Combined social media feed"):
    """Generate RSS 2.0 XML from posts"""
    
    rss = Element("rss", version="2.0", nsmap={
        "atom": "http://www.w3.org/2005/Atom"
    })
    
    channel = SubElement(rss, "channel")
    
    # Channel metadata
    channel_title = SubElement(channel, "title")
    channel_title.text = title
    
    channel_desc = SubElement(channel, "description")
    channel_desc.text = description
    
    channel_link = SubElement(channel, "link")
    channel_link.text = "https://unified-feed.local"
    
    # Add posts as items
    for post in posts:
        item = SubElement(channel, "item")
        
        item_title = SubElement(item, "title")
        item_title.text = f"[{post['platform']}] {post['title']}"
        
        item_link = SubElement(item, "link")
        item_link.text = post['link']
        
        item_desc = SubElement(item, "description")
        item_desc.text = post.get('description', '')
        
        item_date = SubElement(item, "pubDate")
        try:
            dt = datetime.fromisoformat(post['date'])
            item_date.text = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except:
            item_date.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        item_category = SubElement(item, "category")
        item_category.text = post['platform']
        
        # Add source info
        item_source = SubElement(item, "source")
        item_source.text = post.get('source', post['platform'])
    
    xml_string = tostring(rss, encoding='unicode', method='xml')
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    
    return Response(
        content=xml_declaration + xml_string,
        media_type="application/rss+xml"
    )
