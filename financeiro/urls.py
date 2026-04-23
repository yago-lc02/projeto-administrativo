from django.urls import path
from .views import VerificarDadosNFView, SalvarDadosNFView # Adicione aqui

urlpatterns = [
    path('verificar-nf/', VerificarDadosNFView.as_view(), name='verificar_nf'),
    path('salvar-nf/', SalvarDadosNFView.as_view(), name='salvar_nf'), # Nova rota
]