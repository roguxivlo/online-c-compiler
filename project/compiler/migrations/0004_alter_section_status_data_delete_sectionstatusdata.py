# Generated by Django 4.2 on 2023-05-10 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compiler', '0003_sectiontype_can_be_nested'),
    ]

    operations = [
        migrations.AlterField(
            model_name='section',
            name='status_data',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.DeleteModel(
            name='SectionStatusData',
        ),
    ]
