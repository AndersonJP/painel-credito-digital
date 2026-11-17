-- =============================================================================
-- GOLD | fluxo_jira_sprint  -> alimenta o dashboard OPERACIONAL (time / entrega)
-- Grão : 1 linha por sprint
-- Métricas de fluxo usadas por times ágeis: vazão (throughput), story points,
-- lead time médio e % de bugs (proxy de qualidade da entrega).
-- =============================================================================
CREATE OR REPLACE TABLE gold.fluxo_jira_sprint AS
SELECT
    sprint_num,
    sprint,
    COUNT(*)                                                       AS itens_planejados,
    SUM(CASE WHEN status = 'Concluído' THEN 1 ELSE 0 END)          AS itens_concluidos,
    SUM(CASE WHEN status = 'Concluído' THEN story_points ELSE 0 END) AS story_points_entregues,
    ROUND(AVG(lead_time_dias), 1)                                  AS lead_time_medio_dias,
    SUM(CASE WHEN tipo = 'Bug' THEN 1 ELSE 0 END)                  AS bugs,
    ROUND(100.0 * SUM(CASE WHEN tipo = 'Bug' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_bugs,
    MAX(resolvido_em)                                              AS ultima_entrega_em
FROM silver.jira_issues
GROUP BY sprint_num, sprint;
