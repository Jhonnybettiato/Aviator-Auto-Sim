import streamlit as st
from datetime import datetime
import pytz
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from collections import Counter
import io

# 1. Configuración de página
st.set_page_config(page_title="Aviator Predictor Pro v10.0", page_icon="🦅", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0a0a0f; }
    .main-header { 
        background: linear-gradient(90deg, #ff4444, #ff8844, #ff4444);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem; 
        font-weight: 900; 
        text-align: center; 
        padding: 15px; 
        text-transform: uppercase; 
        letter-spacing: 4px; 
        border-bottom: 3px solid #ff4444;
        margin-bottom: 20px;
        text-shadow: 0 0 30px rgba(255, 68, 68, 0.5);
    }
    .elite-card { 
        background: linear-gradient(145deg, #1a1a25, #12121a); 
        padding: 20px; 
        border-radius: 15px; 
        text-align: center; 
        border: 1px solid #333; 
        height: 100%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .elite-card:hover {
        transform: translateY(-2px);
        border-color: #ff4444;
    }
    .label-elite { 
        color: #888 !important; 
        font-weight: 700; 
        text-transform: uppercase; 
        font-size: 0.75rem; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        gap: 5px; 
        margin-bottom: 8px; 
    }
    .valor-elite { 
        color: #FFFFFF !important; 
        font-size: 2rem; 
        font-weight: 900; 
        margin-bottom: 0px; 
    }
    .cronometro { 
        color: #00ff88; 
        font-family: 'Courier New', monospace; 
        font-size: 0.9rem; 
        font-weight: bold; 
        margin-top: 8px;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
    }
    
    .prediction-card {
        background: linear-gradient(145deg, #1a1a25, #0d0d12);
        border: 2px solid;
        border-radius: 20px;
        padding: 25px;
        margin: 15px 0;
    }
    
    .prediction-high { border-color: #00ff88; box-shadow: 0 0 20px rgba(0, 255, 136, 0.2); }
    .prediction-medium { border-color: #ff8844; box-shadow: 0 0 20px rgba(255, 136, 68, 0.2); }
    .prediction-low { border-color: #ff4444; box-shadow: 0 0 20px rgba(255, 68, 68, 0.2); }
    .prediction-hot { border-color: #ff00ff; box-shadow: 0 0 30px rgba(255, 0, 255, 0.4); animation: pulse 2s infinite; }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    .confidence-bar {
        height: 8px;
        border-radius: 4px;
        background: #252535;
        overflow: hidden;
        margin-top: 10px;
    }
    
    .confidence-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
    }
    
    input:focus { 
        border: 2px solid #ff4444 !important; 
        box-shadow: 0 0 15px rgba(255, 68, 68, 0.5) !important;
        background-color: #0a0a0f !important;
    }

    .burbuja { 
        min-width: 70px; 
        height: 65px; 
        border-radius: 35px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        font-weight: 900; 
        color: white; 
        margin-right: 8px; 
        font-size: 1rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .burbuja:hover {
        transform: scale(1.1);
    }
    
    .pattern-box {
        background: #12121a;
        border-radius: 10px;
        padding: 15px;
        margin: 5px 0;
        border-left: 4px solid #ff4444;
    }
    
    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #252535;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Inicialización de Estados
py_tz = pytz.timezone('America/Asuncion')

if 'historial' not in st.session_state: st.session_state.historial = []
if 'registro_saldos' not in st.session_state: st.session_state.registro_saldos = []
if 'registro_tiempos' not in st.session_state: st.session_state.registro_tiempos = []
if 'intervalos_rosas' not in st.session_state: st.session_state.intervalos_rosas = []
if 'rondas_desde_ultima' not in st.session_state: st.session_state.rondas_desde_ultima = 0
if 'saldo_dinamico' not in st.session_state: st.session_state.saldo_dinamico = 475000.0
if 'h_10x' not in st.session_state: st.session_state.h_10x = "00:00"
if 'h_100x' not in st.session_state: st.session_state.h_100x = "---"
if 'key_id' not in st.session_state: st.session_state.key_id = 0
if 'cap_ini' not in st.session_state: st.session_state.cap_ini = 475000.0
if 'predictions' not in st.session_state: st.session_state.predictions = []
if 'last_pattern' not in st.session_state: st.session_state.last_pattern = None

# --- FUNCIÓN DE PREDICCIÓN INTELIGENTE ---
def analyze_patterns(historial):
    """Analisa padrões no histórico e retorna previsões"""
    if len(historial) < 5:
        return None
    
    analysis = {
        'total_signals': len(historial),
        'avg': sum(historial) / len(historial),
        'last_10_avg': sum(historial[-10:]) / min(10, len(historial)) if historial else 0,
        'last_5_avg': sum(historial[-5:]) / min(5, len(historial)) if historial else 0,
        'trend': 'neutral',
        'confidence': 0,
        'prediction': None,
        'patterns': [],
        'sequence_analysis': {},
        'probability_next': {}
    }
    
    # 1. Análise de Tendência
    if len(historial) >= 10:
        avg_first_5 = sum(historial[-10:-5]) / 5
        avg_last_5 = sum(historial[-5:]) / 5
        
        if avg_last_5 > avg_first_5 * 1.3:
            analysis['trend'] = 'rising'
        elif avg_last_5 < avg_first_5 * 0.7:
            analysis['trend'] = 'falling'
        else:
            analysis['trend'] = 'stable'
    
    # 2. Contagem de rondas sem valores altos
    rondas_sin_alto = 0
    for val in reversed(historial):
        if val < 2.0:
            rondas_sin_alto += 1
        else:
            break
    analysis['rondas_sin_alto'] = rondas_sin_alto
    
    # 3. Análise de Sequências
    sequences = {'low': 0, 'medium': 0, 'high': 0}
    current_seq = 1
    seq_type = 'low' if historial[0] < 1.5 else 'medium' if historial[0] < 2.5 else 'high'
    
    for i in range(1, len(historial)):
        val = historial[i]
        current_type = 'low' if val < 1.5 else 'medium' if val < 2.5 else 'high'
        
        if current_type == seq_type:
            current_seq += 1
        else:
            sequences[seq_type] = max(sequences[seq_type], current_seq)
            seq_type = current_type
            current_seq = 1
    
    analysis['max_sequences'] = sequences
    analysis['current_sequence'] = rondas_sin_alto
    
    # 4. Probabilidade baseada no histórico
    total = len(historial)
    bajos = sum(1 for v in historial if v < 1.5)
    medios = sum(1 for v in historial if 1.5 <= v < 2.5)
    altos = sum(1 for v in historial if 2.5 <= v < 5)
    muy_altos = sum(1 for v in historial if v >= 5)
    
    analysis['probability_next'] = {
        'bajo (<1.5x)': (bajos / total) * 100,
        'medio (1.5-2.5x)': (medios / total) * 100,
        'alto (2.5-5x)': (altos / total) * 100,
        'muy_alto (>5x)': (muy_altos / total) * 100
    }
    
    # 5. Detecção de padrões específicos
    patterns_found = []
    
    # Padrão: Muitos baixos seguidos = Alto próximo
    if rondas_sin_alto >= 8:
        patterns_found.append({
            'name': '🔥 ACUMULAÇÃO CRÍTICA',
            'desc': f'{rondas_sin_alto} rodadas sem valor alto',
            'signal': 'ALTO PROVÁVEL',
            'confidence': min(50 + rondas_sin_alto * 3, 95),
            'recommendation': 'ENTRAR AGORA',
            'color': 'hot'
        })
    elif rondas_sin_alto >= 5:
        patterns_found.append({
            'name': '⚠️ Acumulação Detectada',
            'desc': f'{rondas_sin_alto} rodadas sem valor alto',
            'signal': 'FICAR ATENTO',
            'confidence': 40 + rondas_sin_alto * 5,
            'recommendation': 'PREPARAR ENTRADA',
            'color': 'medium'
        })
    
    # Padrão: Alternância
    if len(historial) >= 4:
        last_4 = historial[-4:]
        alternancia = all(
            (last_4[i] < 2 and last_4[i+1] >= 2) or (last_4[i] >= 2 and last_4[i+1] < 2)
            for i in range(3)
        )
        if alternancia:
            next_should_be = 'ALTO' if historial[-1] < 2 else 'BAIXO'
            patterns_found.append({
                'name': '🔄 Padrão de Alternância',
                'desc': 'Alternância consistente detectada',
                'signal': f'Próximo deve ser {next_should_be}',
                'confidence': 65,
                'recommendation': 'SEGUIR PADRÃO',
                'color': 'medium'
            })
    
    # Padrão: Dois altos seguidos = Provável baixo
    if len(historial) >= 2 and historial[-1] >= 2.5 and historial[-2] >= 2.5:
        patterns_found.append({
            'name': '📉 Dois Altos Seguidos',
            'desc': 'Após dois valores altos, geralmente vem baixo',
            'signal': 'PRÓXIMO SERÁ BAIXO',
            'confidence': 70,
            'recommendation': 'NÃO ENTRAR / SAIR CEDO',
            'color': 'low'
        })
    
    # Padrão: Média móvel
    if len(historial) >= 20:
        mm10 = sum(historial[-10:]) / 10
        mm20 = sum(historial[-20:]) / 20
        
        if mm10 > mm20 * 1.2:
            patterns_found.append({
                'name': '📈 Tendência de Alta',
                'desc': f'Média 10 ({mm10:.2f}) > Média 20 ({mm20:.2x})',
                'signal': 'MOMENTO BOM',
                'confidence': 60,
                'recommendation': 'ENTRAR',
                'color': 'high'
            })
        elif mm10 < mm20 * 0.8:
            patterns_found.append({
                'name': '📉 Tendência de Baixa',
                'desc': f'Média 10 ({mm10:.2f}) < Média 20 ({mm20:.2f})',
                'signal': 'MOMENTO RUIM',
                'confidence': 60,
                'recommendation': 'AGUARDAR',
                'color': 'low'
            })
    
    # Padrão: Horas com mais rosas
    if len(historial) >= 30:
        hora_atual = datetime.now(py_tz).hour
        rosas_por_hora = {}
        for i, val in enumerate(historial):
            if val >= 2.0:
                hora = st.session_state.registro_tiempos[i][:2] if i < len(st.session_state.registro_tiempos) else '00'
                rosas_por_hora[hora] = rosas_por_hora.get(hora, 0) + 1
        
        hora_str = f"{hora_atual:02d}"
        if hora_str in rosas_por_hora and rosas_por_hora[hora_str] >= 3:
            patterns_found.append({
                'name': '⏰ Horário Favorável',
                'desc': f'Hora atual ({hora_atual:02d}:00) tem histórico de rosas',
                'signal': 'HORA BOA',
                'confidence': 55,
                'recommendation': 'APROVEITAR',
                'color': 'medium'
            })
    
    analysis['patterns'] = patterns_found
    
    # 6. Previsão Final
    if patterns_found:
        # Pega o padrão com maior confiança
        best_pattern = max(patterns_found, key=lambda x: x['confidence'])
        analysis['prediction'] = best_pattern
        analysis['confidence'] = best_pattern['confidence']
    else:
        # Previsão baseada em probabilidade
        if rondas_sin_alto >= 5:
            analysis['prediction'] = {
                'name': '📊 Análise Estatística',
                'desc': 'Baseado no histórico geral',
                'signal': 'ACUMULAÇÃO EM ANDAMENTO',
                'confidence': 35 + rondas_sin_alto * 3,
                'recommendation': 'OBSERVAR',
                'color': 'medium'
            }
        else:
            analysis['prediction'] = {
                'name': '📊 Dados Insuficientes',
                'desc': 'Aguardando mais sinais',
                'signal': 'NEUTRO',
                'confidence': 30,
                'recommendation': 'AGUARDAR',
                'color': 'low'
            }
    
    return analysis

def calcular_cronometro(hora_str):
    if hora_str == "---" or hora_str == "00:00": return "00m 00s"
    try:
        ahora = datetime.now(py_tz)
        hora_obj = datetime.strptime(hora_str, "%H:%M")
        hora_final = ahora.replace(hour=hora_obj.hour, minute=hora_obj.minute, second=0, microsecond=0)
        diff = ahora - hora_final
        ts = int(diff.total_seconds())
        if ts < 0: ts += 86400
        return f"{ts // 60:02d}m {ts % 60:02d}s"
    except: return "00m 00s"

def registrar():
    curr_key = f"input_{st.session_state.key_id}"
    if curr_key in st.session_state:
        raw = st.session_state[curr_key].replace(',', '.')
        if raw:
            try:
                val = float(raw)
                if val <= 0:
                    st.error("❌ Valor deve ser maior que 0!")
                    return
                    
                apuesta = st.session_state.in_apuesta
                jugado = st.session_state.in_chk
                
                # Cálculo correto de ganho
                if jugado and val >= 10.0:
                    gan = apuesta * (val - 1)  # Lucro = aposta * (multiplicador - 1)
                elif jugado:
                    gan = -apuesta  # Perdeu a aposta
                else:
                    gan = 0.0
                    
                ahora_f = datetime.now(py_tz).strftime("%H:%M")
                
                if val >= 10.0:
                    st.session_state.intervalos_rosas.append(st.session_state.rondas_desde_ultima)
                    st.session_state.rondas_desde_ultima = 0
                    st.session_state.h_10x = ahora_f
                    if val >= 100.0: 
                        st.session_state.h_100x = ahora_f
                        st.balloons()
                else:
                    st.session_state.rondas_desde_ultima += 1
                
                st.session_state.historial.append(val)
                st.session_state.registro_saldos.append(gan)
                st.session_state.registro_tiempos.append(ahora_f)
                st.session_state.saldo_dinamico += gan
                st.session_state.key_id += 1
                
                # Analisar padrão após adicionar
                analysis = analyze_patterns(st.session_state.historial)
                if analysis and analysis['prediction']:
                    st.session_state.predictions.append(analysis['prediction'])
                    
            except ValueError:
                st.error("❌ Valor inválido!")

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### ⚙️ CONFIGURAÇÕES")
    
    # Capital
    nuevo_cap = st.number_input("💰 Capital Inicial", 
                                value=float(st.session_state.cap_ini),
                                min_value=0.0,
                                step=1000.0)
    if nuevo_cap != st.session_state.cap_ini:
        st.session_state.saldo_dinamico += (nuevo_cap - st.session_state.cap_ini)
        st.session_state.cap_ini = nuevo_cap
        st.rerun()

    st.markdown("---")
    
    # Horários
    st.markdown("### 🕒 ÚLTIMAS ROSAS")
    st.session_state.h_10x = st.text_input("Última 10x (HH:MM)", value=st.session_state.h_10x)
    st.session_state.h_100x = st.text_input("Última 100x (HH:MM)", value=st.session_state.h_100x)

    st.markdown("---")
    
    # Estatísticas Rápidas
    st.markdown("### 📊 ESTATÍSTICAS")
    if st.session_state.historial:
        total = len(st.session_state.historial)
        rosas = sum(1 for v in st.session_state.historial if v >= 2.0)
        st.metric("Total Sinais", total)
        st.metric("Rosas (≥2x)", f"{rosas} ({rosas/total*100:.1f}%)")
        st.metric("Maior Sinal", f"{max(st.session_state.historial):.2f}x")
        st.metric("Média Geral", f"{sum(st.session_state.historial)/total:.2f}x")
    
    st.markdown("---")
    
    # Intervalos entre rosas
    st.markdown("### 📈 INTERVALOS ENTRE ROSAS")
    if st.session_state.intervalos_rosas:
        avg_interval = sum(st.session_state.intervalos_rosas) / len(st.session_state.intervalos_rosas)
        st.metric("Média de Intervalo", f"{avg_interval:.1f} rodadas")
        
        for i, dist in enumerate(reversed(st.session_state.intervalos_rosas[-10:])):
            color = "🟢" if dist <= 10 else "🟡" if dist <= 20 else "🔴"
            st.markdown(f"{color} Rosa {len(st.session_state.intervalos_rosas)-i}: **{dist} rondas**")
    else:
        st.info("Aguardando primeira rosa...")

    st.markdown("---")
    
    # Exportar
    if st.session_state.historial and st.button("📥 Exportar CSV"):
        df = pd.DataFrame({
            'hora': st.session_state.registro_tiempos,
            'valor': st.session_state.historial,
            'ganho': st.session_state.registro_saldos
        })
        csv = df.to_csv(index=False)
        st.download_button("⬇️ Download", csv, "aviator_dados.csv", "text/csv")

    if st.button("🔄 REINICIAR TUDO", type="primary"):
        for k in list(st.session_state.keys()): 
            del st.session_state[k]
        st.rerun()

# --- INTERFAZ PRINCIPAL ---
st.markdown('<div class="main-header">🦅 AVIATOR PREDICTOR PRO v10.0</div>', unsafe_allow_html=True)

# Dashboard Superior
col1, col2, col3, col4, col5 = st.columns(5)

res_ac = st.session_state.saldo_dinamico - st.session_state.cap_ini
cor_ganho = "#00ff88" if res_ac >= 0 else "#ff4444"

with col1:
    st.markdown(f'''
    <div class="elite-card">
        <p class="label-elite">💰 SALDO</p>
        <h2 class="valor-elite">{int(st.session_state.saldo_dinamico):,}</h2>
    </div>''', unsafe_allow_html=True)

with col2:
    st.markdown(f'''
    <div class="elite-card" style="border-color: {cor_ganho};">
        <p class="label-elite">📈 LUCRO/PREJU</p>
        <h2 class="valor-elite" style="color: {cor_ganho} !important;">{int(res_ac):,}</h2>
    </div>''', unsafe_allow_html=True)

with col3:
    st.markdown(f'''
    <div class="elite-card">
        <p class="label-elite">✈️ ÚLTIMA 10X</p>
        <h2 class="valor-elite" style="color: #9b59b6 !important;">{st.session_state.h_10x}</h2>
        <p class="cronometro">⏱️ {calcular_cronometro(st.session_state.h_10x)}</p>
    </div>''', unsafe_allow_html=True)

with col4:
    st.markdown(f'''
    <div class="elite-card">
        <p class="label-elite">🚀 ÚLTIMA 100X</p>
        <h2 class="valor-elite" style="color: #e91e63 !important;">{st.session_state.h_100x}</h2>
        <p class="cronometro">⏱️ {calcular_cronometro(st.session_state.h_100x)}</p>
    </div>''', unsafe_allow_html=True)

with col5:
    total_rosas = sum(1 for v in st.session_state.historial if v >= 2.0)
    st.markdown(f'''
    <div class="elite-card">
        <p class="label-elite">🌸 TOTAL ROSAS</p>
        <h2 class="valor-elite" style="color: #ff69b4 !important;">{total_rosas}</h2>
    </div>''', unsafe_allow_html=True)

# --- SEÇÃO DE PREDIÇÃO ---
st.markdown("---")
st.markdown("### 🔮 ANÁLISE E PREDIÇÃO INTELIGENTE")

if st.session_state.historial:
    analysis = analyze_patterns(st.session_state.historial)
    
    if analysis:
        # Cards de Análise
        col_pred1, col_pred2, col_pred3 = st.columns(3)
        
        with col_pred1:
            st.metric("📊 Média Últimos 10", f"{analysis['last_10_avg']:.2f}x")
            st.metric("📉 Média Últimos 5", f"{analysis['last_5_avg']:.2f}x")
            st.metric("📈 Tendência", analysis['trend'].upper())
        
        with col_pred2:
            st.metric("🔥 Rodadas sem Alto", analysis['rondas_sin_alto'])
            st.metric("📊 Média Geral", f"{analysis['avg']:.2f}x")
            if analysis['max_sequences']:
                st.metric("🔢 Seq. Máx Baixos", analysis['max_sequences']['low'])
        
        with col_pred3:
            st.markdown("**🎯 Probabilidades:**")
            for cat, prob in analysis['probability_next'].items():
                cor_prob = "#00ff88" if prob > 30 else "#ff8844" if prob > 15 else "#ff4444"
                st.markdown(f"<span style='color: {cor_prob}'>{cat}: {prob:.1f}%</span>", unsafe_allow_html=True)
        
        # Padrões Detectados
        st.markdown("---")
        st.markdown("### 🎯 PADRÕES DETECTADOS")
        
        if analysis['patterns']:
            for pattern in analysis['patterns']:
                color_class = f"prediction-{pattern['color']}"
                conf_color = "#00ff88" if pattern['confidence'] >= 70 else "#ff8844" if pattern['confidence'] >= 50 else "#ff4444"
                
                st.markdown(f'''
                <div class="prediction-card {color_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0; color: #fff;">{pattern['name']}</h3>
                            <p style="color: #aaa; margin: 5px 0;">{pattern['desc']}</p>
                            <p style="color: {conf_color}; font-weight: bold; font-size: 1.2rem; margin: 10px 0;">
                                {pattern['signal']}
                            </p>
                            <p style="color: #fff; background: rgba(0,0,0,0.3); padding: 8px 15px; border-radius: 8px; display: inline-block;">
                                💡 {pattern['recommendation']}
                            </p>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 2.5rem; font-weight: 900; color: {conf_color};">{pattern['confidence']}%</div>
                            <div style="color: #888; font-size: 0.8rem;">CONFIANÇA</div>
                        </div>
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: {pattern['confidence']}%; background: linear-gradient(90deg, {conf_color}, {conf_color}88);"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.info("📊 Aguardando mais dados para detectar padrões...")
        
        # Previsão Principal
        if analysis['prediction']:
            st.markdown("---")
            pred = analysis['prediction']
            cor_pred = "#00ff88" if pred['confidence'] >= 70 else "#ff8844" if pred['confidence'] >= 50 else "#ff4444"
            
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, #1a1a25, #0d0d12); border: 3px solid {cor_pred}; border-radius: 20px; padding: 30px; text-align: center;">
                <h2 style="color: #fff; margin-bottom: 15px;">🎯 RECOMENDAÇÃO PRINCIPAL</h2>
                <div style="font-size: 3rem; font-weight: 900; color: {cor_pred}; margin: 20px 0;">
                    {pred['recommendation']}
                </div>
                <p style="color: #aaa; font-size: 1.1rem;">{pred['desc']}</p>
                <div style="margin-top: 20px; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 10px; display: inline-block;">
                    <span style="color: {cor_pred}; font-weight: bold;">Confiança: {pred['confidence']}%</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Alerta visual se muito quente
            if analysis['rondas_sin_alto'] >= 10:
                st.error("🔥🔥🔥 ATENÇÃO! Muitas rodadas sem valor alto! Momento pode ser bom para entrada!")
                st.snow()
    
else:
    st.info("📊 Adicione sinais para ver a análise e predições...")

# --- SEMÁFORO CORRIGIDO ---
st.markdown("---")
sin_rosa = st.session_state.rondas_desde_ultima

if sin_rosa <= 3:
    col_sem, msg, emoji = "#ff4444", "🚫 ACABOU DE SAIR ROSA - AGUARDAR", "⛔"
elif sin_rosa <= 8:
    col_sem, msg, emoji = "#ff8844", "⚠️ PERÍODO DE RISCO - OBSERVAR", "⚠️"
elif sin_rosa <= 15:
    col_sem, msg, emoji = "#ffeb3b", "🟡 MOMENTO NEUTRO - AGUARDAR", "🟡"
elif sin_rosa <= 25:
    col_sem, msg, emoji = "#00ff88", "✅ MOMENTO FAVORÁVEL - PREPARAR", "✅"
else:
    col_sem, msg, emoji = "#ff00ff", "🔥🔥🔥 MUITO QUENTE! ENTRAR AGORA!", "🔥"

text_color = "black" if sin_rosa in range(4, 16) else "white"

st.markdown(f'''
<div style="background: linear-gradient(135deg, {col_sem}22, {col_sem}44); 
            border: 3px solid {col_sem}; 
            padding: 25px; 
            border-radius: 20px; 
            text-align: center; 
            margin: 20px 0;
            box-shadow: 0 0 30px {col_sem}66;">
    <div style="font-size: 4rem; margin-bottom: 10px;">{emoji}</div>
    <h1 style="color: {col_sem}; margin: 0; font-weight: 900; font-size: 3rem;">
        {sin_rosa}
    </h1>
    <h3 style="color: {col_sem}; margin: 10px 0; font-weight: 700;">
        RODADAS SEM ROSA
    </h3>
    <p style="color: {col_sem}; font-size: 1.3rem; font-weight: 600; margin-top: 15px;">
        {msg}
    </p>
</div>
''', unsafe_allow_html=True)

# --- ENTRADA DE DADOS ---
st.markdown("---")
st.markdown("### ✏️ REGISTRAR NOVO SINAL")

st.markdown('<div class="elite-card">', unsafe_allow_html=True)
col_r1, col_r2, col_r3, col_r4 = st.columns([2, 1, 0.8, 1])

with col_r1:
    st.text_input("VALOR DO MULTIPLICADOR", 
                  value="", 
                  key=f"input_{st.session_state.key_id}", 
                  on_change=registrar, 
                  placeholder="Ex: 2.45")

with col_r2:
    st.number_input("💵 APOSTA", 
                    value=2000, 
                    min_value=0,
                    step=500,
                    key="in_apuesta")

with col_r3:
    st.write("###")
    st.checkbox("✅ APOSTEI?", key="in_chk")

with col_r4:
    st.write("###")
    if st.button("🚀 REGISTRAR", use_container_width=True, type="primary"):
        registrar()

st.markdown('</div>', unsafe_allow_html=True)

# Foco automático
components.html(f"""
<script>
    function setFocus() {{
        var inputs = window.parent.document.querySelectorAll('input[placeholder="Ex: 2.45"]');
        if (inputs.length > 0) inputs[inputs.length - 1].focus();
    }}
    setFocus();
    setTimeout(setFocus, 500);
</script>
""", height=0)

# --- HISTÓRICO VISUAL ---
if st.session_state.historial:
    st.markdown("---")
    st.markdown("### 📜 HISTÓRICO RECENTE")
    
    h_html = ""
    for v in reversed(st.session_state.historial[-20:]):
        if v >= 10:
            bg_color = "#e91e63"
            border = "3px solid gold"
        elif v >= 2:
            bg_color = "#9b59b6"
            border = "none"
        elif v >= 1.5:
            bg_color = "#3498db"
            border = "none"
        else:
            bg_color = "#2c3e50"
            border = "none"
        
        h_html += f'<div class="burbuja" style="background-color: {bg_color}; border: {border};">{v:.2f}</div>'
    
    st.markdown(f'''
    <div style="display: flex; overflow-x: auto; padding: 20px; 
                background: linear-gradient(145deg, #12121a, #0a0a0f); 
                border-radius: 20px; 
                border: 1px solid #333;
                box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);">
        {h_html}
    </div>
    ''', unsafe_allow_html=True)

# --- BOTÃO DESFAZER ---
if st.session_state.historial:
    if st.button("↩️ DESFAZER ÚLTIMO", type="secondary"):
        if st.session_state.historial:
            last_val = st.session_state.historial.pop()
            if st.session_state.registro_tiempos:
                st.session_state.registro_tiempos.pop()
            if st.session_state.registro_saldos:
                ganho_removido = st.session_state.registro_saldos.pop()
                st.session_state.saldo_dinamico -= ganho_removido
            
            # Recalcular contador
            if last_val >= 10.0 and st.session_state.intervalos_rosas:
                st.session_state.rondas_desde_ultima = st.session_state.intervalos_rosas.pop()
            else:
                st.session_state.rondas_desde_ultima = max(0, st.session_state.rondas_desde_ultima - 1)
            
            st.rerun()

# --- TABELA COMPLETA ---
if st.session_state.historial:
    st.markdown("---")
    st.markdown("### 📋 REGISTRO COMPLETO")
    
    with st.expander("Ver tabela completa"):
        df_display = pd.DataFrame({
            '#': range(1, len(st.session_state.historial) + 1),
            'Hora': st.session_state.registro_tiempos,
            'Valor': [f"{v:.2f}x" for v in st.session_state.historial],
            'Ganho': [f"{g:+.0f}" for g in st.session_state.registro_saldos],
            'Tipo': ['🌸 ROSA' if v >= 2 else '🔵 MÉDIO' if v >= 1.5 else '⚫ BAIXO' 
                     for v in st.session_state.historial]
        })
        st.dataframe(df_display.iloc[::-1], use_container_width=True, hide_index=True)
