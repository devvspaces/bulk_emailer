import os
import sys


def _setup():
    if getattr(sys, 'frozen', False):
        data_dir = os.path.dirname(sys.executable)
        os.environ.setdefault('BULK_EMAILER_DATA_DIR', data_dir)
        os.chdir(data_dir)
    else:
        data_dir = os.path.dirname(os.path.abspath(__file__))
    for name in ('logs', 'media', 'static'):
        os.makedirs(os.path.join(data_dir, name), exist_ok=True)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')


def main():
    _setup()
    from django.core.management import execute_from_command_line

    argv = list(sys.argv)
    host = os.environ.get('BULK_EMAILER_HOST', '127.0.0.1')
    port = os.environ.get('BULK_EMAILER_PORT', '8000')

    if len(argv) <= 1:
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        try:
            from mailer.jobs import resume_orphaned_jobs
            resume_orphaned_jobs()
        except Exception:
            pass
        execute_from_command_line(
            ['manage.py', 'runserver', '--noreload', f'{host}:{port}'])
    else:
        execute_from_command_line(['manage.py'] + argv[1:])


if __name__ == '__main__':
    main()
