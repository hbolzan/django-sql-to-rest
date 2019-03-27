# Generated by Django 2.1.7 on 2019-03-25 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FieldValidation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Validation name')),
                ('service_name', models.CharField(max_length=200, verbose_name='Service name')),
                ('method_name', models.CharField(max_length=200, verbose_name='Method name')),
                ('single_argument', models.CharField(blank=True, help_text='Single argument source field appended to URI (optional)', max_length=200, null=True, verbose_name='Single argument')),
                ('named_arguments', models.TextField(blank=True, help_text='Named URL arguments in pairs `argument_name=field_name` (optional)', null=True, verbose_name='Named arguments')),
                ('expected_results', models.TextField(blank=True, help_text='Expected results in pairs `field_name<=additional_information_field` (optional)', null=True, verbose_name='Expected results')),
                ('message_on_error', models.BooleanField(default=True, help_text='Indicates whether the frontend should display the returned message if an error occurs', verbose_name='Show error message')),
            ],
        ),
    ]