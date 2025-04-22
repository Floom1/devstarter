import zipfile
import os
from django.conf import settings

def create_zip_from_dir(dir_path, zip_name):
    """
    Создаёт ZIP-архив из указанной папки.
    :param dir_path: Путь к папке, которую нужно заархивировать.
    :param zip_name: Имя ZIP-файла.
    :return: Путь к созданному ZIP-файлу.
    """
    zip_path = os.path.join(settings.MEDIA_ROOT, 'temp', zip_name)
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dir_path)
                zipf.write(file_path, arcname)
    return zip_path