# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · BRONZE — Ingestão das fontes
# MAGIC Regra da camada Bronze: **guardar o dado como veio**, sem regra de negócio.
# MAGIC Só fazemos 2 coisas:
# MAGIC 1. padronizar nomes de colunas (o Delta não aceita espaço: `Issue key` → `issue_key`);
# MAGIC 2. adicionar colunas de auditoria: `_ingestao_ts` e `_arquivo_origem` (rastreabilidade).

# COMMAND ----------

from pyspark.sql import functions as F

dbutils.widgets.text("catalogo", "credito_digital")
catalogo = dbutils.widgets.get("catalogo")
spark.sql(f"USE CATALOG {catalogo}")
VOLUME = f"/Volumes/{catalogo}/raw/arquivos"

# COMMAND ----------

def salvar_bronze(df, tabela: str):
    """Padroniza colunas, adiciona auditoria e grava como tabela Delta na bronze."""
    for col in df.columns:
        df = df.withColumnRenamed(col, col.strip().lower().replace(" ", "_"))
    df = (df.withColumn("_ingestao_ts", F.current_timestamp())
            .withColumn("_arquivo_origem", F.col("_metadata.file_path")))
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"bronze.{tabela}")
    print(f"bronze.{tabela}: {spark.table(f'bronze.{tabela}').count():,} linhas")

# COMMAND ----------

# Fonte 1 — Sistema core de crédito (CSV ",").
# Sem inferSchema de propósito: na bronze tudo entra como texto; tipagem é na silver.
salvar_bronze(spark.read.option("header", True).csv(f"{VOLUME}/propostas_credito.csv"),
              "propostas_credito")

# Fonte 2 — Cadastro legado de agências (CSV com ";")
salvar_bronze(spark.read.option("header", True).option("sep", ";").csv(f"{VOLUME}/agencias.csv"),
              "agencias")

# Fonte 3 — Export de issues do Jira
salvar_bronze(spark.read.option("header", True).csv(f"{VOLUME}/jira_issues.csv"),
              "jira_issues")

# Fonte 4 — Releases do Jira (JSON da API, um array em várias linhas => multiLine)
salvar_bronze(spark.read.option("multiLine", True).json(f"{VOLUME}/jira_versions.json"),
              "jira_versions")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Conferência rápida: o dado "sujo" chegou como veio (status com variações)
# MAGIC SELECT status, COUNT(*) AS qtd
# MAGIC FROM bronze.propostas_credito
# MAGIC GROUP BY status
# MAGIC ORDER BY qtd DESC
