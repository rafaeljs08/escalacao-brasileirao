from django.urls import path

from . import views
from .assetsmgr import views as asset_views

urlpatterns = [
    path('', views.escalacao_lista, name='futebol'),
    path('time/novo/', views.escalacao_criar, name='futebol_time_criar'),
    path('time/<int:pk>/', views.escalacao_detalhe, name='futebol_time'),
    path('time/<int:pk>/editar/', views.escalacao_editar, name='futebol_time_editar'),
    path('time/<int:pk>/excluir/', views.escalacao_excluir, name='futebol_time_excluir'),
    path('time/<int:pk>/jogador/novo/', views.jogador_criar, name='futebol_jogador_criar'),
    path('time/<int:pk>/jogador/<int:jogador_pk>/editar/', views.jogador_editar, name='futebol_jogador_editar'),
    path('time/<int:pk>/jogador/<int:jogador_pk>/excluir/', views.jogador_excluir, name='futebol_jogador_excluir'),
    path('time/<int:pk>/jogador/<int:jogador_pk>/noticia/nova/', views.noticia_criar, name='futebol_noticia_criar'),
    path(
        'time/<int:pk>/jogador/<int:jogador_pk>/noticia/<int:noticia_pk>/excluir/',
        views.noticia_excluir,
        name='futebol_noticia_excluir',
    ),
    path('atletas/', views.atletas_catalogo, name='futebol_atletas'),
    path('atletas.json', views.catalogo_json, name='futebol_catalogo_json'),
    path('painel/assets/', asset_views.painel_assets, name='futebol_assets'),
    path('assets/<str:kind>/<str:filename>', asset_views.servir_arquivo, name='futebol_asset_arquivo'),
    path('api/teams', asset_views.api_teams, name='api_teams'),
    path('api/teams/<int:pk>', asset_views.api_team_detail, name='api_team_detail'),
    path('api/teams/<int:pk>/logo', asset_views.api_team_logo, name='api_team_logo'),
    path('api/players', asset_views.api_players, name='api_players'),
    path('api/players/<int:pk>', asset_views.api_player_detail, name='api_player_detail'),
    path('api/players/<int:pk>/image', asset_views.api_player_image, name='api_player_image'),
    path('api/assets/status', asset_views.api_assets_status, name='api_assets_status'),
    path('api/assets/missing', asset_views.api_assets_missing, name='api_assets_missing'),
    path('api/sync/status', asset_views.api_sync_status, name='api_sync_status'),
]
