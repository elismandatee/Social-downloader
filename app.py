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
        # Configuration for yt-dlp to find the video stream link securely
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt',
            'allowed_extractors': ['default', 'youtube', 'tiktok', 'instagram', 'facebook', 'twitter'],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            download_url = info.get('url')
            title = info.get('title', 'Social Media Video')
            
            return jsonify({
                'success': True,
                'title': title,
                'download_url': download_url
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
