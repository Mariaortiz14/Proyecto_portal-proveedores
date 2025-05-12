from rest_framework import viewsets
from .models import registro_formulario
from .serializers import RegistroFormularioSerializer
from users.models import Departamento, Municipio
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = registro_formulario.objects.all()
    serializer_class = RegistroFormularioSerializer
    permission_classes = [AllowAny]


@api_view(['GET'])
def listar_departamentos(request):
    departamentos = Departamento.objects.all().values('codigo', 'nombre')
    return Response(list(departamentos))

@api_view(['GET'])
def listar_municipios(request, departamento_id):
    municipios = Municipio.objects.filter(departamento_id__codigo=departamento_id).values('codigo', 'nombre')
    return Response(list(municipios))

from proveedores.models import (
    actividad_eco_seccion,
    actividad_eco_division,
    actividad_eco_grupo,
    actividad_eco_clase
)

@api_view(['GET'])
def listar_secciones(request):
    secciones = actividad_eco_seccion.objects.all().values('codigo', 'descripcion')
    return Response(list(secciones))

@api_view(['GET'])
def listar_divisiones(request, seccion_codigo):
    divisiones = actividad_eco_division.objects.filter(seccion__codigo=seccion_codigo).values('codigo', 'descripcion')
    return Response(list(divisiones))

@api_view(['GET'])
def listar_grupos(request, division_codigo):
    grupos = actividad_eco_grupo.objects.filter(division__codigo=division_codigo).values('codigo', 'descripcion')
    return Response(list(grupos))

@api_view(['GET'])
def listar_clases(request, grupo_codigo):
    clases = actividad_eco_clase.objects.filter(grupo__codigo=grupo_codigo).values('codigo', 'descripcion')
    return Response(list(clases))
