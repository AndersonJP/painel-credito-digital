# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · SILVER — Limpeza, padronização e integração
# MAGIC As regras ficam em arquivos **`.sql` versionados no Git** (pasta `/sql/silver`).
# MAGIC Este notebook só os executa em ordem. Vantagens:
# MAGIC - a regra de negócio está escrita **uma vez** e roda no Databricks **e** localmente;
# MAGIC - code review fica fácil (diff de SQL puro);
# MAGIC - qualquer analista entende sem saber PySpark.

# COMMAND ----------

import os, glob

dbutils.widgets.text("catalogo", "credito_digital")
spark.sql(f"USE CATALOG {dbutils.widgets.get('catalogo')}")

# Em uma Git Folder (Repos), o diretório atual é a pasta do notebook
PASTA_SQL = os.path.abspath("../sql/silver")

# COMMAND ----------

# Executa 01_agencias.sql, 02_propostas_credito.sql, 03_jira_issues.sql, 04_jira_versions.sql
for arquivo in sorted(glob.glob(f"{PASTA_SQL}/*.sql")):
    spark.sql(open(arquivo, encoding="utf-8").read())
    tabela = "silver." + os.path.basename(arquivo)[3:-4]
    print(f"{tabela:<28} {spark.table(tabela).count():>8,} linhas")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Depois da limpeza: só 3 status possíveis e o tempo de decisão já calculado
# MAGIC SELECT status, canal_grupo, COUNT(*) AS qtd, ROUND(AVG(horas_ate_decisao), 1) AS horas_media
# MAGIC FROM silver.propostas_credito
# MAGIC GROUP BY status, canal_grupo
# MAGIC ORDER BY canal_grupo, status

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Jira: status PT/EN unificados
# MAGIC SELECT status, tipo, COUNT(*) AS qtd FROM silver.jira_issues GROUP BY ALL ORDER BY ALL
