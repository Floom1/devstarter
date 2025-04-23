from uuid import uuid4
from pytils.translit import slugify


def unique_slugify(instance, slug, slug_field):
    model = instance.__class__
    unique_slug = slug_field
    if not slug_field:
        unique_slug = slugify(slug)
    elif model.objects.filter(slug=slug_field).exclude(id=instance.id).exists():
        unique_slug = f'{slugify(slug)}-{uuid4().hex[:8]}'
    return unique_slug


def generate_ci_yaml(template, params):
    """
    Генерирует содержимое ci.yml на основе категории и параметров.
    :param category: Объект Category.
    :param params: Словарь с параметрами (например, {'python_version': '3.10', 'test_command': 'pytest'}).
    :return: Содержимое файла ci.yml.
    """
    template = template.ci_template
    if not template:
        raise ValueError(f"Шаблон CI для категории {category.slug} не задан.")
    return template.format(**params)