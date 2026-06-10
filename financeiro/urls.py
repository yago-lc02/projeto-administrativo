from django.urls import path
from .views import ConsultaRAGView
from . import views

urlpatterns = [
    path('api/consulta-rag/', ConsultaRAGView.as_view(), name='consulta_rag'),

    path('api/gerar-parcelas/', views.gerar_parcelas_api, name='gerar_parcelas_api'),
    path('api/obter-parcelas/<int:movimento_id>/', views.obter_parcelas_api, name='obter_parcelas_api'),

    path('lancamentos/', views.listar_lancamentos, name='listar_lancamentos'),
    path('lancamentos/incluir/', views.incluir_lancamento, name='incluir_lancamento'),
    path('alterar/<int:movimento_id>/', views.alterar_lancamento, name='alterar_lancamento'),
    path('lancamentos/excluir/<int:movimento_id>/', views.excluir_lancamento, name='excluir_lancamento'),
    path('parcelas/<int:pk>/', views.listar_lancamentos, name='gerar_parcelas'),
]