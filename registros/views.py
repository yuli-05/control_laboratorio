from django.shortcuts import render, get_object_or_404, redirect
from django.shortcuts import render, redirect
from .forms import RegistroUsoLaboratorioForm
from .models import RegistroUsoLaboratorio
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Docente 
from .models import RegistroUsoLaboratorio, Docente
from django.db.models import Sum, Count, F, FloatField, ExpressionWrapper
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from openpyxl import Workbook
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from datetime import datetime
from .models import RegistroUsoLaboratorio, Laboratorio, Docente
from datetime import datetime
import openpyxl
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO



@login_required
def dashboard(request):
    total_docentes = Docente.objects.count()
    total_registros = RegistroUsoLaboratorio.objects.count()

    total_horas_programadas = RegistroUsoLaboratorio.objects.aggregate(
        Sum('horas_programadas')
    )['horas_programadas__sum'] or 0

    total_horas_cumplidas = RegistroUsoLaboratorio.objects.aggregate(
        Sum('horas_cumplidas')
    )['horas_cumplidas__sum'] or 0

    ultimos_registros = RegistroUsoLaboratorio.objects.select_related('docente').order_by('-fecha')[:5]

    registros_por_laboratorio = RegistroUsoLaboratorio.objects.values('laboratorio').annotate(total=Count('id'))
    labels_labs = [r['laboratorio'] for r in registros_por_laboratorio]
    data_labs = [r['total'] for r in registros_por_laboratorio]

    # NUEVO
    porcentaje_cumplimiento = (
        round((total_horas_cumplidas / total_horas_programadas) * 100, 2)
        if total_horas_programadas else 0
    )

    cumplimiento_labs = (
        RegistroUsoLaboratorio.objects
        .values('laboratorio')
        .annotate(
            horas_programadas=Sum('horas_programadas'),
            horas_cumplidas=Sum('horas_cumplidas'),
        )
        .annotate(
            porcentaje=ExpressionWrapper(
                F('horas_cumplidas') * 100.0 / F('horas_programadas'),
                output_field=FloatField()
            )
        )
    )

    cumplimiento_carreras = (
        RegistroUsoLaboratorio.objects
        .values('carrera')
        .annotate(
            horas_programadas=Sum('horas_programadas'),
            horas_cumplidas=Sum('horas_cumplidas'),
        )
        .annotate(
            porcentaje=ExpressionWrapper(
                F('horas_cumplidas') * 100.0 / F('horas_programadas'),
                output_field=FloatField()
            )
        )
    )

    context = {
        'total_docentes': total_docentes,
        'total_registros': total_registros,
        'total_horas_programadas': total_horas_programadas,
        'total_horas_cumplidas': total_horas_cumplidas,
        'ultimos_registros': ultimos_registros,
        'labels_labs': labels_labs,
        'data_labs': data_labs,
        # NUEVO
        'porcentaje_cumplimiento': porcentaje_cumplimiento,
        'cumplimiento_labs': cumplimiento_labs,
        'cumplimiento_carreras': cumplimiento_carreras,
    }

    return render(request, 'registros/dashboard.html', context)



def vista_reportes(request):
    registros = RegistroUsoLaboratorio.objects.all()
    docentes = Docente.objects.all()

    # Filtros GET
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    laboratorio = request.GET.get('laboratorio')
    docente = request.GET.get('docente')

    if fecha_inicio:
        registros = registros.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        registros = registros.filter(fecha__lte=fecha_fin)
    if laboratorio:
        registros = registros.filter(laboratorio=laboratorio)
    if docente:
        registros = registros.filter(docente__id=docente)

    # Porcentaje de cumplimiento por registro
    for r in registros:
        if r.horas_programadas:
            r.porcentaje_cumplimiento = (r.horas_cumplidas / r.horas_programadas) * 100
        else:
            r.porcentaje_cumplimiento = 0

    # Estadísticas por laboratorio (basado en choices)
    estadisticas_laboratorios = {}
    for codigo, nombre in RegistroUsoLaboratorio.LABORATORIOS:
        registros_lab = registros.filter(laboratorio=codigo)
        horas_prog = registros_lab.aggregate(Sum('horas_programadas'))['horas_programadas__sum'] or 0
        horas_cump = registros_lab.aggregate(Sum('horas_cumplidas'))['horas_cumplidas__sum'] or 0
        porcentaje = (horas_cump / horas_prog * 100) if horas_prog > 0 else 0
        estadisticas_laboratorios[nombre] = {
            'registros': registros_lab.count(),
            'horas_programadas': horas_prog,
            'horas_cumplidas': horas_cump,
            'porcentaje_cumplimiento': porcentaje,
        }

    context = {
        'registros': registros,
        'docentes': docentes,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'laboratorio_seleccionado': laboratorio,
        'docente_seleccionado': int(docente) if docente else None,
        'laboratorios_choices': RegistroUsoLaboratorio.LABORATORIOS,
        'estadisticas_laboratorios': estadisticas_laboratorios,
    }
    return render(request, 'reportes.html', context)




def exportar_reporte_excel(request):
    registros = RegistroUsoLaboratorio.objects.all()

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    laboratorio = request.GET.get('laboratorio')
    docente = request.GET.get('docente')

    if fecha_inicio:
        registros = registros.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        registros = registros.filter(fecha__lte=fecha_fin)
    if laboratorio:
        registros = registros.filter(laboratorio__id=laboratorio)
    if docente:
        registros = registros.filter(docente__id=docente)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte"

    headers = ["Fecha", "Docente", "Laboratorio", "Carrera", "Materia", "Grupo", "Unidad", "Tema", "Horas Programadas", "Horas Cumplidas", "Cumplimiento %"]
    ws.append(headers)

    for r in registros:
        porcentaje = (r.horas_cumplidas / r.horas_programadas * 100) if r.horas_programadas else 0
        ws.append([
            r.fecha.strftime("%Y-%m-%d"),
            str(r.docente),
            str(r.laboratorio),
            r.carrera,
            r.materia,
            r.grupo,
            r.unidad,
            r.tema,
            r.horas_programadas,
            r.horas_cumplidas,
            round(porcentaje, 2)
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = 'attachment; filename=ReporteLaboratorio.xlsx'
    wb.save(response)
    return response


def exportar_reporte_pdf(request):
    registros = RegistroUsoLaboratorio.objects.all()

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    laboratorio = request.GET.get('laboratorio')
    docente = request.GET.get('docente')

    if fecha_inicio:
        registros = registros.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        registros = registros.filter(fecha__lte=fecha_fin)
    if laboratorio:
        registros = registros.filter(laboratorio__id=laboratorio)
    if docente:
        registros = registros.filter(docente__id=docente)

    for r in registros:
        if r.horas_programadas:
            r.porcentaje_cumplimiento = (r.horas_cumplidas / r.horas_programadas) * 100
        else:
            r.porcentaje_cumplimiento = 0

    template = get_template("reporte_pdf.html")
    html = template.render({'registros': registros})

    response = BytesIO()
    pisa.CreatePDF(html, dest=response)
    pdf = response.getvalue()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=ReporteLaboratorio.pdf'
    return response



def logout_view(request):
    logout(request)
    return redirect('login')  # o a donde quieras redirigir después

def registro_formulario(request):
    if request.method == 'POST':
        form = RegistroUsoLaboratorioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('registro_exitoso')  # luego la creamos
    else:
        form = RegistroUsoLaboratorioForm()

    return render(request, 'registro_form.html', {'form': form})


def registro_exitoso(request):
    return render(request, 'registro_exitoso.html')


def lista_registros(request):
    registros = RegistroUsoLaboratorio.objects.all().order_by('-fecha')
    return render(request, 'registros/lista_registros.html', {'registros': registros})

def editar_registro(request, pk):
    registro = get_object_or_404(RegistroUsoLaboratorio, pk=pk)

    if request.method == 'POST':
        form = RegistroUsoLaboratorioForm(request.POST, instance=registro)
        if form.is_valid():
            form.save()
            return redirect('lista_registros')
    else:
        form = RegistroUsoLaboratorioForm(instance=registro)

    return render(request, 'registros/editar_registro.html', {'form': form})

def eliminar_registro(request, pk):
    registro = get_object_or_404(RegistroUsoLaboratorio, pk=pk)

    if request.method == 'POST':
        registro.delete()
        return redirect('lista_registros')

    return render(request, 'registros/eliminar_registro.html', {'registro': registro})


def lista_docentes(request):
    docentes = Docente.objects.all()
    return render(request, 'registros/lista_docentes.html', {'docentes': docentes})