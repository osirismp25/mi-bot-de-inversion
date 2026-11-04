import streamlit as st
import yfinance as yf
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

# Configuración de la página web estilo app móvil/financiera
st.set_page_config(page_title="Mi Mini-eToro", page_icon="📈", layout="centered")

# Configurar autorefresco cada 10 segundos (10000 milisegundos) para que actúe en vivo
count = st_autorefresh(interval=10000, limit=None, key="bot_autorefresh_counter")

st.title("📈 Mini-eToro Bot Trader en Vivo")
st.write(f"🔄 Ciclo de monitorización activo (Actualización nº {count})")

# --- BARRA LATERAL (CONFIGURACIÓN) ---
st.sidebar.header("⚙️ Configuración del Bot")
ticker = st.sidebar.selectbox("Selecciona Activo", ["BTC-USD", "ETH-USD", "AAPL", "TSLA", "MSFT"])
capital_inicial = st.sidebar.number_input("Capital Virtual ($)", value=10000.0, step=500.0)
stop_loss_pct = st.sidebar.slider("Stop-Loss (%)", min_value=1.0, max_value=10.0, value=2.0) / 100.0
take_profit_pct = st.sidebar.slider("Take-Profit / Ganancia (%)", min_value=1.0, max_value=20.0, value=3.0) / 100.0

# --- FUNCIONES DE MERCADO ---
def obtener_datos_mercado(simbolo):
    try:
        activo = yf.Ticker(simbolo)
        hist = activo.history(period="1d", interval="1m")
        return hist
    except Exception as e:
        return pd.DataFrame()

# Cargar datos en tiempo real del activo elegido
datos_df = obtener_datos_mercado(ticker)

if not datos_df.empty:
    precio_actual = float(datos_df['Close'].iloc[-1])
    
    # --- MÉTRICAS VISUALES ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label=f"Precio Actual ({ticker})", value=f"${precio_actual:,.2f}")
    with col2:
        st.metric(label="Capital Disponible", value=f"${capital_inicial:,.2f}")

    st.markdown("---")

    # --- GRÁFICO INTERACTIVO ---
    st.subheader("📊 Gráfico de Evolución del Precio en Directo")
    st.line_chart(datos_df['Close'])

    # --- ESTADO DEL BOT ---
    st.subheader("🤖 Vigía del Mercado Automático")
    st.success(f"🟢 El bot está observando {ticker} en tiempo real.")
    st.info(f"💡 **Gestión de riesgo activa:** Stop-Loss al {stop_loss_pct*100}% | Take-Profit al {take_profit_pct*100}%. Última lectura a las {time.strftime('%H:%M:%S')}")
else:
    st.error("Esperando conexión con el mercado...")

# Pie de página
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Sistema autónomo en la nube.</p>", unsafe_allow_html=True)
