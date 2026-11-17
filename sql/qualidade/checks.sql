-- =============================================================================
-- QUALIDADE DE DADOS (data quality checks)
-- Cada consulta retorna a quantidade de VIOLAÇÕES. Esperado: 0 em todas.
-- O pipeline (local e Databricks) lê este arquivo, separa as consultas e executa
-- cada checagem. Se alguma falhar, o processo para antes de publicar o dashboard.
-- =============================================================================

-- check: propostas sem duplicidade
SELECT COUNT(*) - COUNT(DISTINCT id_proposta) AS violacoes FROM silver.propostas_credito;

-- check: status dentro do domínio esperado
SELECT COUNT(*) AS violacoes FROM silver.propostas_credito
WHERE status NOT IN ('APROVADA', 'REPROVADA', 'PENDENTE');

-- check: tempo de decisão nunca negativo
SELECT COUNT(*) AS violacoes FROM silver.propostas_credito WHERE horas_ate_decisao < 0;

-- check: toda proposta encontrou a agência (integridade entre fontes)
SELECT COUNT(*) AS violacoes FROM silver.propostas_credito WHERE regiao IS NULL;

-- check: issues do Jira sem duplicidade
SELECT COUNT(*) - COUNT(DISTINCT issue_key) AS violacoes FROM silver.jira_issues;

-- check: issue concluída precisa ter data de resolução
SELECT COUNT(*) AS violacoes FROM silver.jira_issues
WHERE status = 'Concluído' AND resolvido_em IS NULL;
