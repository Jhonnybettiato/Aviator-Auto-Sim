import streamlit as st
import time

# 1. Configuración de página
st.set_page_config(page_title="Aviator Auto-Sim v1.0", page_icon="🤖", layout="wide")

# --- DISEÑO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #111827; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    .auto-status { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-bottom: 10px; }
    .log-container { background-color: #000; color: #00ff41; padding: 15px; border-radius: 5px; font-family: monospace; height: 250px; overflow-y: auto; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN ---
if 'historial' not in st.session_state: st.session_state.historial = []
if 'log' not in st.session_state: st.session_state.log = ["🤖 Sistema Iniciado..."]
if 'saldo_sim' not in st.session_state: st.session_state.saldo_sim = 0.0
# Usamos una llave para saber si el usuario cambió el capital manualmente
if 'capital_anterior' not in st.session_state: st.session_state.capital_anterior = 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración")
    capital_prueba = st.number_input("Capital de Prueba Gs.", value=100000, step=10000)
    
    # LÓGICA DE ACTUALIZACIÓN FORZADA:
    # Si el capital_prueba es diferente al que teníamos guardado, reseteamos el saldo
    if capital_prueba != st.session_state.capital_anterior:
        st.session_state.saldo_sim = float(capital_prueba)
        st.session_state.capital_anterior = float(capital_prueba)
        st.session_state.log.append(f"🔄 Capital reiniciado a {capital_prueba:,} Gs")
    
    modo = st.selectbox("Estrategia Automática:", 
                        ["Estrategia del Hueco 10x o +", "Cazador de Rosas (10x)", "Estrategia 2x2", "Conservadora (1.50x)"])
    
    monto_apuesta = st.number_input("Monto por Apuesta Gs.", value=2000, step=1000)

# --- LÓGICA DEL CEREBRO AUTOMÁTICO ---
def procesar_simulacion():
    if st.session_state.entrada_auto:
        try:
            val = float(st.session_state.entrada_auto.replace(',', '.'))
            st.session_state.historial.append(val)
            
            # 1. Determinar si el bot debía entrar en esta ronda
            hueco = 0
            for h in reversed(st.session_state.historial[:-1]): # Excluimos el actual para ver la decisión previa
                if h >= 10: break
                hueco += 1
            
            debe_apostar = False
            target = 1.50
            
            if modo == "Estrategia del Hueco 10x o +":
                target = 10.0
                if hueco >= 25: debe_apostar = True
            elif modo == "Cazador de Rosas (10x)":
                target = 10.0
                debe_apostar = True # Apuesta siempre buscando rosa
            elif modo == "Estrategia 2x2":
                target = 2.0
                if len(st.session_state.historial) >= 2 and st.session_state.historial[-2] < 2.0: debe_apostar = True
            else:
                target = 1.50
                debe_apostar = True

            # 2. Ejecutar apuesta virtual
            if debe_apostar:
                st.session_state.saldo_sim -= monto_apuesta
                if val > target:
                    premio = monto_apuesta * target
                    st.session_state.saldo_sim += premio
                    st.session_state.log.append(f"✅ GANADO: Vuelo {val}x | Apuesta {int(monto_apuesta):,} | +{int(premio-monto_apuesta):,} Gs")
                else:
                    st.session_state.log.append(f"❌ PERDIDO: Vuelo {val}x | Apuesta {int(monto_apuesta):,} | -{int(monto_apuesta):,} Gs")
            else:
                st.session_state.log.append(f"👀 OBSERVANDO: Vuelo {val}x | No cumple condiciones.")

        except: pass
        st.session_state.entrada_auto = ""

# --- INTERFAZ PRINCIPAL ---
st.title("🤖 Aviator Auto-Sim Lab")
st.write("Carga los resultados y el bot decidirá solo si 'apuesta' o no según la estrategia.")

c1, c2 = st.columns([1, 2])

with c1:
    st.metric("Saldo Virtual", f"{int(st.session_state.saldo_sim):,} Gs")
    st.text_input("Ingresar Resultado:", key="entrada_auto", on_change=procesar_simulacion)
    
    # Status visual del bot
    hueco_actual = 0
    for v in reversed(st.session_state.historial):
        if v >= 10: break
        hueco_actual += 1
    
    if "Hueco" in modo and hueco_actual < 25:
        st.markdown('<div class="auto-status" style="background-color: #2d3436;">ESPERANDO HUECO...</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="auto-status" style="background-color: #00ff41; color: black;">BOT ACTIVO / BUSCANDO ENTRADA</div>', unsafe_allow_html=True)

with c2:
    st.write("📝 Registro de Operaciones:")
    log_text = "\n".join(reversed(st.session_state.log))
    st.markdown(f'<div class="log-container">{log_text}</div>', unsafe_allow_html=True)

st.markdown("---")
# Historial de burbujas (reutilizado)
if st.session_state.historial:
    html_b = ""
    for val in reversed(st.session_state.historial[-20:]):
        color = "#3498db" if val < 2.0 else "#9b59b6" if val < 10.0 else "#e91e63"
        html_b += f'<div style="min-width:40px; height:40px; border-radius:50%; background:{color}; display:flex; align-items:center; justify-content:center; margin:5px; font-weight:bold; font-size:10px;">{val:.2f}</div>'
    st.markdown(f'<div style="display:flex; overflow-x:auto;">{html_b}</div>', unsafe_allow_html=True)
