"""
analise_precos.py — Ferramenta OPCIONAL da skill pesquisa-precos-publicos.

=====================================================================
ATENÇÃO: este script NÃO é executado no fluxo padrão da skill.
=====================================================================

O agente de pesquisa de preços entrega, por padrão, a tabela bruta de
registros (OBJETO + VALOR + LINK + DATA DE ACESSO). A análise estatística
— média, mediana, coeficiente de variação, detecção de outliers — cabe
ao pregoeiro/agente de contratação, conforme Art. 23, § 2º da Lei
14.133/2021.

Este script só é executado quando o usuário PEDE EXPLICITAMENTE:
  - "calcula a mediana desses preços"
  - "qual o CV da cesta?"
  - "tem outlier aí?"
  - "roda a análise estatística"

Entrada esperada: lista de dicionários com pelo menos a chave 'valor'
(float) e, opcionalmente, 'fonte' (str) para rastreamento.

Saída: dicionário com estatísticas descritivas + outliers detectados
via IQR (método útil, mas não substitui análise qualitativa).

Uso via CLI:
    python analise_precos.py '[{"valor": 11.87, "fonte": "PNCP"}, ...]'
"""
import pandas as pd
import numpy as np
import sys
import json


def analisar_precos(dados_precos):
    """
    Análise descritiva de uma cesta de preços.

    Args:
        dados_precos: lista de dicts. Cada dict deve ter 'valor' (float).
                      Campo 'fonte' é opcional, usado para rastreabilidade.

    Returns:
        dict com estatísticas e outliers. Se len < 4, não calcula IQR.
    """
    if not dados_precos:
        return {"error": "Nenhum dado fornecido"}

    df = pd.DataFrame(dados_precos)

    if 'valor' not in df.columns:
        return {"error": "Campo 'valor' ausente nos registros"}

    # Estatísticas descritivas básicas
    stats = {
        "contagem": int(len(df)),
        "minimo": float(df['valor'].min()),
        "maximo": float(df['valor'].max()),
        "media": float(df['valor'].mean()),
        "mediana": float(df['valor'].median()),
        "desvio_padrao": float(df['valor'].std()) if len(df) > 1 else 0.0,
    }

    # Coeficiente de Variação — indicador de homogeneidade da cesta.
    # CV > 25% é o gatilho clássico (TCU Ac. 403/2021-Pl) para preferir mediana.
    stats["cv_percentual"] = (
        (stats["desvio_padrao"] / stats["media"]) * 100
        if stats["media"] > 0 else 0.0
    )
    stats["cesta_homogenea"] = stats["cv_percentual"] <= 25.0

    # Detecção de outliers por IQR (só faz sentido com n >= 4)
    if len(df) >= 4:
        q1 = df['valor'].quantile(0.25)
        q3 = df['valor'].quantile(0.75)
        iqr = q3 - q1
        limite_inferior = q1 - 1.5 * iqr
        limite_superior = q3 + 1.5 * iqr

        df = df.copy()
        df['is_outlier'] = (
            (df['valor'] < limite_inferior) | (df['valor'] > limite_superior)
        )
        outliers = df[df['is_outlier']].to_dict('records')
        limpos = df[~df['is_outlier']]

        stats["outliers_detectados"] = outliers
        stats["limite_inferior_iqr"] = float(limite_inferior)
        stats["limite_superior_iqr"] = float(limite_superior)
        stats["media_sem_outliers"] = float(limpos['valor'].mean())
        stats["mediana_sem_outliers"] = float(limpos['valor'].median())
    else:
        stats["outliers_detectados"] = []
        stats["observacao"] = "n < 4: análise de outliers (IQR) não aplicável."
        stats["media_sem_outliers"] = stats["media"]
        stats["mediana_sem_outliers"] = stats["mediana"]

    # Recomendação textual de critério (apenas sugestão)
    if stats["cv_percentual"] > 25.0:
        stats["criterio_sugerido"] = (
            "Mediana (cesta heterogênea, CV > 25%). Avaliar descarte de outliers."
        )
    else:
        stats["criterio_sugerido"] = (
            "Média ou mediana (cesta homogênea, CV <= 25%). Menor valor "
            "também é aceitável se houver justificativa de economicidade."
        )

    return stats


if __name__ == "__main__":
    try:
        input_data = json.loads(sys.argv[1])
        resultado = analisar_precos(input_data)
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    except IndexError:
        print(json.dumps({
            "error": "Uso: python analise_precos.py '[{\"valor\": 10.0}, ...]'"
        }))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
