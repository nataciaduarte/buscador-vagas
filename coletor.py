import json
import os
import re
import sqlite3
import time

import requests
from dotenv import load_dotenv

# Lê o arquivo .env e coloca as chaves nas variáveis de ambiente
load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

# "br" = Brasil. O número no fim do endereço é a página de resultados
URL_BASE = "https://api.adzuna.com/v1/api/jobs/br/search/{pagina}"

# O que o coletor vai procurar. Por enquanto só uma busca,
# porque o plano de teste da Adzuna tem poucas chamadas.
BUSCAS = [
    {"termo": "estágio", "local": "Rio de Janeiro"},
]
PAGINAS_POR_BUSCA = 1      # cada página traz até 50 vagas
DIAS_PARA_MANTER = 30      # vagas mais antigas que isso são apagadas


def limpar_texto(texto):
    """Remove marcações HTML (como <strong>) que às vezes vêm nos títulos."""
    if not texto:
        return ""
    return re.sub(r"<[^>]+>", "", texto).strip()


def conectar_banco():
    """Abre (ou cria) o arquivo vagas.db e garante que a tabela existe."""
    conn = sqlite3.connect("vagas.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            id TEXT PRIMARY KEY,
            titulo TEXT,
            empresa TEXT,
            local TEXT,
            descricao TEXT,
            link TEXT,
            data_publicacao TEXT,
            categoria TEXT,
            salario_min REAL,
            salario_max REAL,
            termo_busca TEXT,
            coletada_em TEXT
        )
    """)
    return conn


def buscar_vagas(termo, local, pagina):
    """Pede uma página de vagas para a API da Adzuna e devolve a lista."""
    parametros = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": termo,
        "results_per_page": 50,
        "content-type": "application/json",
        "sort_by": "date",
    }
    if local:
        parametros["where"] = local

    resposta = requests.get(URL_BASE.format(pagina=pagina), params=parametros, timeout=30)
    resposta.raise_for_status()  # para o programa com erro claro se algo der errado
    return resposta.json().get("results", [])


def salvar_vagas(conn, vagas, termo):
    """Grava as vagas no banco. Vagas repetidas (mesmo id) são ignoradas."""
    novas = 0
    for v in vagas:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO vagas
                (id, titulo, empresa, local, descricao, link, data_publicacao,
                 categoria, salario_min, salario_max, termo_busca, coletada_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                str(v.get("id")),
                limpar_texto(v.get("title")),
                (v.get("company") or {}).get("display_name"),
                (v.get("location") or {}).get("display_name"),
                limpar_texto(v.get("description")),
                v.get("redirect_url"),
                v.get("created"),
                (v.get("category") or {}).get("label"),
                v.get("salary_min"),
                v.get("salary_max"),
                termo,
            ),
        )
        novas += cursor.rowcount  # 1 se gravou, 0 se já existia
    conn.commit()
    return novas


def exportar_json(conn):
    """Grava as vagas do banco em vagas.json, para outras ferramentas
    (como o n8n) lerem os dados sem precisar abrir o SQLite."""
    conn.row_factory = sqlite3.Row
    linhas = conn.execute(
        """
        SELECT id, titulo, empresa, local, link, data_publicacao, coletada_em,
               substr(descricao, 1, 500) AS descricao
        FROM vagas
        ORDER BY data_publicacao DESC
        """
    ).fetchall()
    conn.row_factory = None
    with open("vagas.json", "w", encoding="utf-8") as f:
        json.dump([dict(l) for l in linhas], f, ensure_ascii=False, indent=1)
    return len(linhas)


def main():
    if not APP_ID or not APP_KEY:
        raise SystemExit("Chaves da Adzuna não encontradas. Confira o arquivo .env")

    conn = conectar_banco()
    total_novas = 0

    for busca in BUSCAS:
        for pagina in range(1, PAGINAS_POR_BUSCA + 1):
            vagas = buscar_vagas(busca["termo"], busca["local"], pagina)
            novas = salvar_vagas(conn, vagas, busca["termo"])
            total_novas += novas
            local = busca["local"] or "Brasil"
            print(f"{busca['termo']} | {local} | página {pagina}: "
                  f"{len(vagas)} recebidas, {novas} novas")
            if not vagas:
                break      # acabaram os resultados desta busca
            time.sleep(1)  # pausa curta para não sobrecarregar a API

    # Apaga vagas antigas para o banco não crescer sem parar
    conn.execute(
        "DELETE FROM vagas WHERE data_publicacao < date('now', ?)",
        (f"-{DIAS_PARA_MANTER} days",),
    )
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM vagas").fetchone()[0]
    exportar_json(conn)
    conn.close()
    print(f"Pronto: {total_novas} vagas novas. Total no banco: {total}.")


if __name__ == "__main__":
    main()
