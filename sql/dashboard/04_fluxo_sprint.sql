-- Visão operacional do time (Jira): entregas, lead time e bugs por sprint.
SELECT sprint_num, sprint, itens_concluidos, story_points_entregues, lead_time_medio_dias, bugs, pct_bugs
FROM gold.fluxo_jira_sprint
ORDER BY sprint_num;
