from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import requests
import os

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
            'format': 'best',  # Forces selection of combined streams with audio included
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get('title', 'Social_Media_Download')

        formats_available = []
        fallback_url = None

        if info.get('formats'):
            for f in info['formats']:
                # Filter for valid video streams that include audio or standard combined formats
                if f.get('vcodec') != 'none' and f.get('url'):
                    height = f.get('height')
                    if height:
                        label = f"{height}p"
                        if height >= 1080: label = "HD 1080p"
                        elif height >= 720: label = "HD 720p"
                        elif height >= 480: label = "SD 480p"

                        formats_available.append({
                            'quality': label,
                            'url': f['url'],
                            'type': 'video'
                        })

            # Remove duplicate qualities to keep the list clean and fast
            seen_qualities = set()
            unique_formats = []
            for item in sorted(formats_available, key=lambda x: int(''.join(filter(str.isdigit, x['quality'])) or 0), reverse=True):
                if item['quality'] not in seen_qualities:
                    seen_qualities.add(item['quality'])
                    unique_formats.append(item)
            formats_available = unique_formats

        if not formats_available and 'entries' in info:
            first_entry = info['entries'][0] if info['entries'] else {}
            if first_entry.get('url'):
                fallback_url = first_entry.get('url')
            elif first_entry.get('thumbnails'):
                fallback_url = first_entry.get('thumbnails')[-1].get('url')

        if not formats_available and not fallback_url:
            fallback_url = info.get('url') or (info.get('thumbnails')[-1].get('url') if info.get('thumbnails') else None)

        if not formats_available and fallback_url:
            formats_available.append({
                'quality': 'High Quality Image',
                'url': fallback_url,
                'type': 'image'
            })

        if not formats_available:
            return jsonify({'error': 'Could not extract any content profiles.'}, 400)

        return jsonify({
            'success': True,
            'title': title,
            'formats': formats_available
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/proxy-download')
def proxy_download():
    media_url = request.args.get('url')
    filename = request.args.get('title', 'download')

    if not media_url:
        return "Missing media target URL", 400

    try:
        req = requests.get(media_url, stream=True, timeout=15)
        clean_filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in '._-']).strip()
        
        headers = {
            'Content-Disposition': f'attachment; filename="{clean_filename or "media"}.mp4";',
            'Content-Type': req.headers.get('Content-Type', 'video/mp4')
        }

        return Response(req.iter_content(chunk_size=1024*1024), headers=headers)
    except Exception as e:
        return f"Download stream compilation broke: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

