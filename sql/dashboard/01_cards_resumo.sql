-- Cards do topo do dashboard (números-resumo do período).
-- Média de tempo PONDERADA: soma das horas / qtd decididas (não média de médias).
SELECT
    SUM(qtd_propostas)                                         AS total_propostas,
    ROUND(SUM(valor_aprovado), 2)                              AS valor_aprovado,
    ROUND(100.0 * SUM(qtd_aprovadas) / SUM(qtd_decididas), 1)  AS taxa_aprovacao_pct,
    ROUND(SUM(soma_horas_decisao) / SUM(qtd_decididas), 1)     AS tempo_medio_decisao_h
FROM gold.kpi_credito_mensal;
