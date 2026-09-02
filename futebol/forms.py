from django import forms

from .models import Escalacao, Jogador, Noticia


class EscalacaoForm(forms.ModelForm):
    class Meta:
        model = Escalacao
        fields = ['nome', 'torcedor', 'formacao']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex.: Seleção dos Sonhos'}),
            'torcedor': forms.TextInput(attrs={'placeholder': 'Seu nome (opcional)'}),
        }


class JogadorForm(forms.ModelForm):
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
