"""Estilo comum dos gráficos e formatação de números dos notebooks.

Fundo claro e cores testadas para daltonismo (as três primeiras cores
categóricas se distinguem entre si em qualquer combinação).
"""
from pathlib import Path

import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

# Cores categóricas, sempre nesta ordem
AZUL = '#2a78d6'
LARANJA = '#eb6834'
VERDE_AGUA = '#1baf7a'

# Sinal de associação: positivo em azul, negativo em vermelho
POSITIVO = '#2a78d6'
NEGATIVO = '#e34948'

# Destaque: elementos sem ênfase ficam em cinza
CINZA = '#c3c2b7'
CINZA_CLARO = '#e1e0d9'

FUNDO = '#fcfcfb'
TINTA = '#0b0b0b'
TINTA_SEC = '#52514e'
TINTA_MUDA = '#898781'

# Escala divergente para correlações: vermelho (-1) / cinza (0) / azul (+1)
DIVERGENTE = LinearSegmentedColormap.from_list(
    'divergente', ['#b42f2f', '#ee8a89', '#f0efec', '#6da7ec', '#184f95']
)

# Nomes legíveis das variáveis para gráficos e tabelas
ROTULOS = {
    'ideb': 'IDEB',
    'inse_medio_2015': 'INSE 2015',
    'pib_per_capita_2023': 'PIB per capita',
    'log_pib_per_capita': 'PIB per capita (log)',
    'populacao': 'População',
    'log_populacao': 'População (log)',
    'pct_matr_residencia_rural': '% matrículas de residentes rurais',
    'pct_matr_transporte_publico': '% matrículas com transporte público',
    'pct_matr_integral_ai': '% matrículas em tempo integral',
    'n_escolas_ai': 'Nº de escolas (anos iniciais)',
    'log_n_escolas_ai': 'Nº de escolas (log)',
    'matriculas_ai': 'Matrículas (anos iniciais)',
    'log_matriculas_ai': 'Matrículas anos iniciais (log)',
    'alunos_por_docente_ai': 'Alunos por docente',
    'atu_ef_anos_iniciais': 'Alunos por turma',
    'had_ef_anos_iniciais': 'Horas-aula por dia',
    'dsu_ef_anos_iniciais': '% docentes com superior',
    'afd_ef_anos_iniciais_grupo_1': '% docentes com formação adequada (AFD 1)',
    'afd_ef_anos_iniciais_grupo_2': '% docentes AFD grupo 2',
    'afd_ef_anos_iniciais_grupo_3': '% docentes AFD grupo 3',
    'afd_ef_anos_iniciais_grupo_4': '% docentes AFD grupo 4',
    'afd_ef_anos_iniciais_grupo_5': '% docentes sem superior (AFD 5)',
    'pct_formacao_adequada': '% docentes com formação adequada',
    'ied_medio': 'Esforço docente médio (IED)',
    'icg_medio': 'Complexidade de gestão média (ICG)',
    'ird_alta': '% docentes com alta regularidade',
    'ird_baixa_regularidade': '% docentes com baixa regularidade',
    'ird_medio': 'Regularidade docente média (IRD)',
    'pct_esc_biblioteca': '% escolas com biblioteca',
    'pct_esc_lab_informatica': '% escolas com lab. de informática',
    'pct_esc_lab_ciencias': '% escolas com lab. de ciências',
    'pct_esc_quadra': '% escolas com quadra',
    'pct_esc_internet_alunos': '% escolas com internet para alunos',
    'pct_esc_banda_larga': '% escolas com banda larga',
    'pct_esc_esgoto_rede': '% escolas com esgoto da rede',
    'pct_esc_agua_potavel': '% escolas com água potável',
    'pct_esc_energia_rede': '% escolas com energia da rede',
    'infra_basica': 'Infraestrutura básica (índice)',
    'infra_pedagogica': 'Infraestrutura pedagógica (índice)',
    'gasto_ef_por_aluno': 'Gasto EF por aluno',
    'log_gasto_ef_por_aluno': 'Gasto EF por aluno (log)',
}
for _i in range(1, 7):
    ROTULOS[f'ied_ef_anos_iniciais_nivel_{_i}'] = f'% docentes com esforço nível {_i}'
    ROTULOS[f'icg_nivel_{_i}'] = f'% escolas com gestão nível {_i}'
ROTULOS['ird_media_baixa'] = '% docentes com regularidade média-baixa'
ROTULOS['ird_media_alta'] = '% docentes com regularidade média-alta'


def rotulo(coluna):
    if coluna.startswith('regiao_'):
        return 'Região ' + coluna.removeprefix('regiao_')
    return ROTULOS.get(coluna, coluna)


def br(valor, casas=0):
    """Formata um número no padrão brasileiro (1.234,5)."""
    texto = f'{valor:,.{casas}f}'
    return texto.replace(',', 'X').replace('.', ',').replace('X', '.')


def aplicar_estilo():
    mpl.rcParams.update({
        'figure.facecolor': FUNDO,
        'axes.facecolor': FUNDO,
        'savefig.facecolor': FUNDO,
        'axes.edgecolor': CINZA,
        'axes.linewidth': 0.8,
        'axes.labelcolor': TINTA_SEC,
        'axes.titlecolor': TINTA,
        'axes.titlesize': 13,
        'axes.titleweight': 'semibold',
        'axes.titlelocation': 'left',
        'axes.titlepad': 12,
        'axes.labelsize': 11,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'axes.axisbelow': True,
        'grid.color': CINZA_CLARO,
        'grid.linewidth': 0.6,
        'xtick.color': TINTA_MUDA,
        'ytick.color': TINTA_MUDA,
        'xtick.labelcolor': TINTA_SEC,
        'ytick.labelcolor': TINTA_SEC,
        'text.color': TINTA,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Segoe UI', 'Helvetica', 'Arial', 'DejaVu Sans'],
        'font.size': 11,
        'legend.frameon': False,
        'legend.fontsize': 10,
        'lines.linewidth': 2,
        'figure.dpi': 100,
        'savefig.dpi': 200,
        'savefig.bbox': 'tight',
    })


def salvar_figura(fig, nome, pasta):
    """Salva a figura em PNG na pasta indicada e devolve o caminho."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f'{nome}.png'
    fig.savefig(caminho)
    return caminho
