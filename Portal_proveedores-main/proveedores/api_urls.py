from django.urls import path, include
from rest_framework.routers import DefaultRouter
from proveedores.api_views import ProveedorViewSet
from .api_views import listar_departamentos, listar_municipios
from .api_views import (
    listar_secciones, listar_divisiones,
    listar_grupos, listar_clases
)

router = DefaultRouter()
router.register(r'proveedores', ProveedorViewSet, basename='proveedor')

urlpatterns = router.urls
urlpatterns += [
    path('departamentos/', listar_departamentos, name='listar_departamentos'),
    path('municipios/<str:departamento_id>/', listar_municipios, name='listar_municipios'),
    path('secciones/', listar_secciones, name='listar_secciones'),
    path('divisiones/<str:seccion_codigo>/', listar_divisiones, name='listar_divisiones'),
    path('grupos/<str:division_codigo>/', listar_grupos, name='listar_grupos'),
    path('clases/<str:grupo_codigo>/', listar_clases, name='listar_clases'),
]
