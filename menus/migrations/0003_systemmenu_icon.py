# Generated by Django 2.1.7 on 2019-06-29 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menus', '0002_systemmenu_separator'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemmenu',
            name='icon',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Icon'),
        ),
    ]