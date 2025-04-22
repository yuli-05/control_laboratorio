from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template, render_to_string
from django.utils.dateparse import parse_date
from django.db.models import Sum, Count, F, FloatField, ExpressionWrapper
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


from openpyxl import Workbook
from xhtml2pdf import pisa
from io import BytesIO

from .forms import RegistroUsoLaboratorioForm
from .models import RegistroUsoLaboratorio, Docente, Laboratorio, Carrera, Materia


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

    porcentaje_cumplimiento = (
        round((total_horas_cumplidas / total_horas_programadas) * 100, 2)
        if total_horas_programadas else 0
    )

    cumplimiento_labs = RegistroUsoLaboratorio.objects.values('laboratorio').annotate(
        horas_programadas=Sum('horas_programadas'),
        horas_cumplidas=Sum('horas_cumplidas')
    ).annotate(
        porcentaje=ExpressionWrapper(
            F('horas_cumplidas') * 100.0 / F('horas_programadas'),
            output_field=FloatField()
        )
    )

    cumplimiento_carreras = RegistroUsoLaboratorio.objects.values('carrera').annotate(
        horas_programadas=Sum('horas_programadas'),
        horas_cumplidas=Sum('horas_cumplidas')
    ).annotate(
        porcentaje=ExpressionWrapper(
            F('horas_cumplidas') * 100.0 / F('horas_programadas'),
            output_field=FloatField()
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
        'porcentaje_cumplimiento': porcentaje_cumplimiento,
        'cumplimiento_labs': cumplimiento_labs,
        'cumplimiento_carreras': cumplimiento_carreras,
    }
    return render(request, 'registros/dashboard.html', context)


def vista_reportes(request):
    registros = RegistroUsoLaboratorio.objects.all()
    docentes = Docente.objects.all()
    carreras = registros.values_list('carrera', flat=True).distinct()
    materias = registros.values_list('materia', flat=True).distinct()

    # Filtros GET
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    laboratorio = request.GET.get('laboratorio')
    docente = request.GET.get('docente')
    carrera = request.GET.get('carrera')
    materia = request.GET.get('materia')

    if fecha_inicio:
        registros = registros.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        registros = registros.filter(fecha__lte=fecha_fin)
    if laboratorio:
        registros = registros.filter(laboratorio=laboratorio)
    if docente:
        registros = registros.filter(docente__id=docente)
    if carrera:
        registros = registros.filter(carrera=carrera)
    if materia:
        registros = registros.filter(materia=materia)

    # Calcular porcentaje de cumplimiento por registro
    for r in registros:
        if r.horas_programadas:
            r.porcentaje_cumplimiento = (r.horas_cumplidas / r.horas_programadas) * 100
        else:
            r.porcentaje_cumplimiento = 0

    # Estadísticas por laboratorio
    estadisticas_laboratorios = []
    for codigo_lab, nombre_lab in RegistroUsoLaboratorio.LABORATORIOS:
        registros_lab = registros.filter(laboratorio=codigo_lab)
        total_registros = registros_lab.count()
        horas_programadas = sum(r.horas_programadas for r in registros_lab)
        horas_cumplidas = sum(r.horas_cumplidas for r in registros_lab)
        porcentaje = (horas_cumplidas / horas_programadas) * 100 if horas_programadas > 0 else 0

        estadisticas_laboratorios.append({
            'codigo': codigo_lab,
            'laboratorio': nombre_lab,
            'registros': total_registros,
            'horas_programadas': horas_programadas,
            'horas_cumplidas': horas_cumplidas,
            'porcentaje': round(porcentaje, 2),
        })

    context = {
        'registros': registros,
        'docentes': docentes,
        'carreras': carreras,
        'materias': materias,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'docente_seleccionado': int(docente) if docente else None,
        'carrera_seleccionada': carrera,
        'materia_seleccionada': materia,
        'laboratorio_seleccionado': laboratorio,
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
        registros = registros.filter(laboratorio=laboratorio)
    if docente:
        registros = registros.filter(docente__id=docente)

    wb = Workbook()
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
        registros = registros.filter(laboratorio=laboratorio)
    if docente:
        registros = registros.filter(docente__id=docente)

    for r in registros:
        r.porcentaje_cumplimiento = (r.horas_cumplidas / r.horas_programadas * 100) if r.horas_programadas else 0

    template = get_template("reporte_pdf.html")
    html = template.render({'registros': registros})

    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    pdf = buffer.getvalue()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=ReporteLaboratorio.pdf'
    return response


def registros_por_laboratorio(request, lab_id): 
    registros = RegistroUsoLaboratorio.objects.filter(laboratorio=lab_id)

    filtros = {
        'fecha__gte': request.GET.get("fecha_inicio"),
        'fecha__lte': request.GET.get("fecha_fin"),
        'docente_id': request.GET.get("docente"),
        'carrera': request.GET.get("carrera"),
        'materia': request.GET.get("materia")
    }   


    # Quitar filtros vacíos
    filtros = {k: v for k, v in filtros.items() if v}
    registros = registros.filter(**filtros)

    # Calcular porcentaje
    for r in registros:
        if r.horas_programadas:
            r.porcentaje_cumplimiento = (r.horas_cumplidas / r.horas_programadas) * 100
        else:
            r.porcentaje_cumplimiento = 0


    # 3) Configura Paginator: 10 registros por página
    paginator = Paginator(registros, 10)
    page_number = request.GET.get('page')  # viene en la querystring
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)


    # 4) Renderiza el partial con el page_obj
    return render(request, "registros/tabla_registros_parcial.html", {"registros": page_obj})




def registros_por_laboratorio_docentes(request, lab_id):
    # 1️⃣ Filtramos por laboratorio y filtros GET
    registros = RegistroUsoLaboratorio.objects.filter(laboratorio=lab_id)
    filtros = {
        'fecha__gte': request.GET.get("fecha_inicio"),
        'fecha__lte': request.GET.get("fecha_fin"),
        'docente_id': request.GET.get("docente"),
        'carrera': request.GET.get("carrera"),
        'materia': request.GET.get("materia"),
    }
    # limpiamos vacíos
    filtros = {k: v for k, v in filtros.items() if v}
    registros = registros.filter(**filtros)

    # 2️⃣ Agrupamos por docente, carrera y grupo y sumamos horas
    resumen = registros.values(
        'docente__nombre',
        'carrera',
        'grupo'
    ).annotate(
        horas_programadas=Sum('horas_programadas'),
        horas_cumplidas=Sum('horas_cumplidas'),
    ).annotate(
        porcentaje_cumplimiento=ExpressionWrapper(
            F('horas_cumplidas') * 100.0 / F('horas_programadas'),
            output_field=FloatField()
        )
    ).order_by('docente__nombre')

    # 3️⃣ Paginación idéntica a “Ver registros”
    paginator = Paginator(resumen, 5)            # 5 filas por página
    page_num = request.GET.get('page')
    page_obj = paginator.get_page(page_num)

    return render(request,'registros/tabla_docentes_laboratorio.html',
                {
                    'resumenes': page_obj,     # la página actual
                    'page_obj': page_obj,
                })



def registros_filtrados_ajax(request):
    registros = RegistroUsoLaboratorio.objects.all()

    filtros = {
        'fecha__gte': request.GET.get('fecha_inicio'),
        'fecha__lte': request.GET.get('fecha_fin'),
        'docente_id': request.GET.get('docente'),
        'carrera': request.GET.get('carrera'),
        'laboratorio': request.GET.get('laboratorio'),
    }
    registros = registros.filter(**{k: v for k, v in filtros.items() if v})

    registros = registros.annotate(
        porcentaje_cumplimiento=ExpressionWrapper(
            F('horas_cumplidas') * 100.0 / F('horas_programadas'),
            output_field=FloatField()
        )
    )

    return render(request, 'tabla_registros_parcial.html', {'registros': registros})




def cargar_registros_por_laboratorio(request):
    if request.method == 'POST':
        lab_id = request.POST.get('lab_id')
        registros = RegistroUsoLaboratorio.objects.filter(laboratorio_id=lab_id).order_by('-fecha')
        html = render_to_string('tabla_registros_laboratorio.html', {'registros': registros})
        return JsonResponse({'html': html})
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def logout_view(request):
    logout(request)
    return redirect('login')


def registro_formulario(request):
    if request.method == 'POST':
        form = RegistroUsoLaboratorioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('registro_exitoso')
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
