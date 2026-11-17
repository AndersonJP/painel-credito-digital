-- =============================================================================
-- SILVER | jira_versions
-- Origem : bronze.jira_versions (JSON da API REST do Jira: /project/CRED/versions)
-- O que faz: tipa a data de release. É esta tabela que "liga" as entregas do
--            time aos indicadores de negócio (ver gold.impacto_releases).
-- =============================================================================
CREATE OR REPLACE TABLE silver.jira_versions AS
SELECT
    CAST(id AS INT)           AS id_versao,
    TRIM(name)                AS versao,
    CAST(releaseDate AS DATE) AS data_release,
    CAST(released AS BOOLEAN) AS lancada
FROM bronze.jira_versions;
