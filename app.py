from flask import Flask, render_template, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    video_url = data.get('url')
    
    if not video_url:
        return jsonify({'error': 'Please provide a valid URL'}), 400

        try:
        # Configuration for yt-dlp to find media links securely
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt',
            'allowed_extractors': ['default', 'youtube', 'tiktok', 'instagram', 'facebook', 'twitter'],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # Initialize download target
            download_url = None
            title = info.get('title', 'Social Media Download')

            # CASE 1: Check for multi-item posts (Instagram Carousels / TikTok Slide Shows)
            if 'entries' in info:
                # Target the first media entry item in the gallery loop
                first_entry = info['entries'][0] if info['entries'] else {}
                download_url = first_entry.get('url') # Try to grab video from item
                
                if not download_url and first_entry.get('thumbnails'):
                    download_url = first_entry.get('thumbnails')[-1].get('url') # Fallback to image from item

            # CASE 2: Single-item posts (Standard Reels, Videos, or Single Image Posts)
            if not download_url:
                download_url = info.get('url') # Grab direct video stream

            # CASE 3: Fallback if it's a standalone image post with no video stream array
            if not download_url and info.get('thumbnails'):
                download_url = info.get('thumbnails')[-1].get('url')

            if not download_url:
                download_url = info.get('thumbnail')

            # Safety validation flag
            if not download_url:
                return jsonify({'error': 'Could not extract any playable video or image from this link.'}), 400

            return jsonify({
                'success': True,
                'title': title,
                'download_url': download_url
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
            
