from django.db import migrations, models
import django.utils.timezone

def add_description_and_slug(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    for category in Category.objects.all():
        if not category.slug:
            category.slug = category.name.lower().replace(' ', '-')
            category.save()

class Migration(migrations.Migration):
    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='description',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(max_length=100, unique=True, blank=True),
        ),
        migrations.RunPython(add_description_and_slug),
    ]