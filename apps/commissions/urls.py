from django.urls import path
from . import views

app_name = 'commissions'

urlpatterns = [
    path('', views.commission_list, name='commission_list'),
    path('create/', views.commission_create, name='commission_create'),
    path('<int:sheet_id>/', views.commission_detail, name='commission_detail'),
    path('<int:sheet_id>/edit/', views.commission_edit, name='commission_edit'),
    path('<int:sheet_id>/autofill/', views.commission_autofill, name='commission_autofill'),
    path('<int:sheet_id>/add-student/', views.commission_add_student, name='commission_add_student'),
    path('<int:sheet_id>/entry/<int:entry_id>/grade/', views.commission_update_grade, name='commission_update_grade'),
    path('<int:sheet_id>/entry/<int:entry_id>/remove/', views.commission_remove_entry, name='commission_remove_entry'),
    path('<int:sheet_id>/close/', views.commission_close, name='commission_close'),
    path('<int:sheet_id>/export/', views.commission_export, name='commission_export'),
    path('<int:sheet_id>/print/protocol/', views.commission_print_protocol, name='commission_print_protocol'),
    path('<int:sheet_id>/print/order/', views.commission_print_order, name='commission_print_order'),
    path('<int:sheet_id>/print/table/', views.commission_print_table, name='commission_print_table'),
]
