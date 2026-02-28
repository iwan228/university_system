from django.urls import path
from . import views

# НЕТ app_name — все URL без неймспейса для простоты
urlpatterns = [
    path('', views.debt_list, name='debt_list'),
    path('toggle-absence/<int:debt_id>/', views.toggle_absence, name='toggle_absence'),
    path('edit/<int:debt_id>/', views.debt_edit, name='debt_edit'),
    path('import/', views.import_excel, name='import_excel'),
    path('import/log/<int:log_id>/', views.import_log_detail, name='import_log_detail'),
    path('export/', views.export_excel, name='export_excel'),
    path('api/groups/', views.api_groups_by_direction, name='api_groups'),
]
