# Generated by Django 4.0.5 on 2025-01-04 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailer', '0002_emailmanager'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailmanager',
            name='mail_manager',
            field=models.CharField(choices=[('sendgrid', 'Sendgrid'), ('zepto', 'ZeptoMail'), ('smtp', 'SMTP Server')], max_length=10),
        ),
    ]
