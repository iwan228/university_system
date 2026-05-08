# Архитектура и стэк

## Компонентная диаграмма

```mermaid
flowchart LR
    subgraph Client["Клиент (Browser)"]
        UI["HTML/CSS/JS\nTemplates + CSS"]
        Print["window.print()\nПечать таблиц"]
    end

    subgraph Django["Django App Server"]
        Core["core\nAuth, dashboard, backup"]
        Students["students\nМодели, импорт/экспорт, фильтры, вьюхи"]
        Commissions["commissions\nВедомости комиссий, авто-заполнение"]
        Services["services.py\nxlrd/openpyxl import, Excel export"]
        Admin["Django Admin"]
    end

    subgraph Infra["Инфраструктура"]
        DB["DB: SQLite (dev) → PostgreSQL (prod)"]
        Storage["FS: backups/, media (опц.)"]
        Auth["Django Auth\nSessions + CSRF"]
    end

    Client -->|HTTP(S)| Django
    Django -->|ORM| DB
    Django -->|File I/O| Storage
    Client -.->|Forms/CSRF| Auth
    Commissions --> Services
    Students --> Services
    Core --> Students
    Core --> Commissions
```

## Технологический стэк
- Python 3.12, Django 4.2
- БД: SQLite (dev) / PostgreSQL 14+ (prod)
- Импорт/экспорт: xlrd (.xls), openpyxl (.xlsx), python-dateutil
- UI: Django Templates + кастомный CSS (опц. Bootstrap 5)
- Фильтры: django-filter
- Формы: django-crispy-forms, crispy-bootstrap5
- Админка: Django Admin
- Печать: window.print() + @media print стили
- Бэкапы: management-команда backup_db; прод — cron/systemd timer

## Где происходит работа с БД (ORM)
- **Модели**: [apps/students/models.py](apps/students/models.py), [apps/commissions/models.py](apps/commissions/models.py) — определяют таблицы и связи.
- **Импорт Excel**: [apps/students/services.py](apps/students/services.py) — `get_or_create`, `create` для Direction/Group/Student/Subject/AcademicDebt.
- **Вьюхи (UI)**:
    - [apps/students/views.py](apps/students/views.py) — выборка задолженностей с `select_related`, пагинация, редактирование, экспорт.
    - [apps/commissions/views.py](apps/commissions/views.py) — создание/автозаполнение ведомостей, обновление оценок.
- **Фильтры**: [apps/students/filters.py](apps/students/filters.py) — ORM-фильтрация по связанным полям.
- **Админка**: [apps/students/admin.py](apps/students/admin.py), [apps/commissions/admin.py](apps/commissions/admin.py) — CRUD через Django Admin.
- **Management-команды**:
    - [apps/core/management/commands/backup_db.py](apps/core/management/commands/backup_db.py) — копирование файла SQLite / путь БД из `settings.DATABASES`.
    - [apps/core/management/commands/seed_demo_data.py](apps/core/management/commands/seed_demo_data.py) — генерация данных через ORM.
- **Конфигурация БД**: [config/settings.py](config/settings.py) — `DATABASES` (dev: SQLite; prod: сменить на PostgreSQL DSN).

## Поток данных (общее)
1) Пользователь в браузере открывает страницу → Django view получает HTTP запрос.
2) View через ORM читает/записывает модели (Student, AcademicDebt, CommissionSheet, др.).
3) Шаблон рендерит данные; при импорте Excel сервис создаёт/обновляет записи через ORM.
4) Экспорт Excel формируется в памяти и отдаётся как скачивание; печать — `window.print()`.

## Развёртывание (опция)
- Gunicorn/uvicorn + nginx
- Статика через collectstatic
- Бэкап БД на выделенный volume / облако
- CI/CD: GitHub Actions + Ansible (staging/prod)

## Примечания по печати
- Браузер имеет доступ к принтеру через системный диалог (`window.print()`).
- Стили `@media print` скрывают навигацию/кнопки и оформляют таблицы под A4.
