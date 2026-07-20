from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
        # Look for this in your code:
    data = request.get_json()
    video_url = data.get('url')

    if not video_url:
        return jsonify({'error': 'Please provide a valid URL'}), 400

    # ADD THIS NEW BLOCK RIGHT BELOW IT:
    if 'youtube.com' in video_url or 'youtu.be' in video_url:
        return jsonify({'error': 'YouTube downloads are not supported'}), 403
        

    try:
        ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'cookiefile': '/tmp/cookies.txt', # Or your secure path
    'allowed_extractors': ['default', 'tiktok', 'instagram', 'facebook', 'twitter', 'x'],
}


        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get('title', 'Social_Media_Download')
            
            formats_available = []
            fallback_url = None

            # 1. PROCESS VIDEOS & MULTIPLE QUALITY STREAMS
            if info.get('formats'):
                for f in info['formats']:
                    # Filter out audio-only lines and prioritize direct video streams with formats
                    if f.get('vcodec') != 'none' and f.get('url'):
                        height = f.get('height')
                        if height:
                            label = f"{height}p"
                            # Map standard industry flags cleanly
                            if height >= 1080: label = "HD 1080p"
                            elif height >= 720: label = "HD 720p"
                            elif height >= 480: label = "SD 480p"
                            
                            formats_available.append({
                                'quality': label,
                                'url': f['url'],
                                'type': 'video'
                            })
                
                # Sort resolution hierarchy (highest quality first)
                formats_available = sorted(formats_available, key=lambda x: int(''.join(filter(str.isdigit, x['quality']))), reverse=True)

            # 2. PROCESS CAROUSELS / SLIDESHOW ENTRIES
            if not formats_available and 'entries' in info:
                first_entry = info['entries'][0] if info['entries'] else {}
                if first_entry.get('url'):
                    fallback_url = first_entry.get('url')
                elif first_entry.get('thumbnails'):
                    fallback_url = first_entry.get('thumbnails')[-1].get('url')

            # 3. PROCESS STANDALONE IMAGES / SINGLE FORMAT FALLBACKS
            if not formats_available and not fallback_url:
                fallback_url = info.get('url') or (info.get('thumbnails')[-1].get('url') if info.get('thumbnails') else info.get('thumbnail'))

            # If it's a static image or fallback item, add it as a primary stream
            if not formats_available and fallback_url:
                formats_available.append({
                    'quality': 'High Quality Image',
                    'url': fallback_url,
                    'type': 'image'
                })

            if not formats_available:
                return jsonify({'error': 'Could not extract any content profiles.'}), 400

            return jsonify({
                'success': True,
                'title': title,
                'formats': formats_available
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# NEW PROXY ROUTE: Forces mobile browsers to download the media asset locally inside the application window
@app.route('/proxy-download')
def proxy_download():
    media_url = request.args.get('url')
    filename = request.args.get('title', 'download')
    
    if not media_url:
        return "Missing media target URL", 400

    try:
        # Stream data from the target social media platform CDN
        req = requests.get(media_url, stream=True, timeout=15)
        
        # Strip dangerous formatting structures out of names
        clean_filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in ' ._-']).strip()
        
        # Intercept headers to explicitly instruct mobile clients to perform a file saving sequence
        headers = {
            'Content-Disposition': f'attachment; filename="{clean_filename or "media"}"',
            'Content-Type': req.headers.get('Content-Type', 'application/octet-stream')
        }
        
        return Response(req.iter_content(chunk_size=1024*1024), headers=headers)
    except Exception as e:
        return f"Download stream compilation broke: {str(e)}", 500
