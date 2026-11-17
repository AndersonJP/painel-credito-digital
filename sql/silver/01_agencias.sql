-- =============================================================================
-- SILVER | agencias
-- Origem : bronze.agencias  (CSV legado com ";" vindo do cadastro de agências)
-- O que faz:
--   * remove espaços e padroniza a UF em maiúsculo ("rs" -> "RS")
--   * garante código da agência com 4 dígitos (chave de junção com propostas)
--   * remove duplicidades mantendo 1 linha por agência
-- =============================================================================
CREATE OR REPLACE TABLE silver.agencias AS
SELECT
    LPAD(TRIM(cod_agencia), 4, '0') AS cod_agencia,
    TRIM(nome_agencia)              AS nome_agencia,
    TRIM(cidade)                    AS cidade,
    UPPER(TRIM(uf))                 AS uf,
    TRIM(regiao)                    AS regiao
FROM bronze.agencias
QUALIFY ROW_NUMBER() OVER (PARTITION BY LPAD(TRIM(cod_agencia), 4, '0') ORDER BY nome_agencia) = 1;
