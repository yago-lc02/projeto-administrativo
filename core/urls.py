from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('financeiro/', include('financeiro.urls')),  # Adicionado prefixo 'financeiro/' para alinhar com o frontend
]