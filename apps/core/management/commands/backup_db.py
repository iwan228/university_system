"""
Management commands for backup and restore.
Usage:
    python manage.py backup_db           # Create backup
    python manage.py backup_db --restore # List & restore from backup
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Создание и восстановление резервных копий базы данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--restore',
            action='store_true',
            help='Восстановить БД из резервной копии',
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Имя файла резервной копии для восстановления',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Список всех резервных копий',
        )

    def handle(self, *args, **options):
        backup_dir = Path(settings.BACKUP_DIR)
        backup_dir.mkdir(exist_ok=True)

        db_path = settings.DATABASES['default']['NAME']

        if options['list']:
            self._list_backups(backup_dir)
            return

        if options['restore']:
            self._restore(backup_dir, db_path, options.get('file'))
            return

        # Default: create backup
        self._backup(backup_dir, db_path)

    def _backup(self, backup_dir, db_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'db_backup_{timestamp}.sqlite3'
        backup_path = backup_dir / backup_name

        if not os.path.exists(db_path):
            self.stderr.write(self.style.ERROR(f'База данных не найдена: {db_path}'))
            return

        shutil.copy2(db_path, backup_path)
        file_size = os.path.getsize(backup_path)
        self.stdout.write(self.style.SUCCESS(
            f'Резервная копия создана: {backup_name} ({file_size / 1024:.1f} KB)'
        ))

    def _list_backups(self, backup_dir):
        backups = sorted(backup_dir.glob('db_backup_*.sqlite3'), reverse=True)
        if not backups:
            self.stdout.write('Резервных копий не найдено.')
            return

        self.stdout.write(self.style.SUCCESS(f'Найдено {len(backups)} копий:\n'))
        for bp in backups:
            size = os.path.getsize(bp)
            self.stdout.write(f'  {bp.name}  ({size / 1024:.1f} KB)')

    def _restore(self, backup_dir, db_path, file_name=None):
        if file_name:
            backup_path = backup_dir / file_name
        else:
            # Use latest
            backups = sorted(backup_dir.glob('db_backup_*.sqlite3'), reverse=True)
            if not backups:
                self.stderr.write(self.style.ERROR('Резервных копий не найдено.'))
                return
            backup_path = backups[0]
            self.stdout.write(f'Используется последняя копия: {backup_path.name}')

        if not backup_path.exists():
            self.stderr.write(self.style.ERROR(f'Файл не найден: {backup_path}'))
            return

        # Create backup of current DB before restoring
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pre_restore = backup_dir / f'pre_restore_{timestamp}.sqlite3'
            shutil.copy2(db_path, pre_restore)
            self.stdout.write(f'Текущая БД сохранена как: {pre_restore.name}')

        shutil.copy2(backup_path, db_path)
        self.stdout.write(self.style.SUCCESS(
            f'База данных восстановлена из {backup_path.name}'
        ))