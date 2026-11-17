-- Visão por região (propostas cruzadas com o cadastro de agências).
SELECT regiao, SUM(qtd_propostas) AS qtd_propostas,
       ROUND(SUM(valor_aprovado), 2) AS valor_aprovado
FROM gold.kpi_regiao
GROUP BY regiao
ORDER BY qtd_propostas DESC;
