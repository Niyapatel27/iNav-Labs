import tempfile
import os

class FileManager:
    def save_temp_file(self, file):
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        file.save(temp_file.name)
        return temp_file.name

    def remove_temp_file(self, temp_file_path):
        os.remove(temp_file_path)
