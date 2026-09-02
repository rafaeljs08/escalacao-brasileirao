from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('futebol', '0003_asset_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='atletacatalogo',
            name='funcao',
            field=models.CharField(blank=True, choices=[('GOL', 'Goleiro'), ('LD', 'Lateral direito'), ('LE', 'Lateral esquerdo'), ('LAT', 'Lateral'), ('ZAG', 'Zagueiro'), ('VOL', 'Volante'), ('MC', 'Meia central'), ('MAT', 'Meia-atacante'), ('MD', 'Meia direita'), ('ME', 'Meia esquerda'), ('MEI', 'Meia'), ('PD', 'Ponta direita'), ('PE', 'Ponta esquerda'), ('SA', 'Segundo atacante'), ('CA', 'Centroavante'), ('ATA', 'Atacante')], max_length=4, verbose_name='Função tática'),
        ),
        migrations.AddField(
            model_name='jogador',
            name='funcao',
            field=models.CharField(blank=True, choices=[('GOL', 'Goleiro'), ('LD', 'Lateral direito'), ('LE', 'Lateral esquerdo'), ('LAT', 'Lateral'), ('ZAG', 'Zagueiro'), ('VOL', 'Volante'), ('MC', 'Meia central'), ('MAT', 'Meia-atacante'), ('MD', 'Meia direita'), ('ME', 'Meia esquerda'), ('MEI', 'Meia'), ('PD', 'Ponta direita'), ('PE', 'Ponta esquerda'), ('SA', 'Segundo atacante'), ('CA', 'Centroavante'), ('ATA', 'Atacante')], max_length=4, verbose_name='Função tática'),
        ),
        migrations.AlterField(
            model_name='jogador',
            name='posicao',
            field=models.CharField(choices=[('GOL', 'Goleiro'), ('ZAG', 'Zagueiro'), ('LAT', 'Lateral'), ('MEI', 'Meia'), ('ATA', 'Atacante')], max_length=3, verbose_name='Posição na formação'),
        ),
    ]
