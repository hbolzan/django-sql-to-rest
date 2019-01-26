# Generated by Django 2.1.5 on 2019-01-25 20:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('db_query', '0003_auto_20190125_1735'),
    ]

    operations = [
        migrations.AlterField(
            model_name='persistentnestedquery',
            name='child',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parent_query', to='db_query.PersistentQuery', verbose_name='Child query'),
        ),
        migrations.AlterField(
            model_name='persistentnestedquery',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nested_query', to='db_query.PersistentQuery', verbose_name='Parent query'),
        ),
    ]
