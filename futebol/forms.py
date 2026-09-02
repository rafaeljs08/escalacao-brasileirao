from django import forms

from .models import AtletaCatalogo, Escalacao, Jogador, Noticia


class EscalacaoForm(forms.ModelForm):
    class Meta:
        model = Escalacao
        fields = ['nome', 'torcedor', 'formacao']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex.: Seleção dos Sonhos'}),
            'torcedor': forms.TextInput(attrs={'placeholder': 'Seu nome (opcional)'}),
        }


class JogadorForm(forms.ModelForm):
    catalog_id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Jogador
        fields = [
            'nome', 'clube', 'posicao', 'numero',
            'gols', 'assistencias', 'posse_bola', 'foto', 'capitao',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex.: Léo Jardim'}),
            'foto': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }

    def __init__(self, *args, escalacao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.escalacao = escalacao
        self.fields['clube'].empty_label = 'Selecione o clube'
        self._aplicar_catalogo_no_post()

    def _aplicar_catalogo_no_post(self):
        if not self.data:
            return
        bruto = self.data.get('catalog_id')
        if not bruto:
            return
        try:
            catalogo = AtletaCatalogo.objects.select_related('clube').get(pk=int(bruto))
        except (AtletaCatalogo.DoesNotExist, TypeError, ValueError):
            return
        dados = self.data.copy()
        dados['nome'] = catalogo.nome[:60]
        dados['clube'] = str(catalogo.clube_id)
        dados['posicao'] = catalogo.posicao
        if catalogo.numero:
            dados['numero'] = str(catalogo.numero)
        dados['gols'] = str(catalogo.gols)
        if (catalogo.foto_url or '').startswith('http'):
            dados['foto'] = catalogo.foto_url
        self.data = dados

    def clean_posicao(self):
        posicao = self.cleaned_data['posicao']
        if not self.escalacao:
            return posicao

        vagas = self.escalacao.vagas_posicao(posicao)
        label = dict(Jogador.POSICAO_CHOICES)[posicao]

        if vagas == 0:
            raise forms.ValidationError(
                f'A formação {self.escalacao.formacao} não usa {label.lower()}. '
                'Escolha outra posição ou troque a formação do time.'
            )

        ocupadas = self.escalacao.jogadores.filter(posicao=posicao)
        if self.instance.pk:
            ocupadas = ocupadas.exclude(pk=self.instance.pk)

        if ocupadas.count() >= vagas:
            raise forms.ValidationError(
                f'Todas as {vagas} vagas de {label.lower()} já estão preenchidas '
                f'na formação {self.escalacao.formacao}.'
            )
        return posicao


class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'resumo']
        widgets = {
            'titulo': forms.TextInput(attrs={'placeholder': 'Manchete da notícia'}),
            'resumo': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Resumo da notícia'}),
        }
