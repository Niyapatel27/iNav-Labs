import firebase_admin
from firebase_admin import credentials, storage
import os

class FirebaseHandler:
    def __init__(self, cred_path, bucket_name):
        self.cred = credentials.Certificate("service.json")
        firebase_admin.initialize_app(self.cred, {'storageBucket': 'streaming-try-1e1b6.appspot.com'})
        self.bucket = storage.bucket()

    def upload_video_to_firebase(self, video_path):
        blob = self.bucket.blob('videos/' + os.path.basename(video_path))
        blob.upload_from_filename(video_path)
