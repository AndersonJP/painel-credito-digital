"""
pipeline_local.py
=================
Executa o pipeline COMPLETO na sua máquina, sem precisar de Databricks.

Por que existe?
  - Para qualquer pessoa (recrutador, time técnico) clonar o repositório e
    ver tudo funcionando em 1 comando.
  - Usa DuckDB (banco analítico local) rodando OS MESMOS arquivos SQL da pasta
    /sql que os notebooks do Databricks executam. Ou seja: a regra de negócio
    está escrita UMA vez só, em SQL, e roda nos dois ambientes.

Fluxo (arquitetura medalhão):
  RAW (arquivos) -> BRONZE (cópia fiel + metadados) -> SILVER (limpo e integrado)
  -> GOLD (indicadores) -> QUALIDADE (checks) -> EXPORT (CSV + dashboard HTML)

Uso:
  python scripts/gerar_dados.py   # 1x, gera os dados fictícios
  python src/pipeline_local.py    # roda o pipeline e gera dashboard/index.html
"""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw"
GOLD_CSV = RAIZ / "data" / "gold"
SQL = RAIZ / "sql"
DASH = RAIZ / "dashboard"


def conectar() -> duckdb.DuckDBPyConnection:
    """Abre o 'lakehouse' local e cria os schemas das 3 camadas."""
    con = duckdb.connect(str(RAIZ / "data" / "lakehouse.duckdb"))
    for schema in ("bronze", "silver", "gold"):
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    # Compatibilidade de dialeto: no Databricks (Spark SQL) a função
    # unix_timestamp() é nativa. No DuckDB criamos um "apelido" para ela,
    # assim o MESMO arquivo .sql roda nos dois motores.
    con.execute("CREATE OR REPLACE MACRO unix_timestamp(ts) AS epoch(ts)")
    return con


# -----------------------------------------------------------------------------
# 1) BRONZE: ingestão "como veio", só com nomes de coluna padronizados
#    e colunas de auditoria (_ingestao_ts, _arquivo_origem).
# -----------------------------------------------------------------------------
def camada_bronze(con):
    fontes = {
        # tabela bronze       : (leitura do arquivo,                                   renomeação de colunas)
        "propostas_credito": (f"read_csv('{RAW}/propostas_credito.csv', all_varchar=true)", {}),
        "agencias": (f"read_csv('{RAW}/agencias.csv', delim=';', all_varchar=true)", {}),
        "jira_issues": (
            f"read_csv('{RAW}/jira_issues.csv', all_varchar=true)",
            {   # Jira exporta colunas com espaço -> padronizamos para snake_case
                "Issue key": "issue_key", "Issue Type": "issue_type", "Status": "status",
                "Priority": "priority", "Created": "created", "Resolved": "resolved",
                "Sprint": "sprint", "Story Points": "story_points", "Epic Link": "epic_link",
            },
        ),
        "jira_versions": (f"read_json_auto('{RAW}/jira_versions.json')", {}),
    }
    for tabela, (leitura, renomear) in fontes.items():
        colunas = con.execute(f"SELECT * FROM {leitura} LIMIT 0").fetchdf().columns
        select = ", ".join(f'"{c}" AS {renomear.get(c, c)}' for c in colunas)
        con.execute(f"""
            CREATE OR REPLACE TABLE bronze.{tabela} AS
            SELECT {select},
                   current_timestamp      AS _ingestao_ts,
                   '{leitura.split("'")[1]}' AS _arquivo_origem
            FROM {leitura}
        """)
        qtd = con.execute(f"SELECT COUNT(*) FROM bronze.{tabela}").fetchone()[0]
        print(f"  bronze.{tabela:<20} {qtd:>7,} linhas")


# -----------------------------------------------------------------------------
# 2) e 3) SILVER e GOLD: executa os .sql em ordem (01_, 02_, ...)
# -----------------------------------------------------------------------------
def executar_pasta_sql(con, pasta: str):
    for arquivo in sorted((SQL / pasta).glob("*.sql")):
        con.execute(arquivo.read_text(encoding="utf-8"))
        tabela = f"{pasta}.{arquivo.stem[3:]}"  # "02_propostas_credito" -> "propostas_credito"
        qtd = con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        print(f"  {tabela:<27} {qtd:>7,} linhas")


# -----------------------------------------------------------------------------
# 4) QUALIDADE: cada check deve retornar 0 violações
# -----------------------------------------------------------------------------
def checar_qualidade(con):
    texto = (SQL / "qualidade" / "checks.sql").read_text(encoding="utf-8")
    blocos = [b.strip() for b in texto.split(";") if "SELECT" in b]
    falhas = 0
    for bloco in blocos:
        nome = next(l for l in bloco.splitlines() if l.startswith("-- check:"))[10:]
        sql = "\n".join(l for l in bloco.splitlines() if not l.strip().startswith("--"))
        violacoes = con.execute(sql).fetchone()[0]
        status = "OK " if violacoes == 0 else "ERRO"
        falhas += violacoes > 0
        print(f"  [{status}] {nome} ({violacoes} violações)")
    if falhas:
        raise SystemExit("Qualidade reprovada: dashboard NÃO foi publicado.")


# -----------------------------------------------------------------------------
# 5) EXPORT: tabelas gold em CSV (para Power BI/Tableau/QuickSight locais)
#    e dados das consultas do dashboard embutidos no HTML.
# -----------------------------------------------------------------------------
def _json_padrao(valor):
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()[:10]
    if isinstance(valor, Decimal):
        return float(valor)
    raise TypeError(type(valor))


def exportar(con):
    GOLD_CSV.mkdir(parents=True, exist_ok=True)
    for (tabela,) in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='gold' ORDER BY 1"
    ).fetchall():
        con.execute(f"COPY gold.{tabela} TO '{GOLD_CSV / tabela}.csv' (HEADER, DELIMITER ',')")

    dados = {}
    for arquivo in sorted((SQL / "dashboard").glob("*.sql")):
        cursor = con.execute(arquivo.read_text(encoding="utf-8"))
        colunas = [c[0] for c in cursor.description]
        dados[arquivo.stem[3:]] = [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    dados["gerado_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")

    modelo = (DASH / "template.html").read_text(encoding="utf-8")
    html = modelo.replace("/*__DADOS__*/{}", json.dumps(dados, default=_json_padrao, ensure_ascii=False))
    (DASH / "index.html").write_text(html, encoding="utf-8")
    print(f"  data/gold/*.csv e dashboard/index.html gerados")


if __name__ == "__main__":
    con = conectar()
    print("1) BRONZE  - ingestão das 4 fontes");           camada_bronze(con)
    print("2) SILVER  - limpeza, padronização e integração"); executar_pasta_sql(con, "silver")
    print("3) GOLD    - indicadores de negócio");            executar_pasta_sql(con, "gold")
    print("4) QUALIDADE - checks de dados");                 checar_qualidade(con)
    print("5) EXPORT  - CSVs + dashboard");                  exportar(con)
    print("\nPronto! Abra dashboard/index.html no navegador.")
