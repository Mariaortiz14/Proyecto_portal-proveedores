"""
URL configuration for portal_proveedores project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import include, path
from django.views.generic import RedirectView
"""Url de la aplicacion principal de la aplicacion Portal_proveedores """

urlpatterns = [
    path('', RedirectView.as_view(url='users/login/', permanent=False), name='redirection_principal'),
    path('users/', include('users.urls')),
    path('proveedores/', include('proveedores.urls')),
    path('compras/', include('compras.urls')),
    path('admin/', admin.site.urls),
    path('proveedor/', include('proveedores.urls')),
    path('api/', include('proveedores.api_urls')),

    
]
# Configuración de Sentry para el monitoreo de errores
# from sentry_sdk import init
# init(dsn="https://f98603808507410082228881a23684b3@sentry.io/1449108")
# Configuración de Sentry para el monitoreo de errores
# sentry_sdk.init(
#     dsn="https://f98603808507410082228881a23684b3@sentry.io/1449108",
#     integrations=[DjangoIntegration()],
#     traces_sample_rate=1.0,
#     send_default_pii=True,
# )  

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)