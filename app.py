from flask import Flask, render_template, request, jsonify
import os
import tempfile
import firebase_admin
from firebase_admin import credentials, storage

app = Flask(__name__)

# Firebase initialization
cred = credentials.Certificate("service.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'streaming-try-1e1b6.appspot.com'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        file.save(temp_file.name)
        upload_video_to_firebase(temp_file.name)
        os.remove(temp_file.name)
        return jsonify({'success': 'File uploaded successfully'}), 200

    return jsonify({'error': 'File upload failed'}), 500

def upload_video_to_firebase(video_path):
    bucket = storage.bucket()
    blob = bucket.blob('videos/' + os.path.basename(video_path))
    blob.upload_from_filename(video_path)

if __name__ == '__main__':
    app.run(debug=True)
