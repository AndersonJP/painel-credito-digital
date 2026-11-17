-- =============================================================================
-- SILVER | propostas_credito
-- Origem : bronze.propostas_credito (sistema core de crédito) + silver.agencias
-- O que faz:
--   * converte textos para os tipos corretos (timestamp, decimal)
--   * padroniza o status (" Aprovada ", "aprovada" -> "APROVADA")
--   * cria o grupo de canal: Digital (App/Internet Banking) x Presencial
--   * calcula as horas entre a solicitação e a decisão (indicador-chave)
--   * enriquece com cidade/UF/região da agência (integração de 2 fontes)
--   * remove propostas duplicadas (reprocessamento da extração)
-- =============================================================================
CREATE OR REPLACE TABLE silver.propostas_credito AS
WITH base AS (
    SELECT
        TRIM(id_proposta)                                         AS id_proposta,
        CAST(dt_solicitacao AS TIMESTAMP)                         AS dt_solicitacao,
        CAST(NULLIF(TRIM(dt_decisao), '') AS TIMESTAMP)           AS dt_decisao,
        TRIM(canal)                                               AS canal,
        CASE WHEN TRIM(canal) IN ('App', 'Internet Banking')
             THEN 'Digital' ELSE 'Presencial' END                 AS canal_grupo,
        TRIM(produto)                                             AS produto,
        CAST(NULLIF(TRIM(valor_solicitado), '') AS DECIMAL(18,2)) AS valor_solicitado,
        UPPER(TRIM(status))                                       AS status,
        LPAD(TRIM(cod_agencia), 4, '0')                           AS cod_agencia
    FROM bronze.propostas_credito
)
SELECT
    b.*,
    -- tempo de decisão em horas (NULL quando a proposta ainda está pendente)
    CASE WHEN b.dt_decisao IS NOT NULL
         THEN ROUND((unix_timestamp(b.dt_decisao) - unix_timestamp(b.dt_solicitacao)) / 3600.0, 2)
    END                                                AS horas_ate_decisao,
    CAST(date_trunc('MONTH', b.dt_solicitacao) AS DATE) AS mes_ref,
    a.cidade,
    a.uf,
    a.regiao
FROM base b
LEFT JOIN silver.agencias a
       ON a.cod_agencia = b.cod_agencia
-- deduplicação: 1 linha por proposta
QUALIFY ROW_NUMBER() OVER (PARTITION BY b.id_proposta ORDER BY b.dt_solicitacao) = 1;
