import streamlit as st
import yfinance as yf
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

# Configuración de la página web
st.set_page_config(page_title="Mi Mini-eToro", page_icon="📈", layout="centered")

# Configurar autorefresco cada 3 segundos para ver el movimiento en tiempo real
count = st_autorefresh(interval=3000, limit=None, key="bot_autorefresh_counter")

st.title("📈 Mini-eToro Bot Trader - Simulador en Vivo")

# --- INICIALIZAR LA CARTERA VIRTUAL EN MEMORIA ---
if 'efectivo' not in st.session_state:
    st.session_state.efectivo = 10000.0
    st.session_state.unidades = 0.0
    st.session_state.precio_compra = 0.0
    st.session_state.en_posicion = False
    st.session_state.historial = []

# --- BARRA LATERAL (CONFIGURACIÓN) ---
st.sidebar.header("⚙️ Configuración del Bot")
ticker = st.sidebar.selectbox("Selecciona Activo", ["BTC-USD", "ETH-USD", "AAPL", "TSLA"])
stop_loss_pct = st.sidebar.slider("Stop-Loss (%)", min_value=0.1, max_value=5.0, value=0.5) / 100.0 # Margen ajustado para pruebas rápidas
take_profit_pct = st.sidebar.slider("Take-Profit (%)", min_value=0.1, max_value=5.0, value=0.8) / 100.0

# Botón para reiniciar la cartera
if st.sidebar.button("🔄 Reiniciar Cartera a 10,000$"):
    st.session_state.efectivo = 10000.0
    st.session_state.unidades = 0.0
    st.session_state.precio_compra = 0.0
    st.session_state.en_posicion = False
    st.session_state.historial = []
    st.rerun()

# --- FUNCIONES DE MERCADO ---
def obtener_precio_actual(simbolo):
    try:
        activo = yf.Ticker(simbolo)
        hist = activo.history(period="1d", interval="1m")
        if not hist.empty:
            return float(hist['Close'].iloc[-1]), hist
    except Exception as e:
        pass
    return None, pd.DataFrame()

precio_actual, datos_df = obtener_precio_actual(ticker)

if precio_actual is not None:
    # --- LÓGICA DE SIMULACIÓN DE COMPRA / VENTA / RIESGO ---
    valor_en_activo = st.session_state.unidades * precio_actual
    patrimonio_total = st.session_state.efectivo + valor_en_activo

    if not st.session_state.en_posicion:
        # Si no tenemos posición, compramos usando el efectivo disponible
        if st.session_state.efectivo > 0:
            st.session_state.unidades = st.session_state.efectivo / precio_actual
            st.session_state.precio_compra = precio_actual
            st.session_state.efectivo = 0.0
            st.session_state.en_posicion = True
            st.session_state.historial.insert(0, {
                "Hora": time.strftime('%H:%M:%S'),
                "Tipo": "🟢 COMPRA",
                "Precio": f"${precio_actual:,.2f}",
                "Detalle": f"Comprado {ticker}"
            })
    else:
        # Si estamos posicionados, comprobamos Stop-Loss o Take-Profit
        cambio = (precio_actual - st.session_state.precio_compra) / st.session_state.precio_compra

        if cambio <= -stop_loss_pct or cambio >= take_profit_pct:
            # Venta por riesgo o beneficio
            nuevo_efectivo = st.session_state.unidades * precio_actual
            resultado = nuevo_efectivo - (st.session_state.unidades * st.session_state.precio_compra)
            tipo_venta = "🔴 STOP-LOSS" if cambio <= -stop_loss_pct else "🔵 TAKE-PROFIT"
            
            st.session_state.efectivo = nuevo_efectivo
            st.session_state.unidades = 0.0
            st.session_state.en_posicion = False
            
            st.session_state.historial.insert(0, {
                "Hora": time.strftime('%H:%M:%S'),
                "Tipo": tipo_venta,
                "Precio": f"${precio_actual:,.2f}",
                "Detalle": f"Resultado: {resultado:+,.2f}$ ({cambio*100:+.2f}%)"
            })

    # --- MÉTRICAS VISUALES DE LA CARTERA ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Patrimonio Total", value=f"${patrimonio_total:,.2f}", delta=f"{patrimonio_total - 10000:+,.2f}$")
    with col2:
        st.metric(label="Efectivo Libre", value=f"${st.session_state.efectivo:,.2f}")
    with col3:
        st.metric(label=f"Precio {ticker}", value=f"${precio_actual:,.2f}")

    st.markdown("---")

    # --- GRÁFICO EN VIVO ---
    st.subheader("📊 Gráfico de Mercado")
    if not datos_df.empty:
        st.line_chart(datos_df['Close'])

    # --- HISTORIAL DE OPERACIONES (CÓMO SE MUEVE EL DINERO) ---
    st.subheader("📜 Historial de Operaciones del Bot")
    if len(st.session_state.historial) > 0:
        df_historial = pd.DataFrame(st.session_state.historial)
        st.dataframe(df_historial, use_container_width=True)
    else:
        st.info("Esperando la primera operación de compra...")

else:
    st.error("Conectando con el mercado en tiempo real...")

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Simulador automático de trading en la nube.</p>", unsafe_allow_html=True)
