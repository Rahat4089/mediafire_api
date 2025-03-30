from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse
import http.client
from io import BytesIO
from gzip import GzipFile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MediaFireAPI")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Accept-Encoding": "gzip",
}

app = Flask(__name__)

def get_mediafire_direct_link(mediafire_url):
    """
    Fetch the direct download link from a Mediafire page.
    Returns a tuple of (status_code, direct_link)
    """
    try:
        parsed_url = urllib.parse.urlparse(mediafire_url)
        conn = http.client.HTTPConnection(parsed_url.netloc)
        conn.request("GET", parsed_url.path, headers=HEADERS)
        response = conn.getresponse()

        if response.status != 200:
            return (response.status, None)

        if response.getheader("Content-Encoding") == "gzip":
            compressed_data = response.read()
            with GzipFile(fileobj=BytesIO(compressed_data)) as f:
                html = f.read().decode("utf-8")
        else:
            html = response.read().decode("utf-8")

        soup = BeautifulSoup(html, "html.parser")
        download_button = soup.find("a", {"id": "downloadButton"})
        
        if download_button:
            return (200, download_button.get("href"))
        else:
            return (404, None)
            
    except Exception as e:
        logger.error(f"Error fetching Mediafire link: {e}")
        return (500, None)

@app.route('/api/mediafire', methods=['GET'])
def mediafire_api():
    """
    API endpoint to get MediaFire direct link
    Requires 'url' parameter in the query string
    """
    mediafire_url = request.args.get('url')
    
    if not mediafire_url:
        return jsonify({
            "status": "error",
            "message": "Missing 'url' parameter",
            "data": None
        }), 400
    
    status_code, direct_link = get_mediafire_direct_link(mediafire_url)
    
    if direct_link:
        return jsonify({
            "api made by": "RAHAT",
            "status": "success",
            "response_code": status_code,
            "direct_link": direct_link,
            "original_url": mediafire_url            
        })
    else:
        return jsonify({
            "status": "error",
            "response_code": status_code,
            "message": "Failed to extract direct download link",
            "original_url": mediafire_url
        }), status_code if status_code != 200 else 404

@app.route('/')
def index():
    return """
    <h1>MediaFire Direct Link API</h1>
    <p>Send a GET request to <code>/api/mediafire?url=YOUR_MEDIAFIRE_URL</code></p>
    <p>Example: <a href="/api/mediafire?url=https://www.mediafire.com/file/kd2mk0cdg8sdlek/AnimeXin.dev_btth_s5_ep_140_eng.mp4/file">/api/mediafire?url=https://www.mediafire.com/file/kd2mk0cdg8sdlek/AnimeXin.dev_btth_s5_ep_140_eng.mp4/file</a></p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)