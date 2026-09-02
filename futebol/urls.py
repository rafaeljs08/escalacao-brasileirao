from django.urls import path

from . import views

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
]
