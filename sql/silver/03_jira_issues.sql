-- =============================================================================
-- SILVER | jira_issues
-- Origem : bronze.jira_issues (export do Jira da squad Crédito Digital)
-- O que faz:
--   * unifica status em PT/EN ("Done" e "Concluído" -> "Concluído")
--   * traduz o tipo de item (Story -> História, Task -> Tarefa)
--   * extrai o número da sprint ("CRED Sprint 07" -> 7) para ordenar no tempo
--   * calcula o lead time (dias da criação até a conclusão)
--   * remove issues exportadas em duplicidade
-- =============================================================================
CREATE OR REPLACE TABLE silver.jira_issues AS
WITH base AS (
    SELECT
        TRIM(issue_key)                                          AS issue_key,
        CASE TRIM(issue_type) WHEN 'Story' THEN 'História'
                              WHEN 'Task'  THEN 'Tarefa'
                              ELSE TRIM(issue_type) END          AS tipo,
        CASE WHEN TRIM(status) IN ('Done', 'Concluído')            THEN 'Concluído'
             WHEN TRIM(status) IN ('In Progress', 'Em andamento')  THEN 'Em andamento'
             ELSE 'A fazer' END                                  AS status,
        TRIM(priority)                                           AS prioridade,
        CAST(created AS TIMESTAMP)                               AS criado_em,
        CAST(NULLIF(TRIM(resolved), '') AS TIMESTAMP)            AS resolvido_em,
        TRIM(sprint)                                             AS sprint,
        CAST(regexp_extract(sprint, '([0-9]+)$', 1) AS INT)      AS sprint_num,
        CAST(NULLIF(TRIM(story_points), '') AS INT)              AS story_points,
        TRIM(epic_link)                                          AS epico
    FROM bronze.jira_issues
)
SELECT
    *,
    CASE WHEN resolvido_em IS NOT NULL
         THEN ROUND((unix_timestamp(resolvido_em) - unix_timestamp(criado_em)) / 86400.0, 1)
    END AS lead_time_dias
FROM base
QUALIFY ROW_NUMBER() OVER (PARTITION BY issue_key ORDER BY criado_em) = 1;
