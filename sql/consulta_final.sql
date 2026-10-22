-- =====================================================================
-- Problema 4 - Política e Gestão Pública
-- Base: IDEB anos iniciais (5º ano), rede municipal, 1 linha por município/ano
-- Anos-alvo: 2023 (treino) e 2025 (validação fora do tempo)
-- Fonte: Base dos Dados (BigQuery) - projeto ml-ideb-municipios
-- =====================================================================
WITH anos AS (
  -- ano do IDEB -> ano usado em cada fonte (mais recente disponível <= ano do IDEB)
  -- indicadores educacionais: 2022 para os dois anos (2023 e 2024 estão corrompidos na Base dos Dados)
  SELECT 2023 AS ano, 2022 AS ano_indic, 2023 AS ano_censo, 2023 AS ano_fin, 2023 AS ano_pop
  UNION ALL
  SELECT 2025, 2022, 2025, 2025, 2025
),

ideb AS (
  SELECT ano, id_municipio, sigla_uf, ideb, projecao AS meta_ideb
  FROM `basedosdados.br_inep_ideb.municipio`
  WHERE ano IN (2023, 2025)
    AND rede = 'municipal'
    AND ensino = 'fundamental'
    AND anos_escolares = 'iniciais (1-5)'
    AND ideb IS NOT NULL
),

indic AS (
  SELECT
    ano, id_municipio,
    atu_ef_anos_iniciais, had_ef_anos_iniciais, dsu_ef_anos_iniciais,
    afd_ef_anos_iniciais_grupo_1, afd_ef_anos_iniciais_grupo_2, afd_ef_anos_iniciais_grupo_3,
    afd_ef_anos_iniciais_grupo_4, afd_ef_anos_iniciais_grupo_5,
    ied_ef_anos_iniciais_nivel_1, ied_ef_anos_iniciais_nivel_2, ied_ef_anos_iniciais_nivel_3,
    ied_ef_anos_iniciais_nivel_4, ied_ef_anos_iniciais_nivel_5, ied_ef_anos_iniciais_nivel_6,
    ird_baixa_regularidade, ird_media_baixa, ird_media_alta, ird_alta,
    icg_nivel_1, icg_nivel_2, icg_nivel_3, icg_nivel_4, icg_nivel_5, icg_nivel_6
  FROM `basedosdados.br_inep_indicadores_educacionais.municipio`
  WHERE ano = 2022
    AND LOWER(rede) = 'municipal'
    AND LOWER(localizacao) = 'total'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY ano, id_municipio ORDER BY rede) = 1
),

censo AS (
  -- rede = '3' -> municipal (código INEP de dependência administrativa)
  SELECT
    ano, id_municipio,
    COUNT(*) AS n_escolas_ai,
    SUM(quantidade_matricula_fundamental_anos_iniciais) AS matriculas_ai,
    SUM(quantidade_docente_fundamental_anos_iniciais) AS docentes_ai,
    SAFE_DIVIDE(SUM(quantidade_matricula_fundamental_anos_iniciais_integral),
                SUM(quantidade_matricula_fundamental_anos_iniciais)) AS pct_matr_integral_ai,
    SAFE_DIVIDE(SUM(quantidade_matricula_zona_residencia_rural),
                SUM(quantidade_matricula_educacao_basica)) AS pct_matr_residencia_rural,
    SAFE_DIVIDE(SUM(quantidade_matricula_utiliza_transporte_publico),
                SUM(quantidade_matricula_educacao_basica)) AS pct_matr_transporte_publico,
    AVG(CAST(biblioteca_sala_leitura AS FLOAT64)) AS pct_esc_biblioteca,
    AVG(CAST(laboratorio_informatica AS FLOAT64)) AS pct_esc_lab_informatica,
    AVG(CAST(laboratorio_ciencias AS FLOAT64))    AS pct_esc_lab_ciencias,
    AVG(CAST(quadra_esportes AS FLOAT64))         AS pct_esc_quadra,
    AVG(CAST(internet_alunos AS FLOAT64))         AS pct_esc_internet_alunos,
    AVG(CAST(banda_larga AS FLOAT64))             AS pct_esc_banda_larga,
    AVG(CAST(esgoto_rede_publica AS FLOAT64))     AS pct_esc_esgoto_rede,
    AVG(CAST(agua_potavel AS FLOAT64))            AS pct_esc_agua_potavel,
    AVG(CAST(energia_rede_publica AS FLOAT64))    AS pct_esc_energia_rede
  FROM `basedosdados.br_inep_censo_escolar.escola`
  WHERE ano IN (2023, 2025)
    AND rede = '3'
    AND quantidade_matricula_fundamental_anos_iniciais > 0
  GROUP BY ano, id_municipio
),

censo_ef AS (
  -- denominador do gasto: todas as matrículas do EF na rede municipal
  -- (inclui escolas só de anos finais, que o filtro do CTE 'censo' exclui)
  SELECT ano, id_municipio, SUM(quantidade_matricula_fundamental) AS matriculas_ef
  FROM `basedosdados.br_inep_censo_escolar.escola`
  WHERE ano IN (2023, 2025) AND rede = '3'
  GROUP BY ano, id_municipio
),

fin AS (
  -- 3.12.361 = Ensino Fundamental | 3.12.000 = Educação (total da função)
  SELECT
    ano, id_municipio,
    SUM(IF(id_conta_bd = '3.12.361', valor, 0)) AS desp_ensino_fundamental,
    SUM(IF(id_conta_bd = '3.12.000', valor, 0)) AS desp_educacao_total,
    COUNTIF(id_conta_bd = '3.12.361') AS n_linhas_siconfi_ef
  FROM `basedosdados.br_me_siconfi.municipio_despesas_funcao`
  WHERE ano IN (2023, 2025)
    AND estagio_bd = 'Despesas Liquidadas'
    AND id_conta_bd IN ('3.12.361', '3.12.000')
  GROUP BY ano, id_municipio
),

pop AS (
  SELECT ano, id_municipio, populacao
  FROM `basedosdados.br_ibge_populacao.municipio`
  WHERE ano IN (2023, 2025)
),

pib AS (
  -- PIB municipal mais recente disponível = 2023 (usado também para as linhas de 2025)
  SELECT p.id_municipio, p.pib AS pib_2023, SAFE_DIVIDE(p.pib, po.populacao) AS pib_per_capita_2023
  FROM `basedosdados.br_ibge_pib.municipio` p
  LEFT JOIN `basedosdados.br_ibge_populacao.municipio` po
    ON po.id_municipio = p.id_municipio AND po.ano = 2023
  WHERE p.ano = 2023
),

inse AS (
  -- INSE só existe para 2014/2015 nesta base: usado como proxy socioeconômico estrutural
  SELECT id_municipio,
         SAFE_DIVIDE(SUM(valor_inse * inse_quantidade_alunos), SUM(inse_quantidade_alunos)) AS inse_medio_2015
  FROM `basedosdados.br_inep_indicadores_educacionais.escola_nivel_socioeconomico`
  WHERE ano = 2015 AND rede = 'municipal' AND valor_inse IS NOT NULL
  GROUP BY id_municipio
)

SELECT
  i.ano, i.id_municipio, i.sigla_uf,
  i.ideb, i.meta_ideb,
  ind.* EXCEPT (ano, id_municipio),
  c.* EXCEPT (ano, id_municipio),
  f.desp_ensino_fundamental, f.desp_educacao_total, f.n_linhas_siconfi_ef,
  ce.matriculas_ef,
  SAFE_DIVIDE(NULLIF(f.desp_ensino_fundamental, 0), ce.matriculas_ef) AS gasto_ef_por_aluno,
  SAFE_DIVIDE(c.matriculas_ai, c.docentes_ai) AS alunos_por_docente_ai,
  po.populacao,
  pb.pib_2023, pb.pib_per_capita_2023,
  s.inse_medio_2015
FROM ideb i
JOIN anos a ON a.ano = i.ano
LEFT JOIN indic ind ON ind.id_municipio = i.id_municipio AND ind.ano = a.ano_indic
LEFT JOIN censo c   ON c.id_municipio   = i.id_municipio AND c.ano   = a.ano_censo
LEFT JOIN censo_ef ce ON ce.id_municipio = i.id_municipio AND ce.ano = a.ano_censo
LEFT JOIN fin f     ON f.id_municipio   = i.id_municipio AND f.ano   = a.ano_fin
LEFT JOIN pop po    ON po.id_municipio  = i.id_municipio AND po.ano  = a.ano_pop
LEFT JOIN pib pb    ON pb.id_municipio  = i.id_municipio
LEFT JOIN inse s    ON s.id_municipio   = i.id_municipio
ORDER BY i.ano, i.id_municipio
