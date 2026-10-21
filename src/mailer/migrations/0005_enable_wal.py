from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('mailer', '0004_emailmanager_email_domain_emailmanager_reply_to_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            'PRAGMA journal_mode=WAL;',
            reverse_sql='PRAGMA journal_mode=DELETE;',
        ),
    ]
