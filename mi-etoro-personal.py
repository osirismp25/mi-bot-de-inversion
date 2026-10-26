import streamlit as st
import yfinance as yf
import pandas as pd
import time

# Configuración de la página web estilo app móvil/financiera
st.set_page_config(page_title="Mi Mini-eToro", page_icon="📈", layout="centered")

st.title("📈 Mini-eToro Bot Trader")
st.write("Simulador de trading en tiempo real con datos de mercado.")

# --- BARRA LATERAL (CONFIGURACIÓN) ---
st.sidebar.header("⚙️ Configuración del Bot")
ticker = st.sidebar.selectbox("Selecciona Activo", ["BTC-USD", "ETH-USD", "AAPL", "TSLA", "MSFT"])
capital_inicial = st.sidebar.number_input("Capital Virtual ($)", value=10000.0, step=500.0)
stop_loss_pct = st.sidebar.slider("Stop-Loss (%)", min_value=1.0, max_value=10.0, value=2.0) / 100.0
take_profit_pct = st.sidebar.slider("Take-Profit / Ganancia (%)", min_value=1.0, max_value=20.0, value=3.0) / 100.0

# --- FUNCIONES DE MERCADO ---
@st.cache_data(ttl=60) # Guarda en caché los datos unos segundos para no saturar la API
def obtener_datos_mercado(simbolo):
    try:
        activo = yf.Ticker(simbolo)
        # Obtenemos datos recientes de la jornada
        hist = activo.history(period="5d", interval="1h")
        return hist
    except Exception as e:
        return pd.DataFrame()

# Cargar datos del activo elegido
datos_df = obtener_datos_mercado(ticker)

if not datos_df.empty:
    precio_actual = float(datos_df['Close'].iloc[-1])
    
    # --- MÉTRICAS VISUALES (ESTILO APP) ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label=f"Precio Actual ({ticker})", value=f"${precio_actual:,.2f}")
    with col2:
        st.metric(label="Capital Disponible", value=f"${capital_inicial:,.2f}")

    st.markdown("---")

    # --- GRÁFICO INTERACTIVO ---
    st.subheader("📊 Gráfico de Evolución del Precio")
    st.line_chart(datos_df['Close'])

    # --- SIMULADOR DE BOT (PANEL DE CONTROL) ---
    st.subheader("🤖 Estado del Automatismo")
    
    # Botón interactivo para simular el ciclo de análisis del bot
    if st.button("🚀 Ejecutar Ciclo de Análisis y Operativa", type="primary"):
        with st.spinner("Analizando el mercado y evaluando riesgo..."):
            time.sleep(1) # Pequeña pausa visual de carga
            
            # Lógica simulada de toma de decisiones basada en el precio
            # (Aquí aplicamos tu regla de riesgo)
            st.success(f"Análisis completado para {ticker}.")
            st.info(f"💡 **Estado:** El bot está vigilando el nivel de riesgo (Stop-Loss configurado al {stop_loss_pct*100}%). Precio vigilado: ${precio_actual:,.2f}")
            
            # Simulador visual de compra/venta basado en condiciones aleatorias o técnicas simples para la demo
            if precio_actual % 2 == 0: # Condición de ejemplo para simular la entrada
                st.write("🟢 **Señal de Oportunidad detectada:** Posición simulada abierta correctamente.")
            else:
                st.write("⏳ **Mercado en rango:** El bot prefiere esperar una mejor oportunidad de entrada.")
else:
    st.error("No se pudieron cargar los datos del mercado en este momento. Revisa tu conexión a internet.")

# Pie de página estilo app
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Desarrollado como prototipo de inversión automatizada.</p>", unsafe_allow_html=True)