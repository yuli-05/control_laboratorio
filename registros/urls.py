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
    path('registros_por_laboratorio/<str:lab_id>/', views.registros_por_laboratorio, name='registros_por_laboratorio'),
    path('registros_filtrados_ajax/', views.registros_filtrados_ajax, name='registros_filtrados_ajax'),
    path('cargar_registros_por_laboratorio/', views.cargar_registros_por_laboratorio, name='cargar_registros_por_laboratorio'),
    path(
        'registros_por_laboratorio/<str:lab_id>/docentes/',
        views.registros_por_laboratorio_docentes,
        name='registros_por_laboratorio_docentes'
    ),
    # 2) Ruta AJAX general (registros)
    path(
        'registros_por_laboratorio/<str:lab_id>/',
        views.registros_por_laboratorio,
        name='registros_por_laboratorio'
    ),
]
