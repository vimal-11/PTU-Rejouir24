# Generated by Django 4.2.9 on 2024-03-09 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='events',
            name='category',
            field=models.CharField(choices=[('Day1', 'Day1'), ('Day2', 'Day2'), ('Day3', 'Day3')], default='O', max_length=30),
        ),
    ]
