# Generated by Django 5.0.3 on 2024-03-31 18:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0019_alter_tblayout_layoutlogo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tbmiddlelayout',
            name='mdiusrid',
        ),
    ]
