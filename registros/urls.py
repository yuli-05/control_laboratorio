from django.urls import path
from . import views

urlpatterns = [
    path('registrar/', views.registro_formulario, name='registro_uso_laboratorio'),
    path('exito/', views.registro_exitoso, name='registro_exitoso'),
    path('registros/', views.lista_registros, name='lista_registros'),
    path('editar/<int:pk>/', views.editar_registro, name='editar_registro'),
    path('eliminar/<int:pk>/', views.eliminar_registro, name='eliminar_registro'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('docentes/', views.lista_docentes, name='lista_docentes'),
    path('reportes/', views.vista_reportes, name='reportes'),
    path('reportes/exportar_excel/', views.exportar_reporte_excel, name='exportar_reporte_excel'),
    path('reportes/exportar_pdf/', views.exportar_reporte_pdf, name='exportar_reporte_pdf'),

]
