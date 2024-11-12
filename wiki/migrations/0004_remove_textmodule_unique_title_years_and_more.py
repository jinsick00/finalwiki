# Generated by Django 5.1.2 on 2024-10-31 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0003_textmodule_unique_title_years'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='textmodule',
            name='unique_title_years',
        ),
        migrations.AddConstraint(
            model_name='textmodule',
            constraint=models.UniqueConstraint(fields=('parent_module', 'title', 'years'), name='unique_parent_title_years'),
        ),
    ]