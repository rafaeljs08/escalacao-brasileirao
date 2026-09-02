from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Clube(models.Model):
    """Clube da Série A do Campeonato Brasileiro."""

    nome = models.CharField(max_length=60, unique=True)
    sigla = models.CharField(max_length=3)
    cidade = models.CharField(max_length=60)
    estado = models.CharField(max_length=2)
    cor_primaria = models.CharField(max_length=7, default='#111827')
    cor_secundaria = models.CharField(max_length=7, default='#ffffff')
    escudo = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=80, blank=True)
    fonte_id = models.PositiveIntegerField('ID no provider', unique=True, null=True, blank=True)
    logo_url = models.URLField('URL do escudo', max_length=500, blank=True)
    logo_local = models.CharField('Escudo local', max_length=300, blank=True)
    logo_fonte = models.CharField('Fonte do escudo', max_length=40, blank=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Clube'
        verbose_name_plural = 'Clubes'

    def __str__(self):
        return self.nome

    def escudo_publico(self):
        """URL servida pelo Asset Manager, ou o SVG estático do seed."""
        if self.logo_local:
            return f'/assets/{self.logo_local.lstrip("/")}'
        if self.logo_url:
            return self.logo_url
        if self.escudo:
            from django.templatetags.static import static
            return static(self.escudo)
        return '/assets/placeholders/team.png'


class Escalacao(models.Model):
    """Time montado pelo usuário com jogadores de qualquer clube da Série A."""

    FORMACOES = {
        '3-4-3': {'ZAG': 3, 'LAT': 0, 'MEI': 4, 'ATA': 3},
        '3-5-2': {'ZAG': 3, 'LAT': 0, 'MEI': 5, 'ATA': 2},
        '4-3-3': {'ZAG': 2, 'LAT': 2, 'MEI': 3, 'ATA': 3},
        '4-4-2': {'ZAG': 2, 'LAT': 2, 'MEI': 4, 'ATA': 2},
        '4-5-1': {'ZAG': 2, 'LAT': 2, 'MEI': 5, 'ATA': 1},
        '5-3-2': {'ZAG': 3, 'LAT': 2, 'MEI': 3, 'ATA': 2},
        '5-4-1': {'ZAG': 3, 'LAT': 2, 'MEI': 4, 'ATA': 1},
    }
    FORMACAO_CHOICES = [(chave, chave) for chave in FORMACOES]

    nome = models.CharField('Nome do time', max_length=60)
    torcedor = models.CharField('Cartoleiro', max_length=60, blank=True)
    formacao = models.CharField(
        'Formação',
        max_length=10,
        choices=FORMACAO_CHOICES,
        default='4-3-3',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-atualizado_em']
        verbose_name = 'Escalação'
        verbose_name_plural = 'Escalações'

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse('futebol_time', args=[self.pk])

    @property
    def vagas(self):
        """Quantidade de jogadores prevista para cada posição na formação."""
        return {'GOL': 1, **self.FORMACOES[self.formacao]}

    def vagas_posicao(self, posicao):
        return self.vagas.get(posicao, 0)

    def elenco_por_posicao(self, posicao):
        return [j for j in self.jogadores.all() if j.posicao == posicao]

    @property
    def total_escalado(self):
        return sum(
            min(len(self.elenco_por_posicao(pos)), qtd)
            for pos, qtd in self.vagas.items()
        )

    @property
    def total_vagas(self):
        return sum(self.vagas.values())

    @property
    def completo(self):
        return self.total_escalado >= self.total_vagas

    @property
    def progresso(self):
        if not self.total_vagas:
            return 0
        return round(self.total_escalado / self.total_vagas * 100)


class Jogador(models.Model):
    POSICAO_CHOICES = [
        ('GOL', 'Goleiro'),
        ('ZAG', 'Zagueiro'),
        ('LAT', 'Lateral'),
        ('MEI', 'Meia'),
        ('ATA', 'Atacante'),
    ]

    escalacao = models.ForeignKey(
        Escalacao,
        on_delete=models.CASCADE,
        related_name='jogadores',
    )
    clube = models.ForeignKey(
        Clube,
        on_delete=models.PROTECT,
        related_name='jogadores',
        verbose_name='Clube',
    )
    nome = models.CharField('Nome do jogador', max_length=60)
    posicao = models.CharField('Posição', max_length=3, choices=POSICAO_CHOICES)
    numero = models.PositiveSmallIntegerField(
        'Número da camisa',
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )
    gols = models.PositiveIntegerField('Gols', default=0)
    assistencias = models.PositiveIntegerField('Assistências', default=0)
    posse_bola = models.DecimalField(
        'Posse de bola (%)',
        max_digits=5,
        decimal_places=1,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    foto = models.URLField(
        'Foto do jogador (URL)',
        max_length=400,
        blank=True,
        help_text='Cole o endereço de uma imagem. Sem foto, usamos o escudo do clube.',
    )
    capitao = models.BooleanField('Capitão', default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['posicao', 'numero']
        verbose_name = 'Jogador'
        verbose_name_plural = 'Jogadores'

    def __str__(self):
        return f'{self.nome} — {self.get_posicao_display()}'

    def get_absolute_url(self):
        return reverse('futebol_time', args=[self.escalacao_id])

    @property
    def participacoes(self):
        return self.gols + self.assistencias

    def foto_resolvida(self):
        """Foto informada no CRUD, senão a do catálogo/asset manager."""
        if self.foto:
            return self.foto
        catalogo = (
            AtletaCatalogo.objects.filter(nome=self.nome, clube_id=self.clube_id)
            .exclude(foto_local='')
            .first()
        )
        if catalogo:
            return catalogo.foto_publica()
        return ''


class AtletaCatalogo(models.Model):
    """Jogador da Série A disponível para escalar, vindo da API ou do catálogo local."""

    FONTE_CHOICES = [
        ('local', 'Catálogo local'),
        ('cartola', 'Cartola FC'),
        ('artilharia', 'Artilharia (API Futebol)'),
        ('escalacao', 'Escalação de partida (API Futebol)'),
    ]
    FOTO_STATUS = [
        ('ok', 'OK'),
        ('missing', 'MISSING'),
        ('invalid', 'INVALID'),
        ('fallback', 'FALLBACK'),
    ]

    api_id = models.PositiveIntegerField('ID na API Futebol', unique=True, null=True, blank=True)
    fonte_id = models.PositiveIntegerField('ID no provider de assets', unique=True, null=True, blank=True)
    nome = models.CharField('Nome', max_length=80)
    slug = models.SlugField(max_length=120, blank=True)
    clube = models.ForeignKey(
        Clube,
        on_delete=models.CASCADE,
        related_name='catalogo',
        verbose_name='Clube',
    )
    posicao = models.CharField('Posição', max_length=3, choices=Jogador.POSICAO_CHOICES)
    numero = models.PositiveSmallIntegerField('Camisa', null=True, blank=True)
    gols = models.PositiveIntegerField('Gols', default=0)
    fonte = models.CharField('Origem', max_length=20, choices=FONTE_CHOICES, default='local')
    foto_url = models.URLField('URL da foto', max_length=500, blank=True)
    foto_local = models.CharField('Foto local', max_length=300, blank=True)
    foto_fonte = models.CharField('Fonte da foto', max_length=40, blank=True)
    foto_status = models.CharField('Status da foto', max_length=12, choices=FOTO_STATUS, default='missing')
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Atleta do catálogo'
        verbose_name_plural = 'Catálogo de atletas'
        constraints = [
            models.UniqueConstraint(fields=['nome', 'clube'], name='catalogo_nome_clube_unico'),
        ]

    def __str__(self):
        return f'{self.nome} ({self.clube.sigla})'

    def foto_publica(self):
        if self.foto_local:
            return f'/assets/{self.foto_local.lstrip("/")}'
        if self.foto_url:
            return self.foto_url
        return '/assets/placeholders/player.png'


class Noticia(models.Model):
    jogador = models.ForeignKey(
        Jogador,
        on_delete=models.CASCADE,
        related_name='noticias',
    )
    titulo = models.CharField('Título', max_length=160)
    resumo = models.TextField('Resumo', max_length=400)
    data_publicacao = models.DateField('Data', auto_now_add=True)

    class Meta:
        ordering = ['-data_publicacao', '-id']
        verbose_name = 'Notícia'
        verbose_name_plural = 'Notícias'

    def __str__(self):
        return self.titulo


class Asset(models.Model):
    """Registro de auditoria de cada imagem baixada (foto ou escudo)."""

    ENTITY_CHOICES = [
        ('team', 'Clube'),
        ('player', 'Jogador'),
    ]
    KIND_CHOICES = [
        ('logo', 'Escudo'),
        ('photo', 'Foto'),
    ]
    STATUS_CHOICES = [
        ('ok', 'OK'),
        ('missing', 'MISSING'),
        ('invalid', 'INVALID'),
        ('fallback', 'FALLBACK'),
        ('error', 'ERROR'),
    ]

    entity_type = models.CharField(max_length=12, choices=ENTITY_CHOICES)
    entity_id = models.PositiveIntegerField()
    asset_type = models.CharField(max_length=12, choices=KIND_CHOICES)
    url = models.URLField(max_length=500, blank=True)
    local_path = models.CharField(max_length=300, blank=True)
    provider = models.CharField(max_length=40, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    size = models.PositiveIntegerField(default=0)
    mime = models.CharField(max_length=60, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='missing')
    fallback_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['entity_type', 'entity_id']
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
        constraints = [
            models.UniqueConstraint(
                fields=['entity_type', 'entity_id', 'asset_type'],
                name='asset_entidade_tipo_unico',
            ),
        ]

    def __str__(self):
        return f'{self.entity_type}:{self.entity_id}:{self.asset_type}'

    def publico(self):
        if self.local_path:
            return f'/assets/{self.local_path.lstrip("/")}'
        return self.url or ''
