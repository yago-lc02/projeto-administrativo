from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('financeiro.urls')), # Agora as rotas começam com /api/
]