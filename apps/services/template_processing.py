import os
import shutil
from string import Template
from django.conf import settings

def process_template(template_dir, output_dir, variables):
    """
    Обрабатывает файлы шаблона, заменяя плейсхолдеры на значения из variables.
    :param template_dir: Путь к папке с исходными файлами шаблона.
    :param output_dir: Путь к папке, куда сохраняются обработанные файлы.
    :param variables: Словарь с переменными для замены (например, {'project_name': 'my_app'}).
    """
    # Проверяем, существует ли исходная папка
    if not os.path.exists(template_dir):
        raise FileNotFoundError(f"Папка шаблона не найдена: {template_dir}")

    # Создаём выходную папку
    os.makedirs(output_dir, exist_ok=True)

    # Рекурсивно обходим файлы в template_dir
    for root, dirs, files in os.walk(template_dir):
        # Создаём относительный путь для сохранения структуры папок
        relative_root = os.path.relpath(root, template_dir)
        output_root = os.path.join(output_dir, relative_root)

        # Создаём соответствующие папки в выходной директории
        os.makedirs(output_root, exist_ok=True)

        for file in files:
            input_file_path = os.path.join(root, file)
            output_file_path = os.path.join(output_root, file)

            if file.lower() == '.gitignore':
                shutil.copy2(input_file_path, output_file_path)
                continue

            # Читаем содержимое файла
            try:
                with open(input_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Если файл не текстовый, просто копируем его
                shutil.copy2(input_file_path, output_file_path)
                continue

            # Заменяем плейсхолдеры
            try:
                processed_content = Template(content).substitute(variables)
            except KeyError as e:
                # Если переменная не найдена, пропускаем замену или логируем ошибку
                print(f"Предупреждение: Переменная {e} не найдена в словаре variables для файла {input_file_path}")
                processed_content = content

            # Сохраняем обработанный файл
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)