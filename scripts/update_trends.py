"""
Atualiza data/trends.json com as consultas em alta ("rising related queries")
de "gta 6" no Google Trends (Brasil), usando a Google Trends API da SerpApi.

Variável de ambiente necessária:
  SERPAPI_KEY  -> sua chave gratuita da SerpApi (serpapi.com)

Uso local (opcional, pra testar na sua máquina):
  pip install requests
  SERPAPI_KEY=sua_chave python scripts/update_trends.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

import requests

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
QUERY = "gta 6"
GEO = "BR"
HL = "pt-BR"
OUTPUT_PATH = "data/trends.json"

# Termos que já sabemos que precisam de uma nota de contexto (edite/adicione à vontade)
NOTAS_CONHECIDAS = {
    "cyberlink gta 6": "Na real é 'CYBERLEEK' (hacker que vazou build do jogo) — não um produto chamado Cyberlink.",
    "gta 6 já lançou": "Confusão por causa dos vazamentos recentes — o jogo ainda não foi lançado.",
    "atriz da lucia gta 6": "Manni L. Perez é o nome mais especulado — NÃO confirmado pela Rockstar.",
    "gta 6 requisitos minimos": "Versão de PC nem foi anunciada — qualquer 'requisito' é especulação.",
    "que dia lança gta 6": "Resposta: 19/11/2026.",
    "gta 6 vai sair para pc": "Ainda não anunciado pela Rockstar.",
}


def parse_change(value, extracted_value):
    """Converte o campo 'value' da SerpApi (ex: '+150%' ou 'Breakout') em (mudanca:int, pico:bool)."""
    if isinstance(value, str) and value.strip().lower() in ("breakout", "record"):
        # 'Breakout' = crescimento tão grande que o Google não dá um número exato.
        return (extracted_value or 5000), True
    if isinstance(extracted_value, (int, float)):
        return int(extracted_value), False
    if isinstance(value, str):
        digits = re.sub(r"[^\d]", "", value)
        if digits:
            return int(digits), False
    return 0, False


def fetch_rising_queries():
    if not SERPAPI_KEY:
        print("ERRO: variável de ambiente SERPAPI_KEY não encontrada.", file=sys.stderr)
        sys.exit(1)

    params = {
        "engine": "google_trends",
        "q": QUERY,
        "geo": GEO,
        "hl": HL,
        "data_type": "RELATED_QUERIES",
        "api_key": SERPAPI_KEY,
    }
    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rising = data.get("related_queries", {}).get("rising", [])
    if not rising:
        print("Aviso: nenhuma 'rising query' retornada pela SerpApi neste momento.", file=sys.stderr)

    items = []
    for i, r in enumerate(rising[:10], start=1):
        consulta = r.get("query", "").strip()
        mudanca, pico = parse_change(r.get("value"), r.get("extracted_value"))
        items.append({
            "rank": i,
            "consulta": consulta,
            "mudanca": mudanca,
            "pico": pico,
            "nota": NOTAS_CONHECIDAS.get(consulta.lower(), ""),
        })
    return items


def main():
    items = fetch_rising_queries()

    # Horário de Brasília (UTC-3), sem depender de biblioteca externa de timezone
    now_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    captured_at = now_brt.strftime("%Y-%m-%dT%H:%M:%S-03:00")
    captured_label = now_brt.strftime("%d/%m/%Y %H:%M") + " (horário de Brasília) — atualizado automaticamente via SerpApi"

    payload = {
        "capturedAt": captured_at,
        "capturedLabel": captured_label,
        "region": "Brasil",
        "query": QUERY,
        "window": "Consultas relacionadas em alta (Google Trends via SerpApi)",
        "items": items,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"OK: {len(items)} consultas salvas em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
