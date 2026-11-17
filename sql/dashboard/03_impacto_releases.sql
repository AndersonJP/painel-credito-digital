-- Antes x depois de cada release do Jira (Digital = afetado, Presencial = controle).
SELECT versao, data_release, canal_grupo, tempo_antes_h, tempo_depois_h,
       variacao_tempo_pct, aprov_antes_pct, aprov_depois_pct, variacao_aprov_pp
FROM gold.impacto_releases
ORDER BY data_release, canal_grupo;
