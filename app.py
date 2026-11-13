from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import json

app = Flask(__name__)

def gerar_dados_cortes_jogos(plataforma="reels", offset_dia=0):
    # Semente única combinando plataforma e o dia para manter consistência no gráfico
    seed_base = hash(str(plataforma)) % 1000 + offset_dia
    np.random.seed(seed_base)
    
    horas = list(range(24))
    dados = []
    
    for hora in horas:
        # Padrão comportamental específico para o consumo de VODs e Cortes de Jogos:
        # - Pico forte no fim de tarde (quando a galera sai da escola/trabalho)
        # - Pico noturno máximo (das 19h à 01h, onde o consumo de shorts/reels de games explode)
        # - Queda acentuada de madrugada
        
        base = 45 + 25 * np.sin((hora - 8) * np.pi / 12) + 18 * np.cos((hora - 21) * np.pi / 6)
        
        if 18 <= hora <= 23:
            base += 32  # Horário nobre de alta retenção para gaming
        elif 0 <= hora <= 2:
            base += 15  # Corujão gamer (madrugada ainda rende bem para shorts/reels de jogos)
        elif 12 <= hora <= 14:
            base += 10  # Janela de almoço
        elif 3 <= hora <= 8:
            base -= 40  # Madrugada morta / manhã cedo (baixa audiência)
            
        # Ruído estatístico controlado simulando o comportamento dinâmico do algoritmo
        ruido = np.random.uniform(-5, 5)
        score = max(5, min(100, int(base + ruido)))
        
        dados.append({
            "hora": f"{hora:02d}:00",
            "hora_num": hora,
            "score": score,
            "status": "Bom (> 50%)" if score >= 50 else "Ruim (< 50%)"
        })
        
    return pd.DataFrame(dados)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analisar", methods=["POST"])
def analisar():
    data = request.json or {}
    plataforma = data.get("plataforma", "reels")
    
    # Nicho fixado em Cortes de Jogos
    nicho = "Cortes de Jogos"
    
    df_hoje = gerar_dado_cortes = gerar_dados_cortes_jogos(plataforma, offset_dia=0)
    df_amanha = gerar_dados_cortes_jogos(plataforma, offset_dia=1)
    
    def criar_traces_linha(df):
        df = df.replace({np.nan: None})
        
        df_verde = df.copy()
        df_verde.loc[df_verde['score'] < 50, 'score'] = None
        
        df_vermelho = df.copy()
        df_vermelho.loc[df_vermelho['score'] >= 50, 'score'] = None
        
        y_verde = [None if pd.isna(val) else val for val in df_verde["score"].tolist()]
        y_vermelho = [None if pd.isna(val) else val for val in df_vermelho["score"].tolist()]
        
        trace_verde = {
            "x": df["hora"].tolist(),
            "y": y_verde,
            "type": "scatter",
            "mode": "lines+markers",
            "name": "Alta Retenção (> 50%)",
            "line": {"color": "#10B981", "width": 3},
            "marker": {"size": 8, "color": "#10B981"}
        }
        
        trace_vermelho = {
            "x": df["hora"].tolist(),
            "y": y_vermelho,
            "type": "scatter",
            "mode": "lines+markers",
            "name": "Baixa Retenção (< 50%)",
            "line": {"color": "#EF4444", "width": 3},
            "marker": {"size": 8, "color": "#EF4444"}
        }
        
        return [trace_verde, trace_vermelho]

    traces_hoje = criar_traces_linha(df_hoje)
    traces_amanha = criar_traces_linha(df_amanha)
    
    layout_base = {
        "plot_bgcolor": "#0f172a",
        "paper_bgcolor": "#1e293b",
        "font": {"color": "#f8fafc"},
        "xaxis": {"title": "Horários do Dia", "gridcolor": "#334155"},
        "yaxis": {"title": "Índice Preditivo de Visualização (%)", "range": [0, 105], "gridcolor": "#334155"},
        "shapes": [
            {
                "type": "line",
                "xref": "paper",
                "x0": 0,
                "x1": 1,
                "y0": 50,
                "y1": 50,
                "line": {"color": "#94a3b8", "width": 1.5, "dash": "dash"}
            }
        ],
        "margin": {"t": 40, "l": 50, "r": 30, "b": 40},
        "legend": {"orientation": "h", "y": 1.15}
    }
    
    layout_hoje = layout_base.copy()
    layout_hoje["title"] = f"Análise de Cortes de Jogos - Hoje ({plataforma.upper()})"
    
    layout_amanha = layout_base.copy()
    layout_amanha["title"] = f"Análise de Cortes de Jogos - Próximo Dia ({plataforma.upper()})"

    top_horarios = df_hoje.sort_values(by="score", ascending=False).head(3).to_dict(orient="records")

    return jsonify({
        "grafico_hoje": {"data": traces_hoje, "layout": layout_hoje},
        "grafico_amanha": {"data": traces_amanha, "layout": layout_amanha},
        "recomendacoes": top_horarios,
        "analise_ia": f"Modelo Preditivo otimizado para Cortes de Jogos no {plataforma.upper()}: A atenção do público gamer tende a se concentrar fortemente no início da noite e avançar pela madrugada. A linha tracejada em 50% separa o verde (horários ideais para postar seus cortes) do vermelho (períodos de baixa conversão)."
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)