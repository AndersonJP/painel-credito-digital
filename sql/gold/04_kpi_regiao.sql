-- =============================================================================
-- GOLD | kpi_regiao  -> visão geográfica (propostas x agências)
-- Grão : 1 linha por região x UF
-- =============================================================================
CREATE OR REPLACE TABLE gold.kpi_regiao AS
SELECT
    regiao,
    uf,
    COUNT(*)                                                     AS qtd_propostas,
    ROUND(100.0 * SUM(CASE WHEN status = 'APROVADA' THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN status <> 'PENDENTE' THEN 1 ELSE 0 END), 0), 1)
                                                                 AS taxa_aprovacao_pct,
    ROUND(AVG(horas_ate_decisao), 1)                             AS tempo_medio_decisao_h,
    ROUND(SUM(CASE WHEN status = 'APROVADA' THEN valor_solicitado ELSE 0 END), 2)
                                                                 AS valor_aprovado
FROM silver.propostas_credito
GROUP BY regiao, uf;
