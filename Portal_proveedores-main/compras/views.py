from django.urls import reverse
import re 
import os
from django.shortcuts import render
from django.http import HttpResponse
#from weasyprint import HTML, CSS
from collections import defaultdict
from django.db.models import Count, Max, F, ExpressionWrapper, fields, DurationField, Value, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader
from sqlalchemy import False_, desc
from django.apps import apps
from django.db import transaction
from proveedores.models import *
from .forms import Evaluacion_inicial, caracteristicas, crear_solicitud, ComentarioForm, SolicitudForm
from .models import *
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from portal_proveedores.settings import DEFAULT_FROM_EMAIL as s
import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group
from .chart import *


logger = logging.getLogger(__name__)

# Create your views here.
def dashboardc(request):
    return render(request, 'compras/dashboard/index.html', {})

def t_basicas(request):
    return render(request, 'compras/tablas/t_basicas.html', {})

def tablas(request, t):
    app_config = apps.get_app_config('proveedores')
    for model in app_config.get_models():
        t_nombre= model.__name__
        if t == t_nombre:
            tabla = apps.get_model('proveedores', t)
            nombre = t_nombre.replace("_", " ")
            nombre_t = t_nombre
            objetos= tabla.objects.all()
        else:
            tabla = None
            objetos = None

    return render(request, 'compras/tablas/tablas.html', {'t_nombre': nombre_t, 'objetos': objetos, 'nombre': nombre})

def eliminar(request, tablas, id):
    tabla = apps.get_model('proveedores', tablas)
    tabla.objects.filter(id=id).delete()
    
    return redirect('compras:tablas', t=tablas)

def Crear_editar(request, tablas):
    tabla = apps.get_model('proveedores', tablas)
    id = request.POST['id']
    with transaction.atomic():
        if id == '':
            nombre_modelo = request.POST['nombre'] 
            tabla = apps.get_model('proveedores', tablas)
            objeto = tabla.objects.create(nombre=nombre_modelo)
            objeto.save()
        elif tabla.objects.filter(id=id):
            nombre_modelo = request.POST['nombre']
            id = request.POST['id']
            tabla = apps.get_model('proveedores', tablas)
            tabla.objects.filter(id=id).update(nombre=nombre_modelo)    

    return redirect('compras:tablas', t=tablas)

def matriz(request):
    familias_= familias.objects.all()
    doc_generales = matriz_doc.objects.filter(tipo='DG')
    doc_certificados = matriz_doc.objects.filter(tipo='DC')
    doc_regla = matriz_doc.objects.filter(tipo='DR')
    doc_varios = matriz_doc.objects.filter(tipo='DV')
    doc_lic = matriz_doc.objects.filter(tipo='DL')
    doc_califi = matriz_doc.objects.filter(tipo='DCA')
    if request.method == 'POST':
        familia = familias.objects.get(id=request.POST['familia'])      
        print(request.POST)
        for key, value in request.POST.items():
            # Filtrar claves que no son números
            if not key.isdigit():
                continue
            if FamiliaDocumento.objects.filter(familia=familia, documento__id=key).exists():
                documento = matriz_doc.objects.get(id=key)
                if request.POST.get(key):
                    with transaction.atomic(): 
                        doc = FamiliaDocumento.objects.get(familia=familia, documento=documento)
                        doc.obligatoriedad = value
                        doc.save()
            elif matriz_doc.objects.filter(id=key).exists():
                documento = matriz_doc.objects.get(id=key)
                if request.POST.get(key):
                    with transaction.atomic(): 
                        FamiliaDocumento.objects.create(familia=familia, documento=documento, obligatoriedad=value)

    return render(request, 'compras/tablas/matriz.html', {'familias':familias_, 'doc_generales': doc_generales, 'doc_certificados': doc_certificados, 'doc_regla': doc_regla, 'doc_varios': doc_varios, 'doc_lic': doc_lic, 'doc_califi': doc_califi})



def matriz_info(request, familia):
    familia_doc = FamiliaDocumento.objects.filter(familia=familia)
    if familia_doc:
        return JsonResponse({'familia': familia, 'documentos': list(familia_doc.values())})
    else:
        return JsonResponse({'familia': familia, 'documentos': 'No hay documentos asociados a esta familia'})
    

def Misproveedores(request):
    reg = registro_formulario.objects.all()
    registros= {}
    
    for r in reg:
        homologa = homologacion.objects.get(id_registro=r.id_registro)
        registros[r.id_registro] = [r, homologa]
    
    return render(request, 'compras/proveedores/index.html', {'registros': registros})

def Proveedor(request, id_registro):

    registro= registro_formulario.objects.get(id_registro=id_registro)
    homologa = homologacion.objects.get(id_registro=id_registro)
    accionarios = composicion_accionaria.objects.filter(id_registro=id_registro)
    contable = info_pago.objects.get(id_registro=id_registro)

    familias_= familias.objects.all()
    # Obtener todos los documentos y certificaciones
    documentos_g = documentos_requeridos.objects.filter(id_registro=id_registro)
    documentos_c = certificaciones_proveedores.objects.filter(id_registro=id_registro)

    # Contar los documentos y certificaciones
    cant_doc = documentos_g.count()
    cant_cer = documentos_c.count()
    total_doc = cant_doc + cant_cer

    # Obtener aprobaciones de documentos y certificaciones
    documentos_aprobados = aprobacion_doc.objects.filter(documento__id_registro=id_registro).values('documento__id', 'aprobado')
    certifi_aprobados = aprobacion_doc.objects.filter(certificados__id_registro=id_registro).values('certificados__id', 'aprobado')

    # Unir los resultados de aprobaciones
    todos_ids = documentos_aprobados.union(certifi_aprobados)

    # Inicializar contadores
    doc_aceptados = 0
    doc_rechazados = 0

    # Contar aprobados y rechazados
    for doc in todos_ids:
        if doc['aprobado']:
            doc_aceptados += 1
        else:
            doc_rechazados += 1

    # Calcular documentos pendientes
    doc_pendientes = total_doc - (doc_aceptados + doc_rechazados)

    # Ahora tienes las variables doc_pendientes, doc_aceptados y doc_rechazados
    documentos_estado = {doc['documento__id']: doc['aprobado'] for doc in todos_ids}

    if aprobacion_doc.objects.filter(certificados__id='24'):
        oea_val= True
    else:
        oea_val= False
        if certificaciones_proveedores.objects.filter(id_registro=id_registro,  certificacion_id='24'):
            mensaje_oea = "Documento no aprobado o rechazado"
        else:
            mensaje_oea = "Documento no subido"
            
    if registro.responsabilidad_social == True:
        rse= 5
    else:
        rse=0
    plazos = productos_servicios_condiciones.objects.get(id_registro=id_registro)  
    
    todos_documentos_aprobados = all(aprobacion_doc.objects.filter(documento__id=doc_id).exists() for doc_id in documentos_g.values_list('id', flat=True))
    todos_certificados_aprobados = all(aprobacion_doc.objects.filter(certificados__id=cert_id).exists() for cert_id in documentos_c.values_list('id', flat=True))
    # Si todos los documentos y certificados están aprobados, condition es True. Si no, es False.
    condition = todos_documentos_aprobados and todos_certificados_aprobados == True
    
    if condition == True:
        condicion, faltantes, _ = verificar_documentos_y_certificados_por_familia(homologa.familia, id_registro)
        if condicion:
            todos_documentos_aprobados = all(aprobacion_doc.objects.filter(documento__id=doc_id,  aprobado=True).exists() for doc_id in documentos_g.values_list('id', flat=True))
            todos_certificados_aprobados = all(aprobacion_doc.objects.filter(certificados__id=cert_id,  aprobado=True).exists() for cert_id in documentos_c.values_list('id', flat=True))
            # Si todos los documentos y certificados están aprobados, condition es True. Si no, es False.
            matriz = todos_documentos_aprobados and todos_certificados_aprobados == True
            if matriz == True:
                valor_matriz= 40
                mensaje_matriz = "Todos los documentos y certificados requeridos han sido aprobados"
                
            else:
                valor_matriz= 20
                mensaje_matriz = "No todos los documentos y certificados requeridos han sido aprobados"
            
        else:
            valor_matriz = 20
            mensaje_matriz = "No todos los documentos y certificados requeridos han sido subidos"
    else:
        faltantes = []
        valor_matriz = 0
        mensaje_matriz = "No todos los documentos y certificados han sido aprobados"     
       
    form = Evaluacion_inicial(initial={'oea':oea_val, 'extra': rse, 'forma_pago': plazos.plazo.id, 'matriz': valor_matriz})
    return render(request, 'compras/proveedores/proveedor.html', {'registro': registro, 'homologa': homologa, 'contable': contable,
                                                           'total':total_doc, 'familias': familias_, 'documentos_g': documentos_g, 
                                                           'documentos_c': documentos_c, 'documentos_estado': documentos_estado,
                                                          'form':form, 'accionarios': accionarios, 'mensaje_oea': mensaje_oea,
                                                           'condition': condition, 'faltantes':faltantes, 'doc_pendientes': doc_pendientes,
                                                           'doc_aceptados': doc_aceptados, 'doc_rechazados': doc_rechazados, 'mensaje_matriz': mensaje_matriz})

def verificar_documentos_y_certificados_por_familia(familia_id, id_registro):
    # Obtén todos los documentos requeridos para la familia
    documentos_matriz = FamiliaDocumento.objects.filter(familia_id=familia_id)

    # Obtén todos los documentos y certificados subidos
    documentos_subidos = documentos_requeridos.objects.filter(id_registro=id_registro)
    certificados_subidos = certificaciones_proveedores.objects.filter(id_registro=id_registro)

    # Verifica si todos los documentos y certificados requeridos han sido subidos
    documentos_faltantes = [doc_req for doc_req in documentos_matriz if doc_req.documento.id not in [doc_sub.documento.id for doc_sub in documentos_subidos]]
    certificados_faltantes = [cert_req for cert_req in documentos_matriz if cert_req.documento.id not in [cert_sub.certificacion.id for cert_sub in certificados_subidos]]

    # Verifica si todos los documentos y certificados obligatorios han sido subidos
    documentos_obligatorios_faltantes = [doc_req for doc_req in documentos_matriz if doc_req.documento.id not in [doc_sub.documento.id for doc_sub in documentos_subidos] and doc_req.obligatoriedad == '*']
    certificados_obligatorios_faltantes = [cert_req for cert_req in documentos_matriz if cert_req.documento.id not in [cert_sub.certificacion.id for cert_sub in certificados_subidos] and cert_req.obligatoriedad == '*']

    # Si todos los documentos y certificados obligatorios han sido subidos, condition es True. Si no, es False.
    condition = len(documentos_obligatorios_faltantes) == 0 and len(certificados_obligatorios_faltantes) == 0

    # Devuelve la condición y los arrays de documentos y certificados faltantes
    return condition, documentos_faltantes, certificados_faltantes

def aprobar_documento(request, id_registro):
    if request.method == 'POST' and 'aprobar' in request.POST:
        try:
            with transaction.atomic(): 
                if documentos_requeridos.objects.filter(id=request.POST['id']).exists():
                    doc = documentos_requeridos.objects.get(id=request.POST['id'])
                    aprobacion_doc.objects.create(documento=doc, aprobado=True, descripcion=request.POST['des'], fecha_vencimiento=request.POST['fecha_ven'] or None)
                elif certificaciones_proveedores.objects.filter(id=request.POST['id']).exists():
                    doc = certificaciones_proveedores.objects.get(id=request.POST['id'])
                    aprobacion_doc.objects.create(certificados=doc, aprobado=True, descripcion=request.POST['des'], fecha_vencimiento=request.POST['fecha_ven'] or None)      
        except Exception as e:
            print(e)
    
    elif request.method == 'POST' and 'desaprobar' in request.POST:
        try:
            with transaction.atomic(): 
                if documentos_requeridos.objects.filter(id=request.POST['id']).exists():
                    doc = documentos_requeridos.objects.get(id=request.POST['id'])
                    aprobacion_doc.objects.create(documento=doc, aprobado=False, descripcion=request.POST['des'])
                elif certificaciones_proveedores.objects.filter(id=request.POST['id']).exists():
                    doc = certificaciones_proveedores.objects.get(id=request.POST['id'])
                    aprobacion_doc.objects.create(certificados=doc, aprobado=False, descripcion=request.POST['des'])
        except Exception as e:
            print(e)
    return redirect('compras:proveedor', id_registro=id_registro)


def homologacion_proveedor(request, id_registro):
    form = Evaluacion_inicial(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        homologa = evaluacion_inicial.objects.create(id_registro=id_registro, oea=form.cleaned_data['oea'],
                                                    descripcion_o=form.cleaned_data['descripcion_o'], validacion=form.cleaned_data['validacion'],
                                                    descripcion_v=form.cleaned_data['descripcion_v'], calidad=form.cleaned_data['calidad'],
                                                    descripcion_c=form.cleaned_data['descripcion_c'], extra=form.cleaned_data['extra'],
                                                    descripcion_ex=form.cleaned_data['descripcion_ex'], experiencia=form.cleaned_data['experiencia'],
                                                    descripcion_e=form.cleaned_data['descripcion_e'], matriz=form.cleaned_data['matriz'],
                                                    descripcion_m=form.cleaned_data['descripcion_m'], forma_pago=form.cleaned_data['forma_pago'],
                                                    descripcion_f=form.cleaned_data['descripcion_f'])
        homologa.save()
    return redirect('compras:proveedor', id_registro=id_registro)  
        

def asigancion_familia(request, id_registro):
    if request.method == 'POST':
        homo= homologacion.objects.get(id_registro=id_registro)
        familia = familias.objects.get(id=request.POST['familia'])
        homo.familia = familia
        homo.save()
    return redirect('compras:proveedor', id_registro= id_registro)


def MisSolicitudes(request):
    solicitudes = solicitud.objects.all()
    return render(request, 'compras/solicitudes/solicitudes.html', {'solicitudes':solicitudes})



def send_email_task(subject, recipient_list, template_name, context):
    try:        
        if not isinstance(recipient_list, (list, tuple)):
            recipient_list = [recipient_list]
        domain = f"{settings.SITE_DOMAIN}:{settings.SITE_PORT}"
        
        # Generar la URL completa
        solicitud_id = context.get('solicitud_id')
        if solicitud_id:
            relative_url = reverse('compras:solicitud_id', args=[solicitud_id])
            full_url = f"{settings.DEFAULT_HTTP_PROTOCOL}://{domain}{relative_url}"
            print(full_url)
            context['url'] = full_url
 
        print(context)
        # Renderizar la plantilla con el contexto proporcionado
        content = render_to_string(template_name, context)
        from_email = s  # Define el remitente correctamente
        
        # Crea el mensaje de correo electrónico
        message = EmailMultiAlternatives(
            subject,  # Título
            '',  # El cuerpo del mensaje en texto plano (puede estar vacío si solo enviarás HTML)
            from_email,  # Remitente
            [],
            bcc=recipient_list,# Destinatario(s)
        )
        
        # Adjunta el contenido HTML
        message.attach_alternative(content, 'text/html')
        
        # Envía el correo
        message.send()
    except Exception as e:
        print(e)
        logger.error(f"Error al enviar el correo: {e}")

def crear_solicitudes(request):
    form = crear_solicitud(request.POST or None)
    if request.method=='POST':
        carac = form.carasteristicas(request.POST or None)
        try:
            with transaction.atomic():
                if form.is_valid() and carac.is_valid():
                    solicitud_ = solicitud.objects.create(
                        TSolicitud=form.cleaned_data['solicitud'],
                        descripcion=form.cleaned_data['descripcion'],
                        familia=form.cleaned_data['familia'],
                        cantidad=form.cleaned_data['cantidad'],
                        estado='Nueva'
                    )
                    for c in carac.cleaned_data:
                        if 'caracteristica' in c and c['caracteristica'] != ' ':
                            caracteristica = c['caracteristica']
                            caracteristicas_solicitud.objects.create(
                                solicitud_id=solicitud_.id,
                                caracteristica=caracteristica
                            )
                    id = solicitud_.id
                    url = reverse('compras:solicitud_id', args=[id])
                    correos = homologacion.objects.filter(familia=solicitud_.familia).values_list('id_registro__email', flat=True)
                    if correos:
                        context = {
                            'titulo': solicitud_.TSolicitud,
                            'descripcion': solicitud_.descripcion,
                            'fecha_creacion': solicitud_.fecha_creacion,
                            'url': url,
                            'solicitud_id':id, 
                        }
                        send_email_task('Solicitud FEPCO', correos, 'compras/correo/email_notsoli.html', context)
                    else:
                        messages.error(request, 'No se envió correos porque no hay proveedores homologados para esta familia')
                        context = {
                            'solicitud': solicitud_.TSolicitud,
                            'descripcion': solicitud_.descripcion,
                            'fecha_creacion': solicitud_.fecha_creacion,
                            'error': 'No se envió correos porque no hay proveedores homologados para esta familia',
                            'url': url,
                            'solicitud_id': id,
                        }
                        #send_email_task('error al enviar [Solicitud FEPCO]', 'jcsanchez@fepco.com.co', 'compras/correo/email_notsoli.html', context)
                        send_email_task('error al enviar [Solicitud FEPCO]', 'ymorales@fepco.com.co', 'compras/correo/email_notsoli.html', context)
                    return redirect('compras:missolicitudes')
                else:
                    messages.error(request, 'Formulario inválido')
        except Exception as e:
            messages.error(request, f'Error al crear la solicitud: {str(e)}')
            return redirect('compras:crear_solicitud')

    return render(request, 'compras/solicitudes/crear_soli.html', {'form':form})


def eliminar_solicitud(request, id):
    solicitud.objects.filter(id=id).delete()
    return redirect('compras:missolicitudes')

def solicitud_id(request, id):

    solicitudes = solicitud.objects.get(id=id)    
    subquery = propuestas_sol.objects.filter(
        id_homologacion=OuterRef('id_homologacion')
    ).values('id_homologacion').annotate(max_id=Max('id')).values('max_id')
    
    propuestas_ultimas = propuestas_sol.objects.filter(
        id__in=Subquery(subquery), id_solicitud_id=id
    )
    propuestas_ranking = propuestas_ultimas.annotate(
        tiempo_entrega=ExpressionWrapper(
            Coalesce(F('tiempo_entrega_max'), Value(0)) - F('tiempo_entrega_min'),
            output_field=DurationField()
        )
    ).order_by('valor_t', 'tiempo_entrega')
    form = ComentarioForm()                                                                                                                                                                                                                                                                                                                                                                         
    return render(request, 'compras/solicitudes/solicitud_id.html', {'solicitud': solicitudes, 'form_comentarios': form, 'propuestas_ultimas': propuestas_ultimas, 'propuestas_ranking': propuestas_ranking})

def get_propuestas_chart(request, id):
    propuestas= propuestas_sol.objects.filter(id_solicitud_id=id)
 
    propuestas_por_homologacion = defaultdict(list)
    for propuesta in propuestas:
        propuestas_por_homologacion[propuesta.id_homologacion].append(propuesta)
        
    mx_conteo = max(propuesta.conteo for propuesta in propuestas)
      
    return JsonResponse({
        "title": f"Ranking propuestas por Proveedor",
        "data": {
            "labels": [num for num in range(1, mx_conteo + 1)],
            "datasets": [
                {
                    "label": f"Proveedor {id_homologacion.id_registro.sigla}",
                    "data": [propuesta.valor_t for propuesta in propuestas],
                    "fill": False,
                    "borderColor": generate_color_random(),
                    "tension": 0,
                }
                for id_homologacion, propuestas in propuestas_por_homologacion.items()
            ]
        },
    })


def agregar_comentario(request, id, parent_id=None):
    solicitud_obj = get_object_or_404(solicitud, id=id)
    parent_comentario = None
    if parent_id:
        parent_comentario = get_object_or_404(comentarios, id=parent_id)

    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.solicitud = solicitud_obj
            comentario.usuario = request.user
            if parent_comentario:
                comentario.parent = parent_comentario
                correos = comentario.parent.usuario.email
                context = {
                    'titulo': solicitud_obj.TSolicitud,
                    'url': reverse('compras:solicitud_id', args=[solicitud_obj.id]),
                    'solicitud_id': solicitud_obj.id,
                }
                send_email_task(f'Comentario en solicitud {id}', correos, 'compras/correo/email_comentario.html', context)
            comentario.save()
            return redirect('compras:solicitud_id', id=id)
        else:
            messages.error(request, 'Formulario inválido')
            return redirect('compras:solicitud_id', id=id)
    else:
        return redirect('compras:solicitud_id', id=id)
    
    
def tareas(request):
    tareas = Tarea.objects.all()
    return render(request, 'compras/tareas/tareas.html', {'tareas': tareas})



def asignar_tarea_doc(request, id_registro):
    if request.method == 'POST':
        id_doc = request.POST['id']
        tipo = TipoTarea.objects.get(id=1)
        homologacion_ = homologacion.objects.get(id_registro=id_registro)
        crear_tarea = Tarea.objects.create(descripcion=request.POST['descripcion'], fecha_vencimiento=request.POST['fecha_ven'],
                                           datos_adicionales=id_doc, tipo=tipo, usuario=homologacion_.usuario_hologa )
        
    return redirect('compras:tareas')

def generar_pdf(request, id_registro):
    registro = get_object_or_404(registro_formulario, id_registro=id_registro)
    homologa = get_object_or_404(homologacion, id_registro=id_registro)
    accionarios = composicion_accionaria.objects.filter(id_registro=id_registro)
    contable = get_object_or_404(info_pago, id_registro=id_registro)
    financiera = get_object_or_404(info_financiera, id_registro=id_registro)
    tributaria = get_object_or_404(info_tributaria, id_registro=id_registro)
    resolucion_ = resolucion.objects.filter(id_trib=tributaria)
    # Renderizar el HTML con los datos
    html_string = render_to_string('compras/proveedores/contacto_report.html', {
        'registro': registro,
        'homologa': homologa,
        'contable': contable,
        'accionarios': accionarios,
        'financiera': financiera,
        'tributaria': tributaria,
    })

    # Crear el PDF
    '''
    html = HTML(string=html_string)
    bootstrap_css_path = os.path.join(settings.STATIC_ROOT, "bootstrap/css/bootstrap.min.css")
    pdf = html.write_pdf(stylesheets=[CSS(bootstrap_css_path)])
    # Devolver el PDF como respuesta HTTP
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=registro_{id_registro}.pdf'
    return response
'''

def editar_solicitud(request, solicitud_id):
    solicitud_ = get_object_or_404(solicitud, id=solicitud_id)
    if request.method == 'POST':
        form = SolicitudForm(request.POST, instance=solicitud_)
        if form.is_valid():
            form.save()
            return redirect(reverse('detalle_solicitud', args=[solicitud.id]))
    else:
        form = SolicitudForm(instance=solicitud_)
    return render(request, 'editar_solicitud.html', {'form': form, 'solicitud': solicitud_})