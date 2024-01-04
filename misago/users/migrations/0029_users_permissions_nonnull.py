# Generated by Django 4.2.7 on 2023-12-21 21:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("misago_users", "0028_default_groups"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="misago_users.group"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="permissions_id",
            field=models.CharField(max_length=12),
        ),
    ]
