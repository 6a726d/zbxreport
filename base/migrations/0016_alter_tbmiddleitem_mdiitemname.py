# Generated by Django 5.0.3 on 2024-03-27 16:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0015_alter_tbitens_itemname'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tbmiddleitem',
            name='mdiitemname',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.tbitens'),
        ),
    ]
