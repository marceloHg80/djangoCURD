from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('registrar-nuevo-venta/', views.registrar_venta,
         name='registrar_venta'),
    path('lista-de-ventas/', views.listar_ventas, name='listar_ventas'),

    path('detalles-del-venta/<str:id>/',
         views.detalles_venta, name='detalles_venta'),

    path('formulario-para-actualizar-venta/<str:id>/',
         views.view_form_update_venta, name='view_form_update_venta'),

    path('actualizar-venta/<str:id>/',
         views.actualizar_venta, name='actualizar_venta'),
    path('eliminar-venta/', views.eliminar_venta, name='eliminar_venta'),


    path('descargar-informe-ventas',
         views.informe_venta, name="informe_venta"),
    path('formulario-para-la-carga-masiva-de-ventas',
         views.view_form_carga_masiva, name="view_form_carga_masiva"),
    path('subir-data-xlsx', views.cargar_archivo, name="cargar_archivo"),

]
