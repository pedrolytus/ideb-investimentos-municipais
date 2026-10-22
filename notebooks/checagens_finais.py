"""Checagens de validação do projeto.

Rode depois de executar os quatro notebooks em ordem:
    python notebooks/checagens_finais.py
Cada checagem imprime OK ou FALHA. O script termina com código 1 se alguma falhar.
"""
import json
import re
import sys
from importlib.metadata import version
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'notebooks'))
import modelagem as md  # noqa: E402

NOTEBOOKS = ['01_negocio_e_exploracao', '02_preparacao_dados', '03_modelagem',
             '04_avaliacao_e_recomendacoes']
PROIBIDAS = ('aprovacao', 'rendimento', 'saeb', 'reprovacao', 'abandono', 'distorcao', 'tdi',
             'promocao', 'repetencia', 'evasao', 'meta_ideb', 'ideb')
resultados = []


def checar(descricao, condicao, detalhe=''):
    resultados.append(bool(condicao))
    print(f"[{'OK' if condicao else 'FALHA'}] {descricao}" + (f' – {detalhe}' if detalhe else ''))


def codigo(nome):
    nb = nbformat.read(RAIZ / 'notebooks' / f'{nome}.ipynb', as_version=4)
    return nb, '\n'.join(c.source for c in nb.cells if c.cell_type == 'code')


print('1. Execução dos notebooks')
for nome in NOTEBOOKS:
    nb, _ = codigo(nome)
    celulas = [c for c in nb.cells if c.cell_type == 'code']
    erros = [o for c in celulas for o in c.get('outputs', []) if o.output_type == 'error']
    ordem = [c.execution_count for c in celulas]
    checar(f'{nome}: executado do início ao fim, sem erro',
           not erros and ordem == list(range(1, len(celulas) + 1)),
           f'{len(celulas)} células de código')

print('\n2. Vazamento de dados')
config = json.loads((RAIZ / 'dados' / 'processados' / 'features.json').read_text(encoding='utf-8'))
features = config['numericas'] + config['categoricas']
checar('Nenhuma feature ligada ao cálculo do IDEB nem a meta projetada',
       not [f for f in features if any(p in f for p in PROIBIDAS)], f'{len(features)} features')
_, cod03 = codigo('03_modelagem')
checar('Notebook 03 não usa a safra de teste',
       'ano_teste' not in cod03 and not re.search(r'==\s*2025', cod03))
checar('Notebook 03 separa o alvo das entradas', 'assert ALVO not in X.columns' in cod03)
_, cod04 = codigo('04_avaliacao_e_recomendacoes')
checar('Notebook 04 nunca ajusta modelo com dados de 2025',
       not re.search(r'\.fit\([^)]*X_te', cod04) and not re.search(r'cross_val_predict\([^)]*X_te', cod04))
checar('Pré-processamento dentro do Pipeline (imputação e escala não aparecem fora dele)',
       'SimpleImputer(' not in cod03 + cod04 and 'StandardScaler(' not in cod03 + cod04)

# Teste de unidade: o pré-processador aprende só com o que recebe no fit
rng = np.random.default_rng(0)
treino_fake = pd.DataFrame({'a': rng.normal(0, 1, 200), 'uf': rng.choice(['GO', 'SP'], 200)})
teste_fake = pd.DataFrame({'a': rng.normal(50, 1, 50), 'uf': ['GO'] * 50})
prep = md.montar_preprocessador(['a'], ['uf']).fit(treino_fake)
w = prep.named_transformers_['num'].named_steps['winsor']
checar('Winsorizador usa os quantis do treino',
       np.isclose(w.limite_sup_[0], np.nanquantile(treino_fake['a'], 0.99)))
checar('Dados de teste não alteram o ajuste (limite superior continua o do treino)',
       np.allclose(prep.transform(teste_fake)[:, 0], prep.transform(teste_fake.assign(a=1e6))[:, 0]))
base_uf = md.BaselineMediaUF(coluna_uf='uf').fit(treino_fake, treino_fake['a'])
checar('Baseline usa a média da UF no treino',
       np.isclose(base_uf.predict(teste_fake)[0], treino_fake.loc[treino_fake['uf'] == 'GO', 'a'].mean()))

print('\n3. Base de modelagem')
base = pd.read_csv(RAIZ / 'dados' / 'processados' / 'base_modelagem.csv')
checar('10.561 linhas (5.241 em 2023 e 5.320 em 2025)',
       len(base) == 10561 and base['ano'].value_counts().to_dict() == {2025: 5320, 2023: 5241})
checar('Sem chave duplicada e alvo sem ausentes',
       not base.duplicated(['ano', 'id_municipio']).any() and base['ideb'].notna().all())
checar('Gasto implausível removido (todo gasto entre R$ 1 mil e R$ 60 mil)',
       np.exp(base['log_gasto_ef_por_aluno'].dropna()).between(1000, 60000).all())

print('\n4. Figuras e diário')
diario = (RAIZ / 'docs' / 'diario_do_projeto.md').read_text(encoding='utf-8')
citadas = set(re.findall(r'figuras/([\w\-]+\.png)', diario))
existentes = {p.name for p in (RAIZ / 'figuras').glob('*.png')}
checar('Toda figura citada no diário existe em figuras/', citadas <= existentes,
       ', '.join(sorted(citadas - existentes)) or f'{len(citadas)} citadas')
checar('Toda figura gerada é citada no diário', existentes <= citadas,
       ', '.join(sorted(existentes - citadas)) or f'{len(existentes)} geradas')

cv = pd.read_csv(RAIZ / 'dados' / 'processados' / 'resultados_cv.csv', index_col=0)
teste = pd.read_csv(RAIZ / 'dados' / 'processados' / 'resultados_teste_2025.csv', index_col=0)
numeros = {
    'RMSE CV da Regressão Linear + UF': cv.loc['Regressão Linear + UF', 'RMSE'],
    'RMSE CV do baseline': cv.loc['Baseline: média da UF', 'RMSE'],
    'RMSE CV da Regressão Linear + região': cv.loc['Regressão Linear + região', 'RMSE'],
    'RMSE 2025 da Regressão Linear + UF': teste.loc['Regressão Linear + UF', 'RMSE'],
    'RMSE 2025 do SVR': teste.loc['SVR ajustado', 'RMSE'],
}
for descricao, valor in numeros.items():
    texto = f'{valor:.3f}'.replace('.', ',')
    checar(f'Diário traz o {descricao} ({texto})', texto in diario)

print('\n5. Ambiente')
fixadas = dict(linha.split('==') for linha in (RAIZ / 'requirements.txt').read_text().splitlines()
               if '==' in linha)
divergentes = {p: (v, version(p)) for p, v in fixadas.items() if version(p) != v}
checar('Versões instaladas iguais às do requirements.txt', not divergentes, str(divergentes or ''))

print(f'\n{sum(resultados)} de {len(resultados)} checagens OK')
sys.exit(0 if all(resultados) else 1)
