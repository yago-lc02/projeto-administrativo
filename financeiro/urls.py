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

    # Telas integradas
    path('chat/', views.chat_rag_tela, name='chat_rag'),
    path('analisador/', views.analisador_json_tela, name='analisador_json_tela'),

    # APIs REST do analisador de JSON
    path('api/verificar-nf/', views.VerificarDadosNFView.as_view(), name='verificar_nf'),
    path('api/salvar-nf/', views.SalvarDadosNFView.as_view(), name='salvar_nf'),

    # CRUD Pessoas
    path('pessoas/', views.listar_pessoas, name='listar_pessoas'),
    path('pessoas/incluir/', views.incluir_pessoa, name='incluir_pessoa'),
    path('pessoas/alterar/<int:pessoa_id>/', views.alterar_pessoa, name='alterar_pessoa'),
    path('pessoas/excluir/<int:pessoa_id>/', views.excluir_pessoa, name='excluir_pessoa'),

    # CRUD Classificações
    path('classificacoes/', views.listar_classificacoes, name='listar_classificacoes'),
    path('classificacoes/incluir/', views.incluir_classificacao, name='incluir_classificacao'),
    path('classificacoes/alterar/<int:classificacao_id>/', views.alterar_classificacao, name='alterar_classificacao'),
    path('classificacoes/excluir/<int:classificacao_id>/', views.excluir_classificacao, name='excluir_classificacao'),
]