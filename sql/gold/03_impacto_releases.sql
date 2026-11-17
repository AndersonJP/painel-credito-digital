-- =============================================================================
-- GOLD | impacto_releases  -> a pergunta de negócio do case:
--        "As entregas do time (Jira) melhoraram os indicadores de crédito?"
-- Como : para cada release lançada, compara 60 dias ANTES x 60 dias DEPOIS
--        da data de release, separando Digital (afetado) x Presencial (controle).
--        O canal Presencial funciona como "grupo de controle": se só o Digital
--        melhorou, o efeito é da entrega, e não sazonalidade.
-- =============================================================================
CREATE OR REPLACE TABLE gold.impacto_releases AS
WITH janela AS (
    SELECT
        v.versao,
        v.data_release,
        p.canal_grupo,
        CASE WHEN p.dt_solicitacao < v.data_release THEN 'antes' ELSE 'depois' END AS periodo,
        p.horas_ate_decisao,
        p.status
    FROM silver.jira_versions v
    JOIN silver.propostas_credito p
      ON p.dt_solicitacao >= v.data_release - INTERVAL 60 DAYS
     AND p.dt_solicitacao <  v.data_release + INTERVAL 60 DAYS
    WHERE v.lancada
),
resumo AS (
    SELECT
        versao,
        data_release,
        canal_grupo,
        AVG(CASE WHEN periodo = 'antes'  THEN horas_ate_decisao END) AS tempo_antes_h,
        AVG(CASE WHEN periodo = 'depois' THEN horas_ate_decisao END) AS tempo_depois_h,
        100.0 * SUM(CASE WHEN periodo = 'antes'  AND status = 'APROVADA'  THEN 1 ELSE 0 END)
              / NULLIF(SUM(CASE WHEN periodo = 'antes'  AND status <> 'PENDENTE' THEN 1 ELSE 0 END), 0) AS aprov_antes_pct,
        100.0 * SUM(CASE WHEN periodo = 'depois' AND status = 'APROVADA'  THEN 1 ELSE 0 END)
              / NULLIF(SUM(CASE WHEN periodo = 'depois' AND status <> 'PENDENTE' THEN 1 ELSE 0 END), 0) AS aprov_depois_pct
    FROM janela
    GROUP BY versao, data_release, canal_grupo
)
SELECT
    versao,
    data_release,
    canal_grupo,
    ROUND(tempo_antes_h, 1)                                         AS tempo_antes_h,
    ROUND(tempo_depois_h, 1)                                        AS tempo_depois_h,
    ROUND(100.0 * (tempo_depois_h - tempo_antes_h) / tempo_antes_h, 1) AS variacao_tempo_pct,
    ROUND(aprov_antes_pct, 1)                                       AS aprov_antes_pct,
    ROUND(aprov_depois_pct, 1)                                      AS aprov_depois_pct,
    ROUND(aprov_depois_pct - aprov_antes_pct, 1)                    AS variacao_aprov_pp
FROM resumo;
