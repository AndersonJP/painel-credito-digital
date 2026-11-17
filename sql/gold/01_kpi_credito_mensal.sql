-- =============================================================================
-- GOLD | kpi_credito_mensal  -> alimenta o dashboard ESTRATÉGICO
-- Grão : 1 linha por mês x grupo de canal (Digital / Presencial)
-- Obs. : guardamos também SOMAS e CONTAGENS (soma_horas_decisao, qtd_decididas)
--        para que o Power BI / Tableau recalculem médias ponderadas corretamente
--        em qualquer filtro (média de médias é um erro clássico de BI).
-- =============================================================================
CREATE OR REPLACE TABLE gold.kpi_credito_mensal AS
SELECT
    mes_ref,
    canal_grupo,
    COUNT(*)                                                     AS qtd_propostas,
    SUM(CASE WHEN status <> 'PENDENTE' THEN 1 ELSE 0 END)        AS qtd_decididas,
    SUM(CASE WHEN status = 'APROVADA'  THEN 1 ELSE 0 END)        AS qtd_aprovadas,
    ROUND(100.0 * SUM(CASE WHEN status = 'APROVADA' THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN status <> 'PENDENTE' THEN 1 ELSE 0 END), 0), 1)
                                                                 AS taxa_aprovacao_pct,
    ROUND(SUM(horas_ate_decisao), 1)                             AS soma_horas_decisao,
    ROUND(AVG(horas_ate_decisao), 1)                             AS tempo_medio_decisao_h,
    ROUND(SUM(CASE WHEN status = 'APROVADA' THEN valor_solicitado ELSE 0 END), 2)
                                                                 AS valor_aprovado
FROM silver.propostas_credito
GROUP BY mes_ref, canal_grupo;
