import streamlit as st
import pandas as pd
import time
import ccxt
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# Configuración de la página web estilo app financiera
st.set_page_config(page_title="Mi Mini-eToro con OKX", page_icon="🌐", layout="centered")

# Refresco automático cada 3 segundos en vivo
st_autorefresh(interval=3000, limit=None, key="bot_autorefresh_counter")

st.title("🌐 Mi Mini-eToro + OKX Live")

# --- INICIALIZAR CARTERA VIRTUAL EN MEMORIA ---
if 'efectivo' not in st.session_state:
    st.session_state.efectivo = 10000.0
    st.session_state.unidades = 0.0
    st.session_state.precio_compra = 0.0
    st.session_state.en_posicion = False
    st.session_state.historial = []

# --- BARRA LATERAL (CONFIGURACIÓN Y FUENTE) ---
st.sidebar.header("⚙️ Configuración de Mercado")
fuente_datos = st.sidebar.selectbox("Fuente de Datos", ["OKX (Cripto)", "Yahoo Finance (Acciones/Crypto)"])

if fuente_datos == "OKX (Cripto)":
    ticker = st.sidebar.selectbox("Par OKX", ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"])
else:
    ticker = st.sidebar.selectbox("Activo Yahoo", ["BTC-USD", "ETH-USD", "AAPL", "TSLA"])

modo_operacion = st.sidebar.radio("Modo de Operación", ["🤖 Bot Automático", "👤 Manual (Tú decides)"])

stop_loss_pct = st.sidebar.slider("Stop-Loss (%)", 0.1, 5.0, 1.0) / 100.0
take_profit_pct = st.sidebar.slider("Take-Profit (%)", 0.1, 5.0, 1.5) / 100.0

if st.sidebar.button("🔄 Reiniciar Cuenta a $10,000"):
    st.session_state.efectivo = 10000.0
    st.session_state.unidades = 0.0
    st.session_state.precio_compra = 0.0
    st.session_state.en_posicion = False
    st.session_state.historial = []
    st.rerun()

# --- FUNCIONES DE OBTENCIÓN DE PRECIO (OKX / YAHOO) ---
def obtener_precio_en_vivo(fuente, simbolo):
    try:
        if fuente == "OKX (Cripto)":
            # Conexión pública a OKX vía CCXT
            exchange = ccxt.okx()
            ticker_info = exchange.fetch_ticker(simbolo)
            precio = float(ticker_info['last'])
            
            # Generar datos simulados recientes para mantener el gráfico bonito
            ohlcv = exchange.fetch_ohlcv(simbolo, timeframe='1m', limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['Close'] = df['close']
            return precio, df
        else:
            activo = yf.Ticker(simbolo)
            hist = activo.history(period="1d", interval="1m")
            if not hist.empty:
                return float(hist['Close'].iloc[-1]), hist
    except Exception as e:
        st.sidebar.error(f"Error de conexión: {e}")
    return None, pd.DataFrame()

precio_actual, datos_df = obtener_precio_en_vivo(fuente_datos, ticker)

if precio_actual is not None:
    valor_en_activo = st.session_state.unidades * precio_actual
    patrimonio_total = st.session_state.efectivo + valor_en_activo

    # --- LÓGICA DE AUTOMATIZACIÓN O RIESGO ---
    if modo_operacion == "🤖 Bot Automático":
        if not st.session_state.en_posicion and st.session_state.efectivo > 0:
            st.session_state.unidades = st.session_state.efectivo / precio_actual
            st.session_state.precio_compra = precio_actual
            st.session_state.efectivo = 0.0
            st.session_state.en_posicion = True
            st.session_state.historial.insert(0, {
                "Hora": time.strftime('%H:%M:%S'), "Tipo": "🤖 COMPRA BOT (OKX)",
                "Precio": f"${precio_actual:,.2f}", "Detalle": f"Entrada en {ticker}"
            })
        elif st.session_state.en_posicion:
            cambio = (precio_actual - st.session_state.precio_compra) / st.session_state.precio_compra
            if cambio <= -stop_loss_pct or cambio >= take_profit_pct:
                nuevo_efectivo = st.session_state.unidades * precio_actual
                resultado = nuevo_efectivo - (st.session_state.unidades * st.session_state.precio_compra)
                tipo = "🔴 STOP-LOSS" if cambio <= -stop_loss_pct else "🔵 TAKE-PROFIT"
                
                st.session_state.efectivo = nuevo_efectivo
                st.session_state.unidades = 0.0
                st.session_state.en_posicion = False
                st.session_state.historial.insert(0, {
                    "Hora": time.strftime('%H:%M:%S'), "Tipo": tipo,
                    "Precio": f"${precio_actual:,.2f}", "Detalle": f"Resultado: {resultado:+,.2f}$ ({cambio*100:+.2f}%)"
                })

    # --- MÉTRICAS PRINCIPALES ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Patrimonio Total", f"${patrimonio_total:,.2f}", f"{patrimonio_total - 10000:+,.2f}$")
    col2.metric("Efectivo Libre", f"${st.session_state.efectivo:,.2f}")
    col3.metric(f"Precio ({ticker})", f"${precio_actual:,.2f}")

    st.markdown("---")

    # --- PANEL MANUAL ---
    if modo_operacion == "👤 Manual (Tú decides)":
        st.subheader("🎯 Panel de Compra / Venta OKX")
        c_btn1, c_btn2 = st.columns(2)
        
        with c_btn1:
            if not st.session_state.en_posicion:
                if st.button("🟢 COMPRAR AHORA", use_container_width=True, type="primary"):
                    if st.session_state.efectivo > 0:
                        st.session_state.unidades = st.session_state.efectivo / precio_actual
                        st.session_state.precio_compra = precio_actual
                        st.session_state.efectivo = 0.0
                        st.session_state.en_posicion = True
                        st.session_state.historial.insert(0, {
                            "Hora": time.strftime('%H:%M:%S'), "Tipo": "🟢 COMPRA MANUAL",
                            "Precio": f"${precio_actual:,.2f}", "Detalle": f"Comprado {ticker} en OKX"
                        })
                        st.rerun()
            else:
                st.info("Ya tienes una posición abierta.")

        with c_btn2:
            if st.session_state.en_posicion:
                if st.button("🔴 VENDER Y COBRAR", use_container_width=True, type="secondary"):
                    nuevo_efectivo = st.session_state.unidades * precio_actual
                    resultado = nuevo_efectivo - (st.session_state.unidades * st.session_state.precio_compra)
                    st.session_state.efectivo = nuevo_efectivo
                    st.session_state.unidades = 0.0
                    st.session_state.en_posicion = False
                    st.session_state.historial.insert(0, {
                        "Hora": time.strftime('%H:%M:%S'), "Tipo": "👤 VENTA MANUAL",
                        "Precio": f"${precio_actual:,.2f}", "Detalle": f"Cierre OKX | Resultado: {resultado:+,.2f}$"
                    })
                    st.rerun()
            else:
                st.warning("No hay posiciones abiertas.")
        st.markdown("---")

    # --- GRÁFICO EN VIVO ---
    st.subheader("📊 Gráfico de Velas / Línea en Directo")
    if not datos_df.empty:
        st.line_chart(datos_df['Close'])

    # --- HISTORIAL ---
    st.subheader("📜 Registro de Operaciones")
    if len(st.session_state.historial) > 0:
        st.dataframe(pd.DataFrame(st.session_state.historial), use_container_width=True)
    else:
        st.info("Esperando operaciones...")

else:
    st.error("Conectando con el servidor de OKX / Mercado...")
