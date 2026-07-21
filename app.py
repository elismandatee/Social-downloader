from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
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
            'format': 'best',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get('title', 'Social_Media_Download')

        formats_available = []

        if info.get('formats'):
            for f in info['formats']:
                if f.get('url') and f.get('vcodec') != 'none':
                    height = f.get('height')
                    if height and isinstance(height, int):
                        if height >= 1080: label = "HD 1080p"
                        elif height >= 720: label = "HD 720p"
                        elif height >= 480: label = "SD 480p"
                        else: label = f"{height}p"
                    else:
                        label = "HD Video"

                    # Route every platform through our robust stream compiler to guarantee playback
                    proxy_target = f"/proxy-download?url={f['url']}&title={title}"

                    formats_available.append({
                        'quality': label,
                        'url': proxy_target,
                        'type': 'video'
                    })

        # Universal fallback stream
        if not formats_available and info.get('url'):
            fallback_target = f"/proxy-download?url={info.get('url')}&title={title}"
            formats_available.append({
                'quality': 'HD Video',
                'url': fallback_target,
                'type': 'video'
            })

        if not formats_available and 'entries' in info:
            for entry in info['entries']:
                if entry.get('url'):
                    entry_target = f"/proxy-download?url={entry.get('url')}&title={title}"
                    formats_available.append({
                        'quality': 'Media Item',
                        'url': entry_target,
                        'type': 'video'
                    })

        if not formats_available:
            return jsonify({'error': 'Could not extract a valid media stream.'}), 400

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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive'
        }
        
        # Stream data securely using requests with custom spoofed headers
        with requests.get(media_url, headers=headers, stream=True, timeout=30) as req:
            req.raise_for_status()
            clean_filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in '._-']).strip()
            
            response_headers = {
                'Content-Disposition': f'attachment; filename="{clean_filename or "media"}.mp4";',
                'Content-Type': 'video/mp4'
            }

            return Response(req.iter_content(chunk_size=1024*1024), headers=response_headers)
            
    except Exception as e:
        return f"Download stream compilation broke: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
                
