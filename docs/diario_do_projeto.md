# Diário do projeto – Problema 4: planejamento de investimentos municipais

Registro cronológico do que foi feito, das decisões, dos desafios e dos ajustes. É a fonte principal para o **guia da apresentação** e para os **slides**.

> Regra de manutenção: toda etapa nova entra no fim da seção "Registro da implementação", no formato do modelo. Não apagar entradas antigas. Quando uma decisão mudar, registrar a mudança e o motivo.

---

## Fase 1 – Entendimento do problema (21/10/2026)

**O que fizemos**
- Lemos o enunciado do desafio de consultoria (12 problemas, trabalho em dupla, avaliação do professor e por pares).
- Escolhemos o **Problema 4 – Política e Gestão Pública**: entender os fatores associados às diferenças de desempenho educacional entre municípios para apoiar o planejamento orçamentário.

**Leitura do problema**
- O pedido é **estimar** o resultado educacional (IDEB) a partir de características do município. O alvo é numérico e contínuo, então a tarefa é **regressão supervisionada**.
- O enunciado cobra explicitamente a diferença entre **associação e causalidade**: um gasto maior associado a um IDEB maior não prova que o gasto causou a melhora.

---

## Fase 2 – Busca e escolha dos dados (21/10/2026)

**Opções avaliadas**
1. Baixar planilhas soltas em cada órgão (INEP, FNDE/SIOPE, IBGE) e cruzar à mão.
2. Usar a **Base dos Dados**, que publica essas bases já tratadas e padronizadas pelo código IBGE do município, consultáveis por SQL no Google BigQuery.
3. Gerar dados sintéticos (o enunciado permite).

**Decisão:** Base dos Dados + BigQuery.
- Junta 5 fontes oficiais com uma consulta só, usando o mesmo código de município.
- Reduz muito o risco de erro no cruzamento manual.

**Por que não usamos dados sintéticos**
- Numa base simulada, as relações entre as variáveis são as que nós programamos. O modelo apenas "redescobriria" nossas premissas, e a interpretação perderia valor.
- Existem dados públicos reais e de boa qualidade para o problema, o que pesa nos critérios de compreensão do negócio e interpretação.
- Sintéticos ficaram só como plano B (se o acesso falhasse) ou para testar código.

**Fontes oficiais usadas**

| Bloco | Fonte original | Tabela na Base dos Dados |
|---|---|---|
| IDEB (alvo) | INEP | `br_inep_ideb.municipio` |
| Professores, turmas e gestão | INEP – Indicadores Educacionais | `br_inep_indicadores_educacionais.municipio` |
| Infraestrutura e matrículas | INEP – Censo Escolar | `br_inep_censo_escolar.escola` |
| Nível socioeconômico | INEP – INSE | `br_inep_indicadores_educacionais.escola_nivel_socioeconomico` |
| Gasto com educação | Tesouro Nacional – Siconfi/Finbra | `br_me_siconfi.municipio_despesas_funcao` |
| População e PIB | IBGE | `br_ibge_populacao.municipio`, `br_ibge_pib.municipio` |

---

## Fase 3 – Definição do recorte (21/10/2026)

**Primeira ideia:** analisar o 9º ano do fundamental e a 3ª série do ensino médio.

**Desafio encontrado:** a responsabilidade por cada etapa não é a mesma.
- O **ensino médio** é quase todo oferecido pela **rede estadual**. O gasto da prefeitura não explica esse resultado, e o gasto estadual só existe por estado (todos os municípios do mesmo estado teriam o mesmo valor).
- Nos **anos finais (6º ao 9º)**, prefeitura e estado **dividem** a oferta, em proporções que variam muito (em Goiás o estado ainda tem parte grande dessa etapa).
- O município é responsável **prioritariamente** pela educação infantil e pelo ensino fundamental, e o IDEB não mede a educação infantil.

**Ajuste:** recorte final em **anos iniciais (5º ano), rede municipal**. É a etapa mais "municipal" e conversa diretamente com o tema "investimentos municipais".

**Outros filtros avaliados**

| Opção | Resultado |
|---|---|
| Só Goiás | Descartado como base de treino: 246 municípios é pouco para cerca de 15 variáveis. Goiás vira **estudo de caso** na recomendação. |
| Só Centro-Oeste | Descartado: cerca de 467 municípios, perde variedade sem ganho claro. |
| 5º e 9º ano juntos | Descartado como modelo principal: no 9º ano muitos municípios não têm rede municipal com nota. |
| **Brasil, anos iniciais, rede municipal** | **Escolhido:** cerca de 5.400 municípios por ano. |

**Anos:** IDEB 2023 para treino e IDEB 2025 (divulgado em agosto de 2026) para validação fora do tempo. 2021 ficou fora por causa das distorções da pandemia.

---

## Fase 4 – Infraestrutura: nuvem ou máquina local? (21/10/2026)

**Decisão:** modelo híbrido.
- O BigQuery serve só para **extrair** e cruzar os dados.
- A análise roda **localmente**: a base final é pequena (cerca de 10.800 linhas, poucos MB), e assim o projeto fica versionado na pasta, sem depender de internet nem de cota.

**Custo:** zero. O projeto usa o **BigQuery Sandbox**, sem cartão de crédito, com 1 TB de consulta grátis por mês e 10 GB de armazenamento. As tabelas criadas no Sandbox expiram em 60 dias, por isso exportamos tudo em CSV.

---

## Fase 5 – Configuração do Google Cloud (21/10/2026)

**Passos**
1. Acesso ao console do BigQuery.
2. **Desafio:** o console abriu num projeto já existente da conta (vinculado a outros serviços e possivelmente com faturamento ativo).
3. **Ajuste:** criamos um projeto dedicado, `ml-ideb-municipios`, sem organização e sem faturamento. Isso isola o trabalho e garante o modo gratuito.
4. Ativação da BigQuery API e confirmação do selo **Sandbox** no console.

---

## Fase 6 – Mapeamento das tabelas (21–22/10/2026)

**Desafio:** não sabíamos os nomes exatos das colunas, e uma consulta com nome errado falha ou volta vazia.

**Solução:** consultamos os metadados (`INFORMATION_SCHEMA.COLUMNS`) das 6 bases.
- Resultado: **2.456 colunas** mapeadas, com **60 MB** processados (cerca de 0,006% da cota mensal).
- Arquivo: `colunas_basedosdados.csv`.

**Dúvida resolvida:** o download local em CSV tem limite de 10 MB. Esse limite vale para o **tamanho do resultado** (o nosso tinha cerca de 160 KB), não para o volume processado pela consulta (60 MB).

**Descoberta útil:** a tabela de escolas do Censo já traz as contagens de matrículas e de professores. Assim evitamos as tabelas de matrícula aluno a aluno, que têm milhões de linhas e consumiriam muita cota.

---

## Fase 7 – Validação dos valores dos filtros (22/10/2026)

**Desafio:** precisávamos dos valores exatos dos filtros (como a rede está escrita, quais anos existem, como se chama a conta do ensino fundamental) para a consulta final não voltar vazia.

**Solução:** uma consulta curta listando os valores distintos de cada campo. Arquivo: `valores_basedosdados.csv`.

**Descobertas e ajustes**

| Descoberta | Impacto | Ajuste |
|---|---|---|
| INSE só existe para 2014 e 2015 | Não há nível socioeconômico recente | Usamos o INSE 2015 como proxy estrutural e registramos como limitação. PIB per capita reforça o contexto socioeconômico. |
| Indicadores educacionais só até 2024 | Faltam dados de 2025 | As linhas de 2025 usam os indicadores de 2024. |
| PIB municipal só até 2023 | Falta PIB de 2025 | 2023 e 2025 usam o PIB de 2023. |
| No Censo, a rede aparece como código | Filtro por texto não funcionaria | Rede municipal = código `'3'`. |
| Rede e localização com maiúsculas e minúsculas misturadas | Filtro poderia perder linhas | Comparação com `LOWER()` e remoção de duplicados. |
| SIOPE não está na Base dos Dados | Precisaríamos baixar município por município | Substituído pelo **Siconfi/Finbra**: conta `3.12.361 – Ensino Fundamental`, estágio "Despesas Liquidadas". |

---

## Fase 8 – Escolha dos modelos (22/10/2026)

A disciplina limita a escolha a 6 métodos: Mean Shift, GMM, DBSCAN, Regressão Linear, Regressão Logística e SVM.

| Modelo | Decisão | Justificativa |
|---|---|---|
| Regressão Linear | **Principal** | O alvo é contínuo. Os coeficientes mostram quanto cada fator está associado ao IDEB, que é o que a gestão pública precisa saber. É fácil de explicar. |
| SVM (versão de regressão, SVR) | **Desafiante** | Capta relações não lineares (ex.: gasto com retorno decrescente). Em compensação, é pouco interpretável. |
| Regressão Logística | Alternativa | Só serve se a pergunta virar classificação (ex.: "atingiu IDEB ≥ 6?"). |
| GMM, DBSCAN, Mean Shift | Descartados como principal | São agrupamentos não supervisionados e não estimam o IDEB. GMM pode entrar como análise complementar de perfis de municípios. |

**Debate previsto para a apresentação:** se o SVR errar menos, vale perder interpretabilidade num contexto de planejamento público?

**Validação:** KFold (k=5) no treino 2023, com RMSE, MAE e R², comparando com um baseline (média do IDEB por UF). Depois, um teste único em 2025.

---

## Fase 9 – Prevenção de vazamento de dados (22/10/2026)

O IDEB é calculado como **nota do SAEB × taxa de aprovação**. Se essas variáveis entrassem no modelo, ele "acertaria" sem aprender nada útil.

**Excluídas por decisão de projeto:** taxa de aprovação, indicador de rendimento, notas do SAEB, reprovação, abandono, distorção idade-série, promoção, repetência, evasão e a meta projetada do IDEB.

Esse cuidado atende diretamente ao critério "prevenção de vazamento de dados".

---

## Fase 10 – Consulta final de extração (22/10/2026)

- Arquivo: `sql/consulta_final.sql`.
- Junta as 6 fontes numa tabela com uma linha por município e ano (2023 e 2025).
- Variáveis derivadas já na consulta: gasto com ensino fundamental por aluno, alunos por professor, % de escolas com cada item de infraestrutura, % de matrículas em tempo integral, PIB per capita.
- Saída esperada: `dados/brutos/base_ideb_municipios.csv`.

---

## Registro da implementação

> A partir daqui, cada etapa da implementação (extração, EDA, preparação, modelagem, avaliação) entra como uma nova entrada, neste formato:
>
> ### Fase N – Título (data)
>
> - **O que fizemos:** ...
> - **Por quê:** ...
> - **Desafio:** ... (se houve)
> - **Ajuste/solução:** ...
> - **Resultado:** números concretos (linhas, métricas, % de ausentes etc.)
> - **Para a apresentação:** a frase ou o gráfico que vale mostrar (com caminho em `figuras/`).

### Fase 11 – Primeira extração e validação da base (22/10/2026)

**O que fizemos:** rodamos a consulta final, exportamos `dados/brutos/base_ideb_municipios.csv` e validamos o arquivo antes de qualquer modelagem.

**Resultado geral**
- 10.561 linhas e 56 colunas: 5.241 municípios em 2023 e 5.320 em 2025, cobrindo 26 UFs (o DF não tem rede municipal).
- Nenhuma chave duplicada (ano + município).
- IDEB entre 2,5 e 10,0, com mediana 6,0.
- PIB per capita com mediana de cerca de R$ 29,5 mil, o que confirma que o PIB está em reais.

**Desafios encontrados e ajustes**

| Problema | Diagnóstico | Ajuste |
|---|---|---|
| Indicadores educacionais incoerentes | Alunos por turma com mediana de 10 e máximo de 100. Goiânia aparece com 4 alunos por turma. Horas-aula por dia com mediana 0. Formação docente e complexidade de gestão com 98% de vazios. | Suspeita de colunas desalinhadas ou de linhas duplicadas com grafias diferentes de rede e localização na Base dos Dados. Fizemos uma consulta de diagnóstico para Goiânia antes de corrigir. |
| Gasto por aluno superestimado | O denominador só contava escolas com anos iniciais. Escolas municipais só de anos finais ficavam de fora, inflando o gasto por aluno (mediana de R$ 17,3 mil). | Criamos um bloco separado (`censo_ef`) com todas as matrículas do ensino fundamental da rede municipal. |
| Gasto igual a zero | 118 municípios com despesa zero na conta de ensino fundamental (provável lançamento em outra subfunção). | O gasto zero passa a ser tratado como ausente (`NULLIF`). |
| `computadores_por_aluno` vazio | A coluna do Censo não vem preenchida nos anos recentes. | Removida. |
| `pct_esc_coordenador` vazio em 2025 | Campo descontinuado no Censo 2025. | Removido, para manter os dois anos comparáveis. |
| `meta_ideb` vazia | O INEP só projetou metas até 2021. | Mantida apenas como registro, nunca como feature. |

**Ponto de atenção para a análise:** dezenas de municípios do Ceará e de Alagoas têm IDEB entre 9 e 10, acima do resto do país. Isso não é erro de extração, mas é um padrão a investigar na EDA (políticas estaduais de alfabetização, como o PAIC no Ceará, e a hipótese de distorções de participação no SAEB). Também pode influenciar o modelo como outlier.

**Para a apresentação:** a validação antes de modelar evitou treinar com indicadores corrompidos e com gasto por aluno inflado. É um bom exemplo do critério "qualidade dos dados".

### Fase 12 – Diagnóstico dos indicadores educacionais (22/10/2026)

**O que fizemos:** consultamos todas as linhas de Goiânia (código 5208707) na tabela de indicadores educacionais para 2019, 2022, 2023 e 2024, comparando redes e localizações.

**Diagnóstico**
- **2019 e 2022 estão coerentes.** Rede municipal de Goiânia em 2022: 24,5 alunos por turma, 5,2 horas-aula por dia, 96,3% dos docentes com ensino superior e 90,5% com formação adequada. São valores compatíveis com a realidade.
- **2023 e 2024 estão corrompidos na Base dos Dados.** Esses anos foram carregados com outra grafia (`Municipal`, `Total`, com inicial maiúscula) e com os valores trocados de coluna. A rede municipal aparece com 4 alunos por turma e 2,2 horas-aula, e a distorção idade-série surge em colunas erradas. A rede estadual aparece com 0 horas-aula.
- Conclusão: não é um problema da nossa consulta, e sim da carga desses anos na fonte intermediária. Por isso a validação foi feita município por município, comparando com anos anteriores.

**Opções avaliadas**

| Opção | Prós | Contras |
|---|---|---|
| Usar os indicadores de 2022 para as duas safras | Simples, dados confiáveis, mesma fonte | Defasagem de 1 ano no treino (2023) e de 3 anos no teste (2025) |
| Baixar os arquivos de 2023 e 2024 direto do site do INEP | Dados atuais e oficiais | Vários downloads manuais e mais trabalho de integração |
| Recalcular a partir dos microdados do Censo | Controle total | Tabelas muito grandes e regras de cálculo do INEP complexas |

**Decisão:** usar os indicadores de **2022** nas duas safras. Formação docente, tamanho de turma e jornada mudam devagar, então funcionam como características estruturais da rede. As variáveis que mudam ano a ano (matrículas, alunos por docente, tempo integral e infraestrutura) continuam vindo do Censo do próprio ano.

**Limitação registrada:** a defasagem maior no teste de 2025 pode reduzir o desempenho fora do tempo. Se der tempo, a substituição pelos arquivos oficiais do INEP de 2023 e 2024 fica como melhoria.

**Para a apresentação:** mostrar lado a lado os valores de Goiânia em 2022 e em 2023. É um exemplo concreto de por que validar a fonte, mesmo quando ela é "oficial e tratada".

### Fase 13 – Extração final e validação aprovada (22/10/2026)

**O que fizemos:** rodamos a consulta corrigida, substituímos `dados/brutos/base_ideb_municipios.csv` e repetimos a validação.

**Resultado**
- 10.561 linhas (5.241 municípios em 2023 e 5.320 em 2025), 54 colunas e nenhuma chave duplicada.
- Indicadores educacionais agora coerentes e quase completos (menos de 0,2% de vazios): alunos por turma com mediana de 19,3, horas-aula por dia com mediana de 4,5 e 94% dos docentes com ensino superior (mediana).
- Conferência com Goiânia: 24,5 alunos por turma, 5,2 horas-aula, 96,3% dos docentes com superior e IDEB de 6,5 (2023) e 6,6 (2025).
- Gasto com ensino fundamental por aluno: mediana de R$ 15,5 mil (antes da correção do denominador era R$ 17,3 mil). Goiânia ficou com R$ 13,7 mil em 2023 e R$ 17,1 mil em 2025.
- Vazios: gasto por aluno em 2,4% das linhas (municípios sem declaração ou com despesa zero no Siconfi), INSE em 4,7%, os demais abaixo de 1%.

**Pontos que ficam para a preparação dos dados**
- O gasto por aluno tem valores implausíveis nas pontas: 13 municípios abaixo de R$ 1 mil e 2 acima de R$ 60 mil. Os percentis 1% e 99% são R$ 7 mil e R$ 38,6 mil. Tratar como erro de declaração (ausente ou winsorização) e documentar.
- Cerca de 80 municípios do Ceará e de Alagoas têm IDEB entre 9 e 10. Investigar na EDA.
- `meta_ideb` está 100% vazia (o INEP não projeta metas depois de 2021) e não entra no modelo.

**Para a apresentação:** a base final saiu de 5 fontes oficiais, com custo zero, e passou por duas rodadas de validação antes da modelagem.

### Fase 14 – Ambiente e versionamento (22/10/2026)

**O que fizemos:** criamos o ambiente virtual `.venv` com Python 3.14.4, instalamos os pacotes de análise, fixamos as versões em `requirements.txt`, escrevemos o `README.md` e o `.gitignore` e iniciamos o repositório git com um commit inicial.

**Por quê:** com as versões fixadas, qualquer pessoa da dupla (ou o professor) recria o mesmo ambiente com um comando e obtém os mesmos resultados. O git guarda o histórico das decisões junto com o código.

**Decisão:** versionar a base bruta (`dados/brutos/base_ideb_municipios.csv`, cerca de 4 MB) no repositório. Refazer a extração exige uma conta no BigQuery, e as tabelas do Sandbox expiram em 60 dias. Com o CSV no repositório, os notebooks rodam sem acesso à nuvem. Só ficam fora do git o ambiente virtual, caches e arquivos de credenciais.

**Resultado:** versões usadas: pandas 3.1.0, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1, statsmodels 0.15.0, matplotlib 3.11.2, seaborn 0.13.2, jupyter 1.1.1.

**Para a apresentação:** o projeto é reprodutível: consulta SQL, dados brutos, ambiente e notebooks estão versionados juntos.

### Fase 15 – Entendimento do negócio e análise exploratória (22/10/2026)

**O que fizemos:** escrevemos o notebook `01_negocio_e_exploracao.ipynb`, com a análise do negócio (quem decide, que decisão o modelo apoia, variáveis e fatores externos), a formulação do problema e a exploração da base: cobertura, ausentes, unidades, valores implausíveis, distribuição do IDEB, diferenças por UF, correlações e uma primeira análise de confusão entre gasto e nível socioeconômico.

**Por quê:** antes de preparar os dados precisávamos saber o que limpar, quais variáveis são redundantes e se a relação entre gasto e IDEB resiste ao contexto socioeconômico, que é a pergunta central do gestor.

**Decisão de método:** as relações com o IDEB foram exploradas só na safra 2023 (treino). Em 2025 olhamos apenas cobertura e qualidade das features. Assim o teste fora do tempo continua "virgem". Na exploração rápida que fizemos antes de fixar essa regra, chegamos a calcular a média do IDEB 2025 (6,18, contra 5,79 em 2023). Registramos isso por transparência. Esse número não foi usado em nenhuma escolha de modelagem, e o viés do modelo em 2025 será medido no notebook 04.

**Resultado**
- 5.241 municípios em 2023, em 26 UFs. 329 municípios (5,9% do país) não têm IDEB da rede municipal, o que gera viés de seleção.
- IDEB 2023: média 5,79, mediana 5,8, desvio 0,95. 46% dos municípios atingem 6,0.
- Diferença regional grande: média de 4,77 no Norte e 6,35 no Sul. Goiás tem a 6ª maior mediana entre as 26 UFs (6,2).
- Variáveis mais associadas ao IDEB (Spearman): INSE 0,57, % de escolas com quadra 0,45, com biblioteca 0,44, % de docentes sem superior −0,41, com superior 0,40, PIB per capita 0,39. Gasto por aluno: 0,25.
- Confusão entre gasto e contexto: no 5º quintil de gasto, 45% dos municípios são de INSE alto e 14% de INSE baixo. Numa regressão exploratória, dobrar o gasto por aluno acompanha +0,41 ponto de IDEB sem controles, +0,20 controlando INSE e PIB per capita e +0,11 comparando dentro da mesma UF.
- Ceará: todos os municípios com INSE ficam acima da tendência nacional entre INSE e IDEB, em média 1,82 ponto acima. Alagoas: 90%, com 1,06 ponto. Dos 28 municípios com IDEB ≥ 8,5, 24 são do CE ou de AL.

**Desafios e ajustes**

| Problema | Diagnóstico | Ajuste |
|---|---|---|
| Gasto por aluno com erros de declaração | 15 linhas implausíveis. O pior caso é um município mineiro de 136 mil habitantes com R$ 1,28 bilhão declarados em ensino fundamental (R$ 191 mil por aluno). Outros declaram menos de R$ 50 por aluno. | Abaixo de R$ 1 mil ou acima de R$ 60 mil vira ausente. O restante será limitado em p1/p99 do treino, dentro do pipeline. |
| Gasto de 2025 mais incompleto | Ausente em 4,1% das linhas de 2025 contra 0,65% em 2023: a declaração do Siconfi de 2025 ainda não está completa. | Imputação pela mediana do treino. Registrado como limitação do teste. |
| Escalas diferentes | As colunas `pct_esc_*` vêm em fração (0 a 1), e as demais porcentagens em 0 a 100. | Converter para 0 a 100 no notebook 02. |
| Colunas redundantes | AFD, IED, ICG e IRD somam 100% em cada grupo. % com superior e % sem superior têm correlação de −0,98. População e número de escolas: 0,80. | Resumir cada grupo num indicador e remover os espelhos. |
| Instabilidade de redes pequenas | Em 2023 a dispersão do IDEB não cresce nas redes pequenas (desvio de 0,86 no quintil menor e 0,96 no maior). A instabilidade é entre edições, e só dá para medir com o IDEB 2025. | Hipótese levada para o notebook 04: erro do modelo por tamanho de rede. |
| Municípios com IDEB entre 9 e 10 | Concentrados no CE e em AL, ligados à política estadual de alfabetização. Não é erro de extração. | Mantidos. O erro do modelo nesses municípios será acompanhado, e vamos testar UF no lugar de região. |

**Para a apresentação**
- `figuras/01_ideb_por_uf_2023.png`: a desigualdade entre UFs, com Goiás e Ceará em destaque.
- `figuras/01_inse_vs_ideb_ceara.png`: o nível socioeconômico explica muito, mas o Ceará fura a tendência. Bom gancho para discutir fatores externos (política estadual).
- `figuras/01_gasto_vs_ideb_por_inse.png`: o slide de "associação não é causalidade". O gasto parece importar muito quando se olha tudo junto, e bem menos dentro de cada faixa socioeconômica.
- `figuras/01_correlacoes_spearman_ideb.png` e `figuras/01_correlacoes_entre_features.png`: o que está associado ao IDEB e onde há redundância.
- `figuras/01_ideb_distribuicao_2023.png`: distribuição do alvo e a meta 6,0.

### Fase 16 – Preparação dos dados (22/10/2026)

**O que fizemos:** no notebook `02_preparacao_dados.ipynb` aplicamos as regras fixas de limpeza, convertemos escalas, resumimos os grupos de colunas e criamos as features derivadas. Gravamos `dados/processados/base_modelagem.csv` (10.561 linhas, 29 colunas) e `dados/processados/features.json`, com a lista de features que os notebooks 03 e 04 usam. Também criamos `notebooks/modelagem.py`, com o winsorizador, o baseline por UF, o pré-processador e as métricas.

**Por quê:** separamos o que não aprende com os dados (regras fixas, aplicadas aqui) do que aprende (winsorização, imputação, padronização). Esse segundo grupo fica dentro do `Pipeline`, ajustado só no treino de cada dobra. É o que garante que nem a validação cruzada nem o teste de 2025 vazem informação para o ajuste.

**Decisões**

| Tema | Decisão | Motivo |
|---|---|---|
| Gasto implausível | Abaixo de R$ 1 mil ou acima de R$ 60 mil por aluno vira ausente (9 linhas em 2023, 6 em 2025) | Erro de declaração. Os limites são fixos e muito distantes de p1 e p99, então não dependem da amostra |
| Demais extremos | Winsorização em p1/p99 de todas as features numéricas, dentro do pipeline | Reduz a influência de pontos extremos na Regressão Linear sem descartar municípios |
| Escala | 12 colunas de fração (infraestrutura e matrículas) passaram para 0 a 100 | Mesma leitura para todas as porcentagens |
| Grupos que somam 100% | 21 colunas viraram 4 indicadores: % de formação adequada (AFD 1) e médias ponderadas pelo nível de IED, ICG e IRD | Elimina a colinearidade perfeita e reduz a dimensão |
| Redundâncias | Saíram % sem superior (−0,98 com % com superior) e número de escolas (substituído por alunos por escola) | Evitar coeficientes instáveis |
| Água e energia | Viraram um indicador só (`infra_basica`) | São quase universais (mediana de 100%) e marcam apenas as redes mais precárias |
| Logaritmo | População, PIB per capita, gasto por aluno e alunos por escola | Variáveis muito assimétricas |

**Resultado:** 24 features numéricas em 5 grupos (contexto, escala e oferta, professores e gestão, infraestrutura e gasto), mais a região em one-hot. Nenhum par de features passa de 0,75 de correlação no treino (o maior é INSE × PIB per capita, 0,71). Ausentes que serão imputados pela mediana do treino: INSE em 236 municípios em 2023 (4,5%) e 257 em 2025 (4,8%); gasto por aluno em 43 (0,8%) e 224 (4,2%); as demais abaixo de 0,2%.

**Para a apresentação:** `figuras/02_gasto_por_aluno_tratamento.png` mostra os gastos declarados em escala log, com os 15 valores implausíveis destacados. Vale explicar a divisão "regra fixa fora do pipeline, ajuste aprendido dentro do pipeline" como a forma concreta de prevenir vazamento.

### Fase 17 – Modelagem: baseline, Regressão Linear e SVR (22/10/2026)

**O que fizemos:** no notebook `03_modelagem.ipynb` comparamos, com as mesmas 5 dobras (KFold embaralhado, `random_state = 42`) e só com a safra 2023: o baseline pela média da UF, a Regressão Linear com região, a Regressão Linear com UF, o SVR com hiperparâmetros padrão e o SVR ajustado por GridSearchCV (36 combinações de `C`, `epsilon` e `gamma`). Para o SVR ajustado usamos validação cruzada aninhada, para que o erro reportado não seja o mesmo usado na escolha dos hiperparâmetros. Também medimos o ganho de cada bloco de variáveis, o VIF e os resíduos, e fizemos uma Regressão Logística complementar (IDEB ≥ 6).

**Desafio (o principal da modelagem):** a Regressão Linear planejada, com as 24 features e a região em one-hot, **errou mais que o baseline** que só conhece a UF (RMSE de 0,733 contra 0,686). A região é grossa demais: o Nordeste junta o Ceará, muito acima da tendência, com estados abaixo dela. O que diferencia os estados (política de alfabetização, regime de colaboração, ICMS educacional) não aparece em nenhuma variável municipal.

**Ajuste (mudança de decisão):** trocamos a região pela **UF em one-hot**. Com isso, a Regressão Linear passou a errar 6,5% menos que o baseline (RMSE de 0,642), e os coeficientes passaram a comparar municípios dentro do mesmo estado. A especificação planejada (região) continua no notebook, para mostrar o problema.

**Resultado (validação cruzada 2023)**

| Modelo | RMSE | MAE | R² |
|---|---|---|---|
| Baseline: média da UF | 0,686 | 0,523 | 0,475 |
| Regressão Linear + região | 0,733 | 0,543 | 0,402 |
| **Regressão Linear + UF (principal)** | **0,642** | 0,484 | **0,541** |
| SVR padrão | 0,660 | 0,490 | 0,514 |
| SVR ajustado (validação aninhada) | 0,645 | 0,478 | 0,537 |

- Ganho por bloco, adicionando um de cada vez depois da UF: contexto socioeconômico +0,038 de R², escala +0,010, professores e gestão +0,009, infraestrutura +0,008 e gasto 0,000.
- VIF máximo de 4,93 (INSE). Nenhuma feature passa de 5.
- Melhor SVR: `C = 10`, `epsilon = 0,5`, `gamma = 0,01`. Ficou na borda da grade, mas as 8 melhores combinações estão a menos de 0,005 de RMSE entre si, abaixo da variação entre dobras (cerca de 0,017).
- Resíduos: os 28 municípios com IDEB ≥ 8,5 são todos subestimados (erro médio de 2,75 pontos). O Nordeste tem o maior erro (MAE de 0,58, contra 0,40 no Sudeste).
- Regressão Logística (IDEB ≥ 6): ROC AUC de 0,878, contra 0,839 do baseline por UF.
- O GridSearch aninhado levou cerca de 5 minutos em 8 núcleos.

**Decisão:** a Regressão Linear + UF fica como modelo principal. O SVR empata em erro (a diferença é menor que a variação entre dobras) e não tem coeficientes, então não compensou perder a interpretação. Os dois seguem para o teste de 2025.

**Para a apresentação**
- `figuras/03_comparacao_modelos_cv.png`: o baseline vencendo a primeira Regressão Linear é a melhor história de "desafio e ajuste" do projeto.
- `figuras/03_ganho_por_bloco_features.png`: quanto cada grupo de variáveis acrescenta. O gasto, entrando por último, não acrescenta nada.
- `figuras/03_residuos_regressao_linear.png`: diagnóstico dos resíduos.

### Fase 18 – Teste em 2025, interpretação e recomendações (22/10/2026)

**O que fizemos:** no notebook `04_avaliacao_e_recomendacoes.ipynb` ajustamos os modelos escolhidos com todos os municípios de 2023 e os avaliamos **uma única vez** em 2025. Interpretamos a Regressão Linear (coeficientes com IC 95% robusto e conversão para unidades do gestor) e os dois modelos por permutation importance e dependência parcial do gasto. Montamos a regra de priorização (observado contra esperado em duas edições), testamos se a lista muda com o SVR e fizemos o estudo de caso de Goiás. Para identificar os municípios, juntamos nomes e microrregiões oficiais da API de localidades do IBGE (`dados/brutos/municipios_ibge.csv`, 5.571 municípios, todos casando com a base).

**Resultado do teste 2025**

| Modelo | RMSE | R² | Viés | RMSE sem o viés | Spearman previsto × real |
|---|---|---|---|---|---|
| Baseline: média da UF | 0,800 | 0,190 | −0,40 | 0,696 | 0,64 |
| Regressão Linear + UF | 0,745 | 0,298 | −0,35 | 0,658 | 0,70 |
| SVR ajustado | 0,711 | 0,361 | −0,34 | 0,627 | 0,74 |

**Desafios e ajustes**

| Problema | Diagnóstico | Ajuste |
|---|---|---|
| Erro maior em 2025 | A maior parte é viés: o IDEB real ficou 0,35 ponto acima do previsto, porque o país melhorou entre as edições. Descontado esse deslocamento, a Regressão Linear erra 0,658, perto dos 0,642 da validação cruzada. | Reportamos o RMSE sem o viés e a correlação de ordem. Para priorizar, usamos a posição relativa: somamos a alta média ao esperado de 2025. |
| SVR melhor no teste | O SVR errou 4,6% menos que a Regressão Linear em 2025, embora tivessem empatado na validação cruzada. | Mantivemos a escolha feita antes do teste, para não usar o teste como seleção. Verificamos o impacto na decisão: as classificações concordam em 88,9% dos municípios, e nenhum passa de "abaixo" para "acima". |
| Listas de prioridade diferentes | Dos 534 municípios abaixo do esperado pela Regressão Linear, só 300 (56%) também ficam abaixo pelo SVR. | A recomendação passou a usar como lista principal os 300 municípios em que os dois modelos concordam. |
| Instabilidade de redes pequenas | Confirmada de forma moderada: erro médio de 0,53 nas 20% menores redes, contra 0,46 nas maiores, e 12,9% contra 9,4% de erros acima de 1 ponto. | A regra de priorização exige duas edições abaixo do esperado. |

**Interpretação**
- INSE: +5 pontos acompanham +0,31 ponto de IDEB. % de docentes com superior: +10 p.p. acompanham +0,05. Biblioteca, internet para alunos, laboratório de informática, quadra e tempo integral têm associação positiva e pequena. Esforço docente (−0,12 por nível) e complexidade de gestão (−0,08 por nível) têm associação negativa. 12 das 24 features têm IC 95% que não cruza o zero.
- Gasto: dobrar o gasto por aluno acompanha +0,06 ponto (IC 95% de 0,01 a 0,11). Na dependência parcial, ir do percentil 5 (R$ 8,6 mil) ao 95 (R$ 26 mil) muda o IDEB previsto em 0,09 (Regressão Linear) e 0,12 (SVR).
- UF: entre municípios de mesmo perfil, o Ceará fica 1,50 ponto acima da UF mediana e Alagoas, 0,84. Amapá fica 1,09 abaixo. Na permutation importance a UF é a feature mais importante nos dois modelos (+0,20 de RMSE ao embaralhar), seguida do INSE (+0,07).
- Persistência: o desvio em relação ao esperado tem correlação de 0,66 entre 2023 e 2025. Ou seja, não é ruído, é algo do município que a base não mede.

**Goiás:** 237 municípios com as duas edições. 30 ficam abaixo do esperado nas duas (19 com concordância do SVR) e 28 ficam acima. Sete dos 30 estão no Entorno de Brasília e três na microrregião de Goiânia, a maioria periferias metropolitanas. Os municípios abaixo do esperado não gastam menos (mediana de R$ 22,8 mil por aluno, contra R$ 23,8 mil nos que ficam acima) e têm o mesmo INSE. Goiânia está dentro do esperado. Rio Verde e Goianésia ficam mais de 1 ponto acima do esperado nas duas edições, gastando abaixo da mediana do estado.

**Para a apresentação**
- `figuras/04_previsto_vs_real_2025.png`: o deslocamento de +0,35 e por que ele não invalida o modelo para priorizar.
- `figuras/04_coeficientes_regressao_linear.png`: os fatores associados, com intervalo de confiança.
- `figuras/04_efeito_parcial_gasto.png`: o efeito parcial do gasto é pequeno. Slide-chave para "associação não é causalidade" e "qualidade antes de quantidade".
- `figuras/04_importancia_permutacao.png`: a UF domina nos dois modelos.
- `figuras/04_erro_por_tamanho_rede.png`: por que exigir duas edições.
- `figuras/04_goias_real_vs_esperado.png`: o estudo de caso, com os municípios abaixo e acima do esperado.

### Fase 19 – Validação de ponta a ponta (22/10/2026)

**O que fizemos:** apagamos todas as figuras e os dados processados, remontamos os quatro notebooks e os executamos do zero, em ordem. Depois rodamos `notebooks/checagens_finais.py`, que confere automaticamente execução, vazamento, uso do teste, base de modelagem, figuras do diário e versões dos pacotes.

**Por quê:** o trabalho será avaliado por pares. Precisávamos garantir que qualquer pessoa, com o repositório e o `requirements.txt`, chegue aos mesmos números.

**Ajustes feitos durante a revisão**
- No notebook 03, a matriz `X` recebia a tabela inteira, incluindo a coluna do IDEB. O `ColumnTransformer` já descartava as colunas não usadas, então não havia vazamento, mas um leitor poderia suspeitar. Passamos a selecionar só as features e incluímos `assert ALVO not in X.columns`.
- Um texto do notebook 03 dizia que o erro era parecido entre as regiões. A tabela mostrava o contrário (MAE de 0,58 no Nordeste e de 0,40 no Sudeste), e corrigimos o texto.
- Três gráficos foram refeitos: rótulos sobrepostos em `04_previsto_vs_real_2025.png`, eixos com espaço sobrando em `04_goias_real_vs_esperado.png` e escala vertical que exagerava a inclinação em `04_efeito_parcial_gasto.png` (agora com janela fixa de 0,6 ponto).
- As tabelas de Goiás passaram a usar o padrão brasileiro de números e a indicar se o SVR concorda com a classificação.
- Correção de um número da Fase 13: somando as duas safras, são 56 linhas de CE e AL com IDEB ≥ 9 (71 com IDEB ≥ 8,5), e não "cerca de 80". A conclusão (concentração nesses dois estados) não muda.
- Os gráficos por UF e de coeficientes foram alargados (11 × 7 e 12 × 7,2 polegadas), porque no formato alto o texto ficava pequeno demais no slide.

**Resultado**
- Os quatro notebooks rodaram do zero sem erro, em cerca de 12 minutos no total (01: 22 s; 02: 11 s; 03: 7 min, quase todo na busca em grade aninhada do SVR; 04: 4,4 min).
- **23 de 23 checagens OK**, em cinco blocos: execução dos notebooks (4), vazamento de dados (8, incluindo testes de unidade do winsorizador e do baseline), base de modelagem (3), figuras e números do diário (7) e versões do ambiente (1).
- A reexecução reproduziu exatamente os números da primeira rodada (KFold e SVR com semente fixa).
- Uma checagem falhou na primeira tentativa por erro no próprio script de checagem (o teste do baseline usava uma coluna com outro nome). Corrigimos o teste, não o código do projeto.

**Para a apresentação:** reprodutibilidade é parte da qualidade. Os números do diário, dos notebooks e da apresentação são os mesmos e foram regenerados do zero.

### Fase 20 – Entregáveis de apresentação (22/10/2026)

**O que fizemos**
- `docs/guia_apresentacao.md`: roteiro de fala da dupla nos 7 itens do enunciado, com divisão de fala, números-chave, 13 perguntas prováveis com respostas e checklist.
- `docs/prints/`: prints das células dos notebooks executados que comprovam cada resultado (vazamento, gastos implausíveis, features finais, comparação de modelos, VIF, busca em grade, teste 2025, coeficientes, priorização, robustez e Goiás). Cada print traz o nome do notebook e o número da célula.
- `docs/apresentacao/index.html`: 23 cards de slide, na ordem problema → dados → recorte → desafios → proposta → métodos → resultados → recomendações → limitações. Navegação pelas setas do teclado. `docs/apresentacao/apresentacao.pdf` é a cópia para o caso de a sala estar sem internet.

**Decisão de formato:** escolhemos uma apresentação em HTML, com um card por ideia e os gráficos de `figuras/`, porque abre em qualquer navegador e usa diretamente as figuras geradas pelos notebooks. O PDF cobre o risco de falta de rede.

---

## Destaques para a apresentação (atualizar ao longo do projeto)

- Recorte guiado pelo negócio: quem financia cada etapa definiu o filtro.
- Dados reais e oficiais, integrados sem custo.
- Vazamento identificado e evitado antes da modelagem.
- Validação da primeira extração revelou indicadores incoerentes e um erro no denominador do gasto por aluno, corrigidos antes de modelar.
- Indicadores de 2023 e 2024 corrompidos na fonte intermediária, detectados por comparação com anos anteriores. Usamos 2022 como referência estrutural.
- Limitações declaradas: INSE de 2015, defasagem de indicadores e PIB, dados autodeclarados do Siconfi, municípios sem nota excluídos.
- Associação não é causalidade: o modelo serve para priorizar e investigar, não para decidir sozinho onde investir.
- Confusão medida com os nossos dados: dobrar o gasto por aluno acompanha +0,41 ponto sem controles, +0,20 com INSE e PIB, +0,11 dentro da UF e +0,06 no modelo completo (`figuras/01_gasto_vs_ideb_por_inse.png`, `figuras/04_efeito_parcial_gasto.png`).
- O baseline venceu a primeira Regressão Linear. Trocar região por UF resolveu (RMSE de 0,733 para 0,642) e mostrou que o efeito do estado (Ceará +1,50) não aparece em nenhuma variável municipal (`figuras/03_comparacao_modelos_cv.png`).
- O teste em 2025 errou mais por causa de um viés de +0,35 (o país melhorou). Descontado o viés, o erro fica perto da validação cruzada, e a ordem dos municípios se mantém (`figuras/04_previsto_vs_real_2025.png`).
- O SVR foi melhor no teste, mas mantivemos a escolha feita antes dele e medimos o impacto: as classificações concordam em 88,9%, e a lista principal usa os 300 municípios de consenso.
- Goiás: 30 municípios abaixo do esperado nas duas edições, 7 no Entorno de Brasília, e eles não gastam menos que os que ficam acima (`figuras/04_goias_real_vs_esperado.png`).
- Validação de ponta a ponta: os quatro notebooks rodam do zero, e um script de checagens confere vazamento, uso do teste, figuras e versões.
