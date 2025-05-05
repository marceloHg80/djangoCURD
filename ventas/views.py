from django.shortcuts import render, redirect
from datetime import datetime
from django.db.models import Sum, F
from django.core.exceptions import ValidationError
import os
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile

from decimal import Decimal  # Asegúrate de importar Decimal
from django.contrib import messages  # Para usar mensajes flash
from django.core.exceptions import ObjectDoesNotExist

# Para el informe (Reporte) Excel
import pandas as pd

import json

import logging

from django.utils import timezone
from openpyxl import Workbook  # Para generar el informe en excel
from django.http import HttpResponse, JsonResponse

from django.shortcuts import get_object_or_404
from . models import Venta  # Importando el modelo de Venta


def inicio(request):
    opciones_edad = [(str(edad), str(edad)) for edad in range(18, 51)]
    data = {
        'opciones_edad': opciones_edad,
    }
    return render(request, 'venta/form_venta.html', data)


def listar_ventas(request):
    ventas = Venta.objects.all().order_by('-fecha_venta')
    
    # Calcular ingresos por día para el gráfico
    ingresos_diarios = Venta.objects.values('fecha_venta').annotate(
        total_diario=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('fecha_venta')
    
    # Preparar datos para el scatter plot
    puntos_grafico = [
        {
            'x': item['fecha_venta'].strftime("%Y-%m-%d"),
            'y': float(item['total_diario'])
        } for item in ingresos_diarios
    ]
    
    context = {
        'ventas': ventas,
        'puntos_grafico': json.dumps(puntos_grafico)
    }
    return render(request, 'venta/lista_ventas.html', context)




def view_form_carga_masiva(request):
    return render(request, 'venta/form_carga_masiva.html')


def detalles_venta(request, id):
    try:
        venta = Venta.objects.get(id=id)
        data = {"venta": venta}
        return render(request, "venta/detalles.html", data)
    except Venta.DoesNotExist:
        error_message = f"no existe ningún registro para la busqueda id: {id}"
        return render(request, "venta/lista_ventas.html", {"error_message": error_message})


def registrar_venta(request):
    if request.method == 'POST':
        """ 
        Iterando a través de todos los elementos en el diccionario request.POST, 
        que contiene los datos enviados a través del método POST, e imprime cada par clave-valor en la consola
        for key, value in request.POST.items():
            print(f'{key}: {value}')
        """
        prod = request.POST.get('producto')
        cant = request.POST.get('cantidad')
        prec = request.POST.get('precio_unitario')
        fech = request.POST.get('fecha_venta')
        clie = request.POST.get('cliente')

        # Obtén la imagen del formulario
        foto_venta = request.FILES.get('foto_venta')

        if foto_venta:
            foto_venta = generate_unique_filename(foto_venta)

        # Procesa los datos y guarda en la base de datos
        venta = Venta(
            producto=prod,
            cantidad=cant,
            precio_unitario=prec,
            fecha_venta=fech,
            cliente=clie
        )
        venta.save()

        messages.success(
            request, f"Felicitaciones, el venta {prod} fue registrado correctamente 😉")
        return redirect('listar_ventas')

    # Si no se ha enviado el formulario, simplemente renderiza la plantilla con el formulario vacío
    return redirect('inicio')


def view_form_update_venta(request, id):
    try:
        venta = Venta.objects.get(id=id)
        opciones_edad = [(int(edad), int(edad)) for edad in range(18, 51)]

        data = { "venta": venta }
        return render(request, "venta/form_update_venta.html", data)
    except ObjectDoesNotExist:
        error_message = f"El Venta con id: {id} no existe."
        return render(request, "venta/lista_ventas.html", {"error_message": error_message})


def actualizar_venta(request, id):
    try:
        if request.method == "POST":
            # Obtén el venta existente
            venta = Venta.objects.get(id=id)

            venta.producto = request.POST.get('producto')
            venta.cantidad = request.POST.get('cantidad')
            venta.precio_unitario = request.POST.get('precio_unitario')
            # venta.fecha_venta = request.POST.get('fecha_venta')
            venta.cliente = request.POST.get('cliente')

            fecha_str = request.POST.get('fecha_venta')

            try:
                venta.fecha_venta = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                try:
                    # Intenta con formato en español
                    meses = {
                        'Enero': 'January', 'Febrero': 'February', 'Marzo': 'March',
                        'Abril': 'April', 'Mayo': 'May', 'Junio': 'June',
                        'Julio': 'July', 'Agosto': 'August', 'Septiembre': 'September',
                        'Octubre': 'October', 'Noviembre': 'November', 'Diciembre': 'December'
                    }
                    
                    for es, en in meses.items():
                        fecha_str = fecha_str.replace(es, en)
                    
                    venta.fecha_venta = datetime.strptime(fecha_str, "%d de %B de %Y").date()
                except ValueError:
                    raise ValidationError("Formato de fecha inválido. Use YYYY-MM-DD o 'DD de Month de YYYY'")

            # Convierte el valor a Decimal
            precio_unitario = Decimal(request.POST.get(
                'precio_unitario').replace(',', '.'))
            venta.precio_unitario = precio_unitario

            venta.save()
        return redirect('listar_ventas')
    except ObjectDoesNotExist:
        error_message = f"El Venta con id: {id} no se actualizó."
        return render(request, "venta/lista_ventas.html", {"error_message": error_message})


def informe_venta(request):
    try:
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="data_ventas.xlsx"'

        # Consulta la base de datos para obtener los datos que deseas exportar
        datos = Venta.objects.all()

        # Crea un nuevo libro de Excel y una hoja de trabajo
        workbook = Workbook()
        worksheet = workbook.active

        # Agrega encabezados
        worksheet.append(
            ['producto', 'cantidad', 'precio_unitario', 'fecha_venta', 'cliente'])

        # Agrega los datos a la hoja de trabajo
        for dato in datos:
            worksheet.append([dato.producto, dato.cantidad, dato.precio_unitario, dato.fecha_venta, dato.cliente])

        # Guarda el libro de Excel en la respuesta HTTP
        workbook.save(response)

        return response
    except ObjectDoesNotExist:
        error_message = "El Venta con id: {id} no existe."
        return render(request, "venta/lista_ventas.html", {"error_message": error_message})


def eliminar_venta(request):
    if request.method == 'POST':
        id_venta = json.loads(request.body)['idVenta']
        # Busca el venta por su ID
        venta = get_object_or_404(Venta, id=id_venta)
        # Realiza la eliminación del venta
        venta.delete()
        return JsonResponse({'resultado': 1})
    return JsonResponse({'resultado': 1})


def cargar_archivo(request):
    try:
        if request.method == 'POST':
            archivo_xlsx = request.FILES['archivo_xlsx']
            if archivo_xlsx.name.endswith('.xlsx'):
                df = pd.read_excel(archivo_xlsx, header=0)
                df['fecha_venta'] = pd.to_datetime(
                    df['fecha_venta'],
                    dayfirst=True,
                    errors='coerce'
                ).dt.date

                for _, row in df.iterrows():
                    if pd.isna(row['fecha_venta']):
                        continue  # O puedes registrar un mensaje si prefieres

                    venta, creado = Venta.objects.update_or_create(
                        producto=row['producto'],
                        defaults={
                            'producto': row['producto'],
                            'cantidad': row['cantidad'],
                            'precio_unitario': row['precio_unitario'],
                            'fecha_venta': row['fecha_venta'],
                            'cliente': row['cliente'],
                        }
                    )

                return JsonResponse({'status_server': 'success', 'message': 'Los datos se importaron correctamente.'})
            else:
                return JsonResponse({'status_server': 'error', 'message': 'El archivo debe ser un archivo de Excel válido.'})
        else:
            return JsonResponse({'status_server': 'error', 'message': 'Método HTTP no válido.'})

    except Exception as e:
        logging.error("Error al cargar el archivo: %s", str(e))
        return JsonResponse({'status_server': 'error', 'message': f'Error al cargar el archivo: {str(e)}'})


# Genera un nombre único para el archivo utilizando UUID y conserva la extensión.
def generate_unique_filename(file):
    extension = os.path.splitext(file.name)[1]
    unique_name = f'{uuid.uuid4()}{extension}'
    return SimpleUploadedFile(unique_name, file.read())

