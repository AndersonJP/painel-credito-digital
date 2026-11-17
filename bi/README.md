# Camada de consumo: Power BI, Tableau e Amazon QuickSight

As 4 tabelas **gold** são a fonte única para qualquer ferramenta de BI.
Assim o número é o mesmo no Power BI, no Tableau, no QuickSight e no Databricks SQL.

| Tabela gold | Grão | Uso |
|---|---|---|
| `gold.kpi_credito_mensal` | mês × canal | dashboard estratégico |
| `gold.impacto_releases` | release × canal | antes × depois das entregas |
| `gold.fluxo_jira_sprint` | sprint | dashboard operacional do time |
| `gold.kpi_regiao` | região × UF | visão da rede de agências |

> Sem Databricks? Rode `python src/pipeline_local.py` e use os CSVs de `data/gold/`.

---

## 1. Power BI

**Conexão:** Obter dados → *Azure Databricks* (ou *Databricks*) → informe o *Server Hostname*
e o *HTTP Path* do SQL Warehouse → modo **DirectQuery** (dado sempre atualizado) ou
**Import** (mais performance) → selecione o catálogo `credito_digital`, schema `gold`.

**Modelo:** crie uma tabela `dCalendario` e relacione com `kpi_credito_mensal[mes_ref]`.

### Medidas DAX

```DAX
-- Volume
Propostas = SUM ( kpi_credito_mensal[qtd_propostas] )

-- Taxa de aprovação: SEMPRE razão das somas (nunca média das taxas mensais)
Taxa de Aprovação % =
DIVIDE (
    SUM ( kpi_credito_mensal[qtd_aprovadas] ),
    SUM ( kpi_credito_mensal[qtd_decididas] )
)

-- Tempo médio ponderado: por isso a gold guarda soma_horas_decisao
Tempo Médio de Decisão (h) =
DIVIDE (
    SUM ( kpi_credito_mensal[soma_horas_decisao] ),
    SUM ( kpi_credito_mensal[qtd_decididas] )
)

-- Comparação com o mês anterior
Tempo Médio Mês Anterior =
CALCULATE ( [Tempo Médio de Decisão (h)], DATEADD ( dCalendario[Data], -1, MONTH ) )

Variação Tempo vs Mês Anterior % =
DIVIDE ( [Tempo Médio de Decisão (h)] - [Tempo Médio Mês Anterior], [Tempo Médio Mês Anterior] )

-- Ganho do Digital sobre o Presencial (em horas)
Ganho Digital (h) =
CALCULATE ( [Tempo Médio de Decisão (h)], kpi_credito_mensal[canal_grupo] = "Presencial" )
    - CALCULATE ( [Tempo Médio de Decisão (h)], kpi_credito_mensal[canal_grupo] = "Digital" )

-- Qualidade da entrega (Jira)
% Bugs na Sprint =
DIVIDE ( SUM ( fluxo_jira_sprint[bugs] ), SUM ( fluxo_jira_sprint[itens_planejados] ) )
```

**Páginas sugeridas:** (1) Estratégico: cards + linha de tempo com as releases como *linhas
constantes*; (2) Impacto das releases: matriz antes × depois; (3) Operacional do time: Jira por sprint.

---

## 2. Tableau

**Conexão:** Conectar → *Databricks* → Server Hostname + HTTP Path + token.
Arraste `gold.kpi_credito_mensal`. Campos calculados equivalentes:

```
// Taxa de Aprovação
SUM([Qtd Aprovadas]) / SUM([Qtd Decididas])

// Tempo Médio Ponderado
SUM([Soma Horas Decisao]) / SUM([Qtd Decididas])
```
Para marcar as releases na linha do tempo: *Analytics → Reference Line* com as datas de `impacto_releases`.

---

## 3. Amazon QuickSight

**Conexão:** Datasets → New dataset → *Databricks* (conector nativo) → host, porta 443,
HTTP Path e token → escolha `gold.*`. Use **SPICE** para cache.

```
// Campos calculados
taxa_aprovacao = sum({qtd_aprovadas}) / sum({qtd_decididas})
tempo_medio_ponderado = sum({soma_horas_decisao}) / sum({qtd_decididas})
```

---

## 4. Databricks SQL Dashboard (nativo)

As consultas de `sql/dashboard/*.sql` são as mesmas do dashboard HTML. No Databricks:
**SQL Editor** → cole a consulta → salve → **Dashboards → Create** → adicione cada consulta como visualização.
Agende o refresh junto com o Job do pipeline.
