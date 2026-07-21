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

    if 'youtube.com' in video_url or 'youtu.be' in video_url:
        return jsonify({'error': 'YouTube downloads are not supported'}), 403

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'cookiefile': '/tmp/cookies.txt',
            'allowed_extractors': ['default', 'tiktok', 'instagram', 'facebook', 'twitter', 'x'],
            'format': 'best/bestvideo+bestaudio',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get('title', 'Social_Media_Download')

        formats_available = []
        seen_urls = set()

        if info.get('formats'):
            for f in info['formats']:
                # Only grab formats that have both a video codec and an audio codec, or safe single streams
                if f.get('url') and f.get('vcodec') != 'none':
                    # Skip video-only tracks to prevent silent downloads on X and Instagram
                    if f.get('acodec') == 'none' and 'tiktok' not in video_url and 'twitter' not in video_url:
                        continue

                    f_url = f['url']
                    if f_url in seen_urls:
                        continue
                    seen_urls.add(f_url)

                    height = f.get('height')
                    if height and isinstance(height, int):
                        if height >= 1080: label = "HD 1080p"
                        elif height >= 720: label = "HD 720p"
                        elif height >= 480: label = "SD 480p"
                        else: label = f"{height}p"
                    else:
                        label = "HD Video"

                    formats_available.append({
                        'quality': label,
                        'url': f_url,
                        'type': 'video'
                    })

        # Universal fallback stream if formats list is empty
        if not formats_available and info.get('url'):
            formats_available.append({
                'quality': 'HD Video',
                'url': info.get('url'),
                'type': 'video'
            })

        if not formats_available and 'entries' in info:
            for entry in info['entries']:
                if entry.get('url'):
                    formats_available.append({
                        'quality': 'Media Item',
                        'url': entry.get('url'),
                        'type': 'video'
                    })

        if not formats_available:
            return jsonify({'error': 'Could not extract a valid media stream. Try another link.'}), 400

        return jsonify({
            'success': True,
            'title': title,
            'formats': formats_available
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
        
