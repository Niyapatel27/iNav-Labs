from mylibrary.app import MyFlaskApp

if __name__ == '__main__':
    firebase_cred_path = "service.json"
    firebase_bucket_name = "streaming-try-1e1b6.appspot.com"
    
    app = MyFlaskApp(firebase_cred_path, firebase_bucket_name)
    app.run()
