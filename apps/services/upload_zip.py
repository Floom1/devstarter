import zipfile
import os
import tempfile
import base64
import requests
from urllib.parse import quote


def extract_zip(zip_path):
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    return temp_dir

def upload_file_to_repo(owner, repo_name, file_path, relative_path, token, branch='main'):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    with open(file_path, 'rb') as f:
        content = base64.b64encode(f.read()).decode('utf-8')
    upload_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{relative_path}"
    upload_data = {
        "message": f"Добавлен файл {relative_path}",
        "content": content,
        "branch": branch
    }
    response = requests.put(upload_url, json=upload_data, headers=headers)
    return response