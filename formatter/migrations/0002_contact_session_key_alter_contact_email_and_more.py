# Generated by Django 5.1.3 on 2024-11-22 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('formatter', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='session_key',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='email',
            field=models.EmailField(default='', max_length=254),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='first_name',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='formatted_number',
            field=models.CharField(default='', max_length=20),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='last_name',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
    ]
