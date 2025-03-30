import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
import logging
import cloudscraper
from playwright.sync_api import sync_playwright
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MediaFire-API")

# Initialize cloudscraper
scraper = cloudscraper.create_scraper()

def get_with_playwright(url):
    """Headless browser fallback using Playwright"""
    try:
        with sync_playwright() as p:
            # Launch browser (Chromium)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            
            # Navigate to URL
            page.goto(url, timeout=15000)
            time.sleep(2)  # Wait for JS execution
            
            # Try to get download button
            download_button = page.query_selector('#downloadButton')
            if download_button:
                link = download_button.get_attribute('href')
                browser.close()
                return (200, link)
            
            # Fallback: Search for download links
            all_links = page.query_selector_all('a')
            for link in all_links:
                href = link.get_attribute('href')
                if href and 'download.mediafire.com' in href:
                    browser.close()
                    return (200, href)
            
            browser.close()
            return (404, None)
            
    except Exception as e:
        logger.error(f"Playwright error: {str(e)}")
        return (500, None)

def get_mediafire_link(url):
    """Primary scraping function with fallbacks"""
    # Attempt 1: Standard scraping
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.mediafire.com/"
        }
        response = scraper.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if download_button := soup.find('a', {'id': 'downloadButton'}):
            return (200, download_button['href'])
        
        # Check for indirect links
        for link in soup.find_all('a', href=True):
            if 'download.mediafire.com' in link['href']:
                return (200, link['href'])
                
    except Exception as e:
        logger.warning(f"Standard scrape failed: {str(e)}")
    
    # Attempt 2: Headless browser fallback
    return get_with_playwright(url)

@app.route('/api/mediafire', methods=['GET'])
def get_direct_link():
    mediafire_url = request.args.get('url')
    if not mediafire_url:
        return jsonify({"error": "URL parameter is required"}), 400
    
    status, link = get_mediafire_link(mediafire_url)
    
    if link:
        return jsonify({
            "status": "success",
            "direct_link": link,
            "method": "playwright" if "playwright" in str(link) else "standard",
            "original_url": mediafire_url
        })
    else:
        return jsonify({
            "status": "error",
            "code": status,
            "message": "Failed after multiple attempts",
            "solution": "MediaFire is blocking automated requests"
        }), status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
