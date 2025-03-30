import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
import logging
import cloudscraper  # Bypasses Cloudflare

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MediaFire-API")

# Use cloudscraper to bypass Cloudflare
scraper = cloudscraper.create_scraper()

def get_mediafire_direct_link(url):
    try:
        # First attempt: Standard request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.mediafire.com/",
        }
        
        response = scraper.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        download_button = soup.find('a', {'id': 'downloadButton'})
        
        if download_button:
            return (200, download_button['href'])
        
        # Fallback: Check for indirect link
        for link in soup.find_all('a'):
            if 'download.mediafire.com' in str(link.get('href', '')):
                return (200, link['href'])
                
        return (403, None)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return (500, None)

@app.route('/api/mediafire', methods=['GET'])
def api_handler():
    mediafire_url = request.args.get('url')
    if not mediafire_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400
    
    status_code, direct_link = get_mediafire_direct_link(mediafire_url)
    
    if direct_link:
        return jsonify({
            "status": "success",
            "direct_link": direct_link,
            "original_url": mediafire_url
        })
    else:
        return jsonify({
            "status": "error",
            "code": status_code,
            "message": "Failed to extract link (MediaFire may be blocking this request)",
            "solution": "Try again later or use a proxy/VPN"
        }), status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
