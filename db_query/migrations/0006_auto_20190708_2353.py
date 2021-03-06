# Generated by Django 2.1.7 on 2019-07-08 23:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db_query', '0005_persistentquery_conn_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='persistentquery',
            name='before_delete',
            field=models.CharField(blank=True, help_text='Method in a service to be called before record is deleted (service/method)', max_length=255, null=True, verbose_name='Before insert'),
        ),
        migrations.AddField(
            model_name='persistentquery',
            name='before_insert',
            field=models.CharField(blank=True, help_text='Method in a service to be called before record is inserted (service/method)', max_length=255, null=True, verbose_name='Before insert'),
        ),
        migrations.AddField(
            model_name='persistentquery',
            name='before_update',
            field=models.CharField(blank=True, help_text='Method in a service to be called before record is updated (service/method)', max_length=255, null=True, verbose_name='Before insert'),
        ),
    ]
