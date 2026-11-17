# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Qualidade de dados + Insights
# MAGIC 1. Roda os **checks de qualidade** (`/sql/qualidade/checks.sql`). Se algum falhar, o Job para
# MAGIC    e o dashboard **não** é atualizado com dado errado.
# MAGIC 2. Explora os resultados e registra os **insights acionáveis**.

# COMMAND ----------

import os

dbutils.widgets.text("catalogo", "credito_digital")
spark.sql(f"USE CATALOG {dbutils.widgets.get('catalogo')}")

texto = open(os.path.abspath("../sql/qualidade/checks.sql"), encoding="utf-8").read()
falhas = []
for bloco in [b.strip() for b in texto.split(";") if "SELECT" in b]:
    nome = next(l for l in bloco.splitlines() if l.startswith("-- check:"))[10:]
    sql = "\n".join(l for l in bloco.splitlines() if not l.strip().startswith("--"))
    violacoes = spark.sql(sql).collect()[0][0]
    print(f"[{'OK ' if violacoes == 0 else 'ERRO'}] {nome}: {violacoes}")
    if violacoes:
        falhas.append(nome)

assert not falhas, f"Qualidade reprovada: {falhas}"

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Insight 1: depois da v2.0, o tempo de decisão do Digital caiu de ~33h para ~8h.
# MAGIC -- O Presencial (que não recebeu o motor novo) ficou igual => o efeito é da entrega.
# MAGIC SELECT versao, canal_grupo, tempo_antes_h, tempo_depois_h, variacao_tempo_pct, variacao_aprov_pp
# MAGIC FROM gold.impacto_releases
# MAGIC WHERE versao LIKE 'v2.0%'

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Insight 2: o Presencial ainda leva ~34h. Quantas propostas por mês seriam beneficiadas
# MAGIC -- se o motor v2 fosse levado para a rede de agências?
# MAGIC SELECT mes_ref, qtd_propostas, tempo_medio_decisao_h
# MAGIC FROM gold.kpi_credito_mensal
# MAGIC WHERE canal_grupo = 'Presencial' AND mes_ref >= '2026-07-01'
# MAGIC ORDER BY mes_ref

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Insight 3: as sprints em torno da v2.0 (9 a 14) tiveram ~29% de bugs, contra ~19% nas demais.
# MAGIC -- Sugestão: reservar capacidade de sustentação antes e depois de releases grandes.
# MAGIC SELECT CASE WHEN sprint_num BETWEEN 9 AND 14 THEN 'Em torno da v2.0' ELSE 'Demais sprints' END AS periodo,
# MAGIC        ROUND(100.0 * SUM(bugs) / SUM(itens_planejados), 1) AS pct_bugs
# MAGIC FROM gold.fluxo_jira_sprint
# MAGIC GROUP BY 1
