from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import requests

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
        formats_available = []
        title = "Social_Media_Download"

        # 1. Dedicated TikTok Handler
        if 'tiktok.com' in video_url.lower():
            try:
                api_endpoint = f"https://tikwm.com/api/?url={requests.utils.quote(video_url)}"
                res = requests.get(api_endpoint, timeout=15).json()
                if res.get('code') == 0 and res.get('data'):
                    vid_data = res['data']
                    title = vid_data.get('title', 'TikTok_Video')
                    play_addr = vid_data.get('play')
                    if play_addr:
                        proxy_target = f"/proxy-download?url={requests.utils.quote(play_addr)}&title={requests.utils.quote(title)}"
                        formats_available.append({
                            'quality': 'HD Video (No Watermark)',
                            'url': proxy_target,
                            'type': 'video'
                        })
            except Exception:
                pass

        # 2. Dedicated Instagram Handler (Completely bypasses yt-dlp login blocks)
        elif 'instagram.com' in video_url.lower():
            try:
                # Using a dedicated public JSON extractor API endpoint for Instagram
                ig_api = f"https://api.cobalt.tools/api/json"
                payload = {"url": video_url}
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
                r = requests.post(ig_api, json=payload, headers=headers, timeout=15)
                if r.status_code == 200:
                    res_json = r.json()
                    direct_vid = res_json.get('url') or (res_json.get('picker') and res_json['picker'][0].get('url'))
                    title = "Instagram_Media"
                    
                    if direct_vid:
                        proxy_target = f"/proxy-download?url={requests.utils.quote(direct_vid)}&title={requests.utils.quote(title)}"
                        formats_available.append({
                            'quality': 'HD Video',
                            'url': proxy_target,
                            'type': 'video'
                        })
            except Exception:
                pass

        # 3. Standard yt-dlp extraction strictly for Facebook and X (Twitter)
        if not formats_available and not ('instagram.com' in video_url.lower() or 'tiktok.com' in video_url.lower()):
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
                'format': 'best',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                title = info.get('title', 'Social_Media_Download')

            seen_qualities = set()
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

                        if label in seen_qualities:
                            continue
                        seen_qualities.add(label)

                        target_url = f['url']
                        if 'twitter.com' in video_url.lower() or 'x.com' in video_url.lower():
                            target_url = f"/proxy-download?url={requests.utils.quote(target_url)}&title={requests.utils.quote(title)}"

                        formats_available.append({
                            'quality': label,
                            'url': target_url,
                            'type': 'video'
                        })

            if not formats_available and info.get('url'):
                fallback_url = info.get('url')
                if 'twitter.com' in video_url.lower() or 'x.com' in video_url.lower():
                    fallback_url = f"/proxy-download?url={requests.utils.quote(fallback_url)}&title={requests.utils.quote(title)}"
                
                formats_available.append({
                    'quality': 'HD Video',
                    'url': fallback_url,
                    'type': 'video'
                })

        if not formats_available:
            return jsonify({'error': 'Could not extract media. Ensure the link is public and correct.'}), 400

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Range': 'bytes=0-'
        }
        
        req = requests.get(media_url, headers=headers, stream=True, timeout=35)
        clean_filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in '._-']).strip()
        
        response_headers = {
            'Content-Disposition': f'attachment; filename="{clean_filename or "media"}.mp4";',
            'Content-Type': req.headers.get('Content-Type', 'video/mp4')
        }

        return Response(req.iter_content(chunk_size=1024*1024), headers=response_headers)
        
    except Exception as e:
        return f"Proxy stream failed: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
                    
