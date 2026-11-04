import streamlit as st
import pandas as pd
import time
import ccxt
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# Configuración de la página web estilo app financiera
st.set_page_config(page_title="Mi Mini-eToro Multi-Divisa", page_icon="💱", layout="centered")

# Refresco automático cada 3 segundos en vivo
st_autorefresh(interval=3000, limit=None, key="bot_autorefresh_counter")

st.title("💱 Mi Mini-eToro (OKX & Yahoo | USD / EUR)")

# --- INICIALIZAR CARTERA VIRTUAL EN MEMORIA ---
if 'efectivo' not in st.session_state:
    st.session_state.efectivo = 10000.0
    st.session_state.unidades = 0.0
    st.session_state.precio_compra = 0.0
    st.session_state.en_posicion = False
    st.session_state.historial = []

# --- BARRA LATERAL (CONFIGURACIÓN Y DIVISA) ---
st.sidebar.header("⚙️ Configuración")
moneda_sel = st.sidebar.selectbox("Moneda de Visualización", ["USD ($)", "EUR (€)"])
fuente_datos = st.sidebar.selectbox("Fuente de Datos", ["OKX (Cripto)", "Yahoo Finance (Acciones/Crypto)"])

if fuente_datos == "OKX (Cripto)":
    ticker = st.sidebar.selectbox("Par OKX", ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"])
else:
    # Incluye Tesla (TSLA) y Apple, además de criptos
    ticker = st.sidebar.selectbox("Activo Yahoo", ["TSLA", "AAPL", "BTC-USD", "ETH-USD"])

modo_operacion = st.sidebar.radio("Modo de Operación", ["🤖 Bot Automático", "👤 Manual (Tú decides)"])

stop_loss_pct = st.sidebar.slider("Stop-Loss (%)", 0.1, 5.0, 1.0) / 100.0
take_profit_pct = st.sidebar.slider("Take-Profit (%)", 0.1, 5.0, 1.5) / 100.0

if st.sidebar.button("🔄 Reiniciar Cuenta a 10,000"):
    st.session_state.efectivo = 10000.0
    st.session_state.unidades = 0.0
    st.session_state.precio_compra = 0.0
    st.session_state.en_posicion = False
    st.session_state.historial = []
    st.rerun()

# --- OBTENER TIPO DE CAMBIO EUR/USD ---
def obtener_tipo_cambio():
    try:
        rate_df = yf.Ticker("EURUSD=X").history(period="1d")
        if not rate_df.empty:
            return float(rate_df['Close'].iloc[-1]) # Cuántos dólares vale 1 euro
    except:
        pass
    return 1.08 # Valor aproximado por defecto si falla

tasa_eur_usd = obtener_tipo_cambio()
simbolo_moneda = "$" if moneda_sel == "USD ($)" else "€"

def convertir(valor_en_usd):
    if moneda_sel == "EUR (€)":
        return valor_en_usd / tasa_eur_usd
    return valor_en_usd

# --- FUNCIONES DE OBTENCIÓN DE PRECIO ---
def obtener_precio_en_vivo(fuente, simbolo):
    try:
        if fuente == "OKX (Cripto)":
            exchange = ccxt.okx()
            ticker_info = exchange.fetch_ticker(simbolo)
            precio = float(ticker_info['last'])
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
        st.sidebar.error(f"Error: {e}")
    return None, pd.DataFrame()

precio_actual_usd, datos_df = obtener_precio_en_vivo(fuente_datos, ticker)

if precio_actual_usd is not None:
    # Todo el motor interno opera en USD para mantener consistencia matemática
    valor_en_activo_usd = st.session_state.unidades * precio_actual_usd
    patrimonio_total_usd = st.session_state.efectivo + valor_en_activo_usd

    # --- LÓGICA DE AUTOMATIZACIÓN O RIESGO ---
    if modo_operacion == "🤖 Bot Automático":
        if not st.session_state.en_posicion and st.session_state.efectivo > 0:
            st.session_state.unidades = st.session_state.efectivo / precio_actual_usd
            st.session_state.precio_compra = precio_actual_usd
            st.session_state.efectivo = 0.0
            st.session_state.en_posicion = True
            st.session_state.historial.insert(0, {
                "Hora": time.strftime('%H:%M:%S'), "Tipo": "🤖 COMPRA BOT",
                "Precio": f"{convertir(precio_actual_usd):,.2f} {simbolo_moneda}", "Detalle": f"Entrada en {ticker}"
            })
        elif st.session_state.en_posicion:
            cambio = (precio_actual_usd - st.session_state.precio_compra) / st.session_state.precio_compra
            if cambio <= -stop_loss_pct or cambio >= take_profit_pct:
                nuevo_efectivo_usd = st.session_state.unidades * precio_actual_usd
                resultado_usd = nuevo_efectivo_usd - (st.session_state.unidades * st.session_state.precio_compra)
                tipo = "🔴 STOP-LOSS" if cambio <= -stop_loss_pct else "🔵 TAKE-PROFIT"
                
                st.session_state.efectivo = nuevo_efectivo_usd
                st.session_state.unidades = 0.0
                st.session_state.en_posicion = False
                st.session_state.historial.insert(0, {
                    "Hora": time.strftime('%H:%M:%S'), "Tipo": tipo,
                    "Precio": f"{convertir(precio_actual_usd):,.2f} {simbolo_moneda}", 
                    "Detalle": f"Resultado: {convertir(resultado_usd):+,.2f} {simbolo_moneda} ({cambio*100:+.2f}%)"
                })

    # --- CONVERTIR VALORES PARA MOSTRAR EN PANTALLA ---
    patrimonio_display = convertir(patrimonio_total_usd)
    efectivo_display = convertir(st.session_state.efectivo)
    precio_display = convertir(precio_actual_usd)
    delta_display = convertir(patrimonio_total_usd - 10000.0)

    # --- MÉTRICAS PRINCIPALES ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Patrimonio Total", f"{patrimonio_display:,.2f} {simbolo_moneda}", f"{delta_display:+,.2f} {simbolo_moneda}")
    col2.metric("Efectivo Libre", f"{efectivo_display:,.2f} {simbolo_moneda}")
    col3.metric(f"Precio ({ticker})", f"{precio_display:,.2f} {simbolo_moneda}")

    st.markdown("---")

    # --- PANEL MANUAL ---
    if modo_operacion == "👤 Manual (Tú decides)":
        st.subheader("🎯 Panel de Compra / Venta")
        c_btn1, c_btn2 = st.columns(2)
        
        with c_btn1:
            if not st.session_state.en_posicion:
                if st.button("🟢 COMPRAR AHORA", use_container_width=True, type="primary"):
                    if st.session_state.efectivo > 0:
                        st.session_state.unidades = st.session_state.efectivo / precio_actual_usd
                        st.session_state.precio_compra = precio_actual_usd
                        st.session_state.efectivo = 0.0
                        st.session_state.en_posicion = True
                        st.session_state.historial.insert(0, {
                            "Hora": time.strftime('%H:%M:%S'), "Tipo": "🟢 COMPRA MANUAL",
                            "Precio": f"{precio_display:,.2f} {simbolo_moneda}", "Detalle": f"Comprado {ticker}"
                        })
                        st.rerun()
            else:
                st.info("Ya tienes una posición abierta.")

        with c_btn2:
            if st.session_state.en_posicion:
                if st.button("🔴 VENDER Y COBRAR", use_container_width=True, type="secondary"):
                    nuevo_efectivo_usd = st.session_state.unidades * precio_actual_usd
                    resultado_usd = nuevo_efectivo_usd - (st.session_state.unidades * st.session_state.precio_compra)
                    st.session_state.efectivo = nuevo_efectivo_usd
                    st.session_state.unidades = 0.0
                    st.session_state.en_posicion = False
                    st.session_state.historial.insert(0, {
                        "Hora": time.strftime('%H:%M:%S'), "Tipo": "👤 VENTA MANUAL",
                        "Precio": f"{precio_display:,.2f} {simbolo_moneda}", 
                        "Detalle": f"Cierre | Resultado: {convertir(resultado_usd):+,.2f} {simbolo_moneda}"
                    })
                    st.rerun()
            else:
                st.warning("No hay posiciones abiertas.")
        st.markdown("---")

    # --- GRÁFICO ---
    st.subheader("📊 Gráfico de Cotización en Directo")
    if not datos_df.empty:
        # Opcional: mostrar precios del gráfico en la moneda seleccionada
        df_chart = datos_df.copy()
        if moneda_sel == "EUR (€)":
            df_chart['Close'] = df_chart['Close'] / tasa_eur_usd
        st.line_chart(df_chart['Close'])

    # --- HISTORIAL ---
    st.subheader("📜 Registro de Operaciones")
    if len(st.session_state.historial) > 0:
        st.dataframe(pd.DataFrame(st.session_state.historial), use_container_width=True)
    else:
        st.info("Esperando operaciones...")

else:
    st.error("Conectando con el mercado...")
