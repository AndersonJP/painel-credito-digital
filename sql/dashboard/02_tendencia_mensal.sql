-- Linha do tempo: tempo médio de decisão e taxa de aprovação por mês e canal.
SELECT mes_ref, canal_grupo, qtd_propostas, taxa_aprovacao_pct, tempo_medio_decisao_h, valor_aprovado
FROM gold.kpi_credito_mensal
ORDER BY mes_ref, canal_grupo;
