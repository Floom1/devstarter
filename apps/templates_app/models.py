from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.urls import reverse
from django.contrib.auth.models import User
from apps.services.utils import unique_slugify


class Category(MPTTModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, verbose_name='URL категории', blank=True)
    description = models.TextField(verbose_name='Описание категории', max_length=300, blank=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
        related_name='children',
        verbose_name='Родительская категория'
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        db_table = 'dev_category'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def get_absolute_url(self):
        return reverse('category_templates', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, '')
        super().save(*args, **kwargs)


class TemplateManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


class Template(models.Model):
    name = models.CharField(max_length=70, verbose_name='Название')
    description = models.TextField(verbose_name='Описание', default='')
    file = models.FileField(upload_to='templates/', verbose_name='Шаблон', blank=True)
    template_dir = models.CharField(max_length=255, verbose_name='Путь к шаблону', blank=True, default='templates/')
    ci_template = models.TextField(blank=True, help_text="Шаблон ci.yml для GitHub Actions")
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    category = TreeForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')

    objects=models.Manager()
    custom = TemplateManager()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'dev_template'
        verbose_name = 'Шаблон'
        verbose_name_plural = 'Шаблоны'
        indexes = [models.Index(fields=['is_published'])]
