"""
gerar_dados.py
==============
Gera os dados FICTÍCIOS usados no case (nenhum dado real de banco ou de cliente).

Simula 4 fontes diferentes, em 3 formatos diferentes, como acontece num ambiente
corporativo real:

  1. data/raw/propostas_credito.csv  -> extração do sistema core de crédito (CSV ",")
  2. data/raw/agencias.csv           -> cadastro legado de agências (CSV ";")
  3. data/raw/jira_issues.csv        -> export de issues do Jira da squad Crédito Digital
  4. data/raw/jira_versions.json     -> releases (fixVersions) vindas da API REST do Jira

Os dados têm "sujeira" proposital (status escritos de jeitos diferentes, espaços,
duplicidades, valores nulos, Jira misturando PT e EN) para mostrar a etapa de
limpeza na camada Silver.

Também existe um efeito de negócio "escondido": a release v2.0 (novo motor de
crédito, 15/06/2026) reduz bastante o tempo de decisão nos canais digitais.
O pipeline precisa ENCONTRAR esse efeito cruzando Jira x dados de negócio.

Uso:  python scripts/gerar_dados.py
"""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)  # semente fixa: todo mundo que rodar terá exatamente os mesmos dados

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

INICIO = datetime(2026, 1, 1)
FIM = datetime(2026, 10, 31)

# ----------------------------------------------------------------------------
# Releases do Jira (fixVersions) — o "gatilho" das mudanças no negócio
# ----------------------------------------------------------------------------
VERSOES = [
    {"id": "10010", "name": "v1.4 - Onboarding Digital", "releaseDate": "2026-03-16", "released": True},
    {"id": "10011", "name": "v2.0 - Motor de Crédito", "releaseDate": "2026-06-15", "released": True},
    {"id": "10012", "name": "v2.1 - Antifraude", "releaseDate": "2026-09-14", "released": True},
    {"id": "10013", "name": "v2.2 - Renegociação", "releaseDate": "2026-12-07", "released": False},
]
REL_V20 = datetime(2026, 6, 15)
REL_V21 = datetime(2026, 9, 14)

# ----------------------------------------------------------------------------
# 1) Agências (CSV com ";" e UF às vezes minúscula — típico de sistema legado)
# ----------------------------------------------------------------------------
CIDADES = [
    ("Passo Fundo", "RS", "Sul"), ("Porto Alegre", "RS", "Sul"), ("Caxias do Sul", "RS", "Sul"),
    ("Chapecó", "SC", "Sul"), ("Florianópolis", "SC", "Sul"), ("Curitiba", "PR", "Sul"),
    ("Londrina", "PR", "Sul"), ("São Paulo", "SP", "Sudeste"), ("Campinas", "SP", "Sudeste"),
    ("Belo Horizonte", "MG", "Sudeste"), ("Rio de Janeiro", "RJ", "Sudeste"),
    ("Goiânia", "GO", "Centro-Oeste"), ("Cuiabá", "MT", "Centro-Oeste"),
    ("Salvador", "BA", "Nordeste"), ("Recife", "PE", "Nordeste"),
]
agencias = []
for i, (cidade, uf, regiao) in enumerate(CIDADES * 2, start=1):  # 30 agências
    agencias.append({
        "cod_agencia": f"{i:04d}",
        "nome_agencia": f"Agência {cidade} {'Centro' if i <= 15 else 'Bairro'}",
        "cidade": cidade,
        "uf": uf.lower() if random.random() < 0.2 else uf,  # sujeira: UF minúscula
        "regiao": regiao,
    })
with open(RAW / "agencias.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=agencias[0].keys(), delimiter=";")
    w.writeheader()
    w.writerows(agencias)

# ----------------------------------------------------------------------------
# 2) Propostas de crédito (sistema core)
# ----------------------------------------------------------------------------
CANAIS = ["App", "Internet Banking", "Agência", "Correspondente"]
PESO_CANAL = [0.45, 0.20, 0.25, 0.10]
PRODUTOS = {  # produto: (valor médio, desvio)
    "Crédito Pessoal": (8000, 4000),
    "Consignado": (15000, 6000),
    "Cartão de Crédito": (3000, 1500),
    "Financiamento de Veículo": (45000, 15000),
}
STATUS_VARIANTES = {  # mesmo status escrito de vários jeitos (sujeira)
    "APROVADA": ["APROVADA", "aprovada", " Aprovada "],
    "REPROVADA": ["REPROVADA", "reprovada", "Reprovada"],
    "PENDENTE": ["PENDENTE", "pendente"],
}


def tempo_decisao_horas(canal: str, dt: datetime) -> float:
    """Horas entre a solicitação e a decisão. A v2.0 acelera muito o digital."""
    digital = canal in ("App", "Internet Banking")
    if digital and dt >= REL_V21:
        base = 5
    elif digital and dt >= REL_V20:
        base = 7
    else:
        base = 30
    return max(0.3, random.lognormvariate(0, 0.45) * base)


def prob_aprovacao(canal: str, dt: datetime) -> float:
    digital = canal in ("App", "Internet Banking")
    if digital and dt >= REL_V20:
        return 0.63
    return 0.56


propostas = []
dias = (FIM - INICIO).days + 1
seq = 1
for d in range(dias):
    dia = INICIO + timedelta(days=d)
    # volume cresce ao longo do ano e cai no fim de semana
    volume = int(55 + d * 0.08) if dia.weekday() < 5 else 18
    if dia >= datetime(2026, 3, 16):  # onboarding digital (v1.4) traz mais clientes
        volume = int(volume * 1.12)
    for _ in range(volume):
        canal = random.choices(CANAIS, PESO_CANAL)[0]
        produto = random.choice(list(PRODUTOS))
        media, desvio = PRODUTOS[produto]
        ts = dia + timedelta(minutes=random.randint(7 * 60, 21 * 60))
        dt_decisao = ts + timedelta(hours=tempo_decisao_horas(canal, ts))
        if dt_decisao > FIM + timedelta(days=1):
            status = "PENDENTE"
        elif random.random() < 0.03:
            status = "PENDENTE"
        else:
            status = "APROVADA" if random.random() < prob_aprovacao(canal, ts) else "REPROVADA"
        valor = round(max(500, random.gauss(media, desvio)), 2)
        propostas.append({
            "id_proposta": f"PRP{seq:07d}",
            "dt_solicitacao": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "dt_decisao": "" if status == "PENDENTE" else dt_decisao.strftime("%Y-%m-%d %H:%M:%S"),
            "canal": canal,
            "produto": produto,
            "valor_solicitado": "" if random.random() < 0.01 else valor,  # sujeira: nulos
            "status": random.choice(STATUS_VARIANTES[status]),
            "cod_agencia": random.choice(agencias)["cod_agencia"],
        })
        seq += 1

# sujeira: ~1% de linhas duplicadas (reprocessamento da extração)
propostas += random.sample(propostas, k=len(propostas) // 100)
random.shuffle(propostas)

with open(RAW / "propostas_credito.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=propostas[0].keys())
    w.writeheader()
    w.writerows(propostas)

# ----------------------------------------------------------------------------
# 3) Issues do Jira (squad Crédito Digital) — sprints de 2 semanas
# ----------------------------------------------------------------------------
EPICOS = ["Onboarding Digital", "Motor de Crédito", "Antifraude", "Renegociação", "Sustentação"]
STATUS_DONE = ["Done", "Concluído"]  # sujeira: Jira com idiomas misturados
issues = []
key = 1
inicio_sprint = datetime(2026, 1, 5)
for n in range(1, 23):  # 22 sprints (jan -> nov/2026)
    ini = inicio_sprint + timedelta(days=14 * (n - 1))
    fim = ini + timedelta(days=13)
    # logo depois da v2.0 sobe o número de bugs (estabilização), depois normaliza
    pico_bug = 1 if ini <= REL_V20 + timedelta(days=28) and ini >= REL_V20 else 0
    qtd = random.randint(18, 26)
    for _ in range(qtd):
        tipo = random.choices(["Story", "Bug", "Task"], [0.6, 0.2 + 0.25 * pico_bug, 0.2])[0]
        criado = ini - timedelta(days=random.randint(0, 20), hours=random.randint(0, 23))
        terminou = fim <= datetime(2026, 11, 13)
        resolvido = (criado + timedelta(days=random.uniform(2, 16))) if terminou and random.random() < 0.9 else None
        if resolvido and resolvido > fim:
            resolvido = fim - timedelta(hours=random.randint(1, 30))
        if resolvido and resolvido < criado:
            resolvido = criado + timedelta(days=1)
        if tipo == "Bug":
            epico = "Sustentação"
        elif ini < datetime(2026, 3, 16):
            epico = "Onboarding Digital"
        elif ini < REL_V20:
            epico = "Motor de Crédito"
        elif ini < REL_V21:
            epico = "Antifraude"
        else:
            epico = "Renegociação"
        issues.append({
            "Issue key": f"CRED-{key}",
            "Issue Type": tipo,
            "Status": random.choice(STATUS_DONE) if resolvido else random.choice(["In Progress", "To Do", "Em andamento"]),
            "Priority": random.choices(["Highest", "High", "Medium", "Low"], [0.1, 0.3, 0.45, 0.15])[0],
            "Created": criado.strftime("%Y-%m-%d %H:%M"),
            "Resolved": resolvido.strftime("%Y-%m-%d %H:%M") if resolvido else "",
            "Sprint": f"CRED Sprint {n:02d}",
            "Story Points": random.choice([1, 2, 3, 5, 8]) if tipo == "Story" else "",
            "Epic Link": epico,
        })
        key += 1

issues += random.sample(issues, k=12)  # sujeira: issue exportada duas vezes
with open(RAW / "jira_issues.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=issues[0].keys())
    w.writeheader()
    w.writerows(issues)

# ----------------------------------------------------------------------------
# 4) Versões do Jira (formato da API REST: GET /rest/api/3/project/CRED/versions)
# ----------------------------------------------------------------------------
with open(RAW / "jira_versions.json", "w", encoding="utf-8") as f:
    json.dump(VERSOES, f, ensure_ascii=False, indent=2)

print(f"OK: {len(propostas):,} propostas | {len(issues)} issues | {len(agencias)} agências | {len(VERSOES)} versões")
