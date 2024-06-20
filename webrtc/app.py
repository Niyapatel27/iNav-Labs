from flask import Flask, render_template, request, jsonify
from .firebase_handler import FirebaseHandler
from .file_manager import FileManager
import os

class MyFlaskApp:
    def __init__(self, firebase_cred_path, firebase_bucket_name):
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        self.app = Flask(__name__, template_folder=template_dir)
        self.firebase_handler = FirebaseHandler(firebase_cred_path, firebase_bucket_name)
        self.file_manager = FileManager()

        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/upload_video', 'upload_video', self.upload_video, methods=['POST'])

    def index(self):
        return render_template('index.html')

    def upload_video(self):
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file:
            temp_file = self.file_manager.save_temp_file(file)
            self.firebase_handler.upload_video_to_firebase(temp_file)
            self.file_manager.remove_temp_file(temp_file)
            return jsonify({'success': 'File uploaded successfully'}), 200

        return jsonify({'error': 'File upload failed'}), 500

    def run(self, debug=True):
        self.app.run(debug=debug)
