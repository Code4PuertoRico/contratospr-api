# Generated by Django 3.1.12 on 2021-12-18 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("contracts", "0007_auto_20210912_2302")]

    operations = [
        migrations.AlterField(
            model_name="contract",
            name="exempt_id",
            field=models.CharField(blank=True, max_length=255),
        )
    ]
