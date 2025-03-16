# Generated by Django 5.1.6 on 2025-03-16 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Analysis', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='excelfile',
            old_name='year',
            new_name='studying_year',
        ),
        migrations.AddField(
            model_name='excelfile',
            name='year_of_admission',
            field=models.IntegerField(default=2024),
            preserve_default=False,
        ),
    ]
