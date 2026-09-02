from django.contrib import admin

from .models import Asset, AtletaCatalogo, Clube, Escalacao, Jogador, Noticia


class JogadorInline(admin.TabularInline):
    model = Jogador
    extra = 0
    fields = ('nome', 'clube', 'posicao', 'numero', 'gols', 'assistencias', 'posse_bola', 'capitao')


class NoticiaInline(admin.TabularInline):
    model = Noticia
    extra = 0
    fields = ('titulo', 'resumo')


@admin.register(Clube)
class ClubeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'cidade', 'estado', 'fonte_id', 'logo_fonte')
    search_fields = ('nome', 'sigla', 'cidade')
    list_filter = ('estado',)


@admin.register(Escalacao)
class EscalacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'torcedor', 'formacao', 'atualizado_em')
    list_filter = ('formacao',)
    search_fields = ('nome', 'torcedor')
    inlines = [JogadorInline]


@admin.register(Jogador)
class JogadorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'clube', 'posicao', 'numero', 'gols', 'assistencias', 'escalacao')
    list_filter = ('posicao', 'clube', 'escalacao')
    search_fields = ('nome',)
    inlines = [NoticiaInline]


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'jogador', 'data_publicacao')
    list_filter = ('data_publicacao',)
    search_fields = ('titulo', 'resumo', 'jogador__nome')


@admin.register(AtletaCatalogo)
class AtletaCatalogoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'clube', 'posicao', 'numero', 'gols', 'fonte', 'foto_status')
    list_filter = ('posicao', 'clube', 'fonte', 'foto_status')
    search_fields = ('nome', 'clube__nome', 'clube__sigla')


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('entity_type', 'entity_id', 'asset_type', 'provider', 'status', 'fallback_used', 'updated_at')
    list_filter = ('entity_type', 'asset_type', 'status', 'provider', 'fallback_used')
    search_fields = ('url', 'local_path')
