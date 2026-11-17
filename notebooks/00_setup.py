# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Setup do ambiente
# MAGIC **Projeto:** Painel Crédito Digital — Jira × Indicadores de Negócio
# MAGIC
# MAGIC Cria o catálogo, os schemas da arquitetura medalhão (**bronze → silver → gold**)
# MAGIC e o *Volume* onde os arquivos brutos são colocados.
# MAGIC
# MAGIC > Rode os notebooks na ordem: `00` → `01` → `02` → `03` → `04`.
# MAGIC > (Ou agende como um **Databricks Job** com 4 tarefas em sequência.)

# COMMAND ----------

# Widgets = parâmetros do notebook (aparecem no topo da tela e podem ser passados pelo Job)
dbutils.widgets.text("catalogo", "credito_digital", "Catálogo (Unity Catalog)")
catalogo = dbutils.widgets.get("catalogo")

# COMMAND ----------

# Cria catálogo + schemas das 3 camadas + volume para os arquivos brutos
spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalogo}")
spark.sql(f"USE CATALOG {catalogo}")
for schema in ["raw", "bronze", "silver", "gold"]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
spark.sql("CREATE VOLUME IF NOT EXISTS raw.arquivos")

print(f"Ambiente pronto. Faça upload dos arquivos de data/raw/ para: /Volumes/{catalogo}/raw/arquivos/")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Origem dos arquivos (em produção)
# MAGIC | Arquivo | Fonte real | Como chegaria |
# MAGIC |---|---|---|
# MAGIC | `propostas_credito.csv` | Sistema core de crédito | Extração diária (Auto Loader / Lakeflow Connect) |
# MAGIC | `agencias.csv` | Cadastro legado (CSV `;`) | Carga semanal |
# MAGIC | `jira_issues.csv` | Jira — squad Crédito Digital | API REST do Jira / conector |
# MAGIC | `jira_versions.json` | Jira — releases (fixVersions) | `GET /rest/api/3/project/CRED/versions` |
