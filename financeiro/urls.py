from django.urls import path
from .views import ConsultaRAGView # Importe a nova View
from . import views

urlpatterns = [
    path('api/consulta-rag/', ConsultaRAGView.as_view(), name='consulta_rag'), # ◄ Certifique-se de que tem a / aqui

    # Nova rota para a interface visual da Etapa 4 (CASHFLOW) 🎨
    path('lancamentos/', views.listar_lancamentos, name='listar_lancamentos'),
    path('lancamentos/incluir/', views.incluir_lancamento, name='incluir_lancamento'),

    # Rota para API de geração de parcelas ⚙️
    path('api/gerar-parcelas/', views.gerar_parcelas_api, name='gerar_parcelas_api'),

    # Rotas Auxiliares que o template precisa reconhecer para os botões funcionarem:
    #path('incluir/', views.listar_lancamentos, name='incluir_lancamento'), # Temporário apontando para a listagem
    path('alterar/<int:pk>/', views.listar_lancamentos, name='alterar_lancamento'), # Temporário
    path('lancamentos/excluir/', views.excluir_lancamento, name='excluir_lancamento'),
    path('parcelas/<int:pk>/', views.listar_lancamentos, name='gerar_parcelas'), # Temporário
]