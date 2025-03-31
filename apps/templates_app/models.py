from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    name = models.CharField(max_length=100)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class Template(models.Model):
    name = models.CharField(max_length=70)
    description = models.TextField
    file = models.FileField(upload_to='templates/')
    category = TreeForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
