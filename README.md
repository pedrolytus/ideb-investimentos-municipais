# IDEB e investimentos municipais

Trabalho da disciplina de Aprendizado de Máquina Supervisionado (FATESG – Tecnologia em Inteligência Artificial), Problema 4 – Política e Gestão Pública.

Autoria: Pedro Lytus – LYTUS Inteligência de Negócios.

## Pergunta

Quais características dos municípios estão associadas às diferenças no IDEB, e quanto dá para estimar o resultado educacional a partir delas, para apoiar o planejamento orçamentário municipal?

## Recorte

| Item | Escolha |
|---|---|
| Etapa | Ensino fundamental – anos iniciais (5º ano) |
| Rede | Municipal |
| Unidade | 1 linha por município e ano |
| Treino | IDEB 2023 (5.241 municípios) |
| Teste fora do tempo | IDEB 2025 (5.320 municípios) |
| Abrangência | Brasil, com Goiás como estudo de caso |
| Tarefa | Regressão supervisionada |

Modelo principal: Regressão Linear. Modelo desafiante: SVR (kernel RBF). Baseline: média do IDEB por UF.

## Dados

Fonte: [Base dos Dados](https://basedosdados.org/), consultada no Google BigQuery (modo Sandbox, sem custo). A consulta de extração está em `sql/consulta_final.sql` e cruza seis tabelas:

- `br_inep_ideb.municipio`: IDEB (alvo);
- `br_inep_indicadores_educacionais.municipio`: turma, jornada, formação e esforço docente, complexidade de gestão (ano de referência 2022);
- `br_inep_censo_escolar.escola`: matrículas, docentes e infraestrutura da rede municipal;
- `br_me_siconfi.municipio_despesas_funcao`: despesa liquidada com ensino fundamental;
- `br_ibge_populacao.municipio` e `br_ibge_pib.municipio`: população e PIB;
- `br_inep_indicadores_educacionais.escola_nivel_socioeconomico`: INSE 2015.

O resultado da consulta está em `dados/brutos/base_ideb_municipios.csv` (10.561 linhas, 54 colunas). Para refazer a extração, rode a consulta no BigQuery e exporte o resultado em CSV com o mesmo nome.

Variáveis que entram no cálculo do IDEB (taxa de aprovação, notas do SAEB, reprovação, abandono, distorção idade-série) e a meta projetada não são usadas como feature, para evitar vazamento.

## Estrutura

```
├── sql/consulta_final.sql          # extração no BigQuery
├── dados/brutos/                   # CSV exportado
├── dados/processados/              # base limpa (gerada pelo notebook 02)
├── notebooks/
│   ├── 01_negocio_e_exploracao.ipynb
│   ├── 02_preparacao_dados.ipynb
│   ├── 03_modelagem.ipynb
│   └── 04_avaliacao_e_recomendacoes.ipynb
├── figuras/                        # gráficos usados na apresentação
├── docs/diario_do_projeto.md       # decisões, desafios e ajustes
├── colunas_basedosdados.csv        # colunas das tabelas consultadas
└── valores_basedosdados.csv        # valores usados nos filtros
```

## Como rodar

Requer Python 3.11 ou superior.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
jupyter lab
```

Execute os notebooks na ordem numérica. Cada um lê o que o anterior gravou em `dados/processados/` e salva os gráficos em `figuras/`.

## Limitações principais

- Associação não é causalidade: o modelo indica prioridades para investigar, não o efeito de um investimento.
- INSE de 2015 e PIB de 2023 são usados como contexto estrutural nas duas safras.
- Indicadores educacionais de 2023 e 2024 estão corrompidos na Base dos Dados; usamos 2022.
- Dados do Siconfi são autodeclarados.
- Municípios sem IDEB divulgado ficam fora da base.

O histórico completo está em `docs/diario_do_projeto.md`.
