# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · GOLD — Indicadores prontos para o negócio
# MAGIC | Tabela | Para quê | Público |
# MAGIC |---|---|---|
# MAGIC | `gold.kpi_credito_mensal` | volume, aprovação, tempo de decisão por mês/canal | Diretoria (estratégico) |
# MAGIC | `gold.fluxo_jira_sprint` | entregas, lead time e bugs por sprint | Time / PO (operacional) |
# MAGIC | `gold.impacto_releases` | **antes × depois** de cada release do Jira | Negócio + Tecnologia |
# MAGIC | `gold.kpi_regiao` | visão geográfica | Rede de agências |
# MAGIC
# MAGIC Estas tabelas são a fonte única para **Power BI, Tableau, QuickSight e Databricks SQL Dashboards**.

# COMMAND ----------

import os, glob

dbutils.widgets.text("catalogo", "credito_digital")
spark.sql(f"USE CATALOG {dbutils.widgets.get('catalogo')}")

for arquivo in sorted(glob.glob(os.path.abspath("../sql/gold") + "/*.sql")):
    spark.sql(open(arquivo, encoding="utf-8").read())
    tabela = "gold." + os.path.basename(arquivo)[3:-4]
    print(f"{tabela:<26} {spark.table(tabela).count():>6,} linhas")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- A pergunta do case: a entrega do time mudou o negócio?
# MAGIC SELECT * FROM gold.impacto_releases ORDER BY data_release, canal_grupo

# COMMAND ----------

# Visualização direto no notebook: clique em "+" > Visualization > Line (mes_ref x tempo, série = canal)
display(spark.table("gold.kpi_credito_mensal").orderBy("mes_ref", "canal_grupo"))
