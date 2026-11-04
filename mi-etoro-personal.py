import streamlit as st
import yfinance as yf
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

# Configuración de la página web estilo app financiera
st.set_page_config(page_title="Mi Mini-eToro", page_icon="📱", layout="centered")

# Refresco automático cada 3 segundos
st_autorefresh(interval=3000, limit=None, key="bot_autorefresh_counter")

st.title("📱 Mi Mini-eToro - Panel de Trading")

# --- INICIALIZAR LA CARTERA VIRTUAL EN MEMORIA ---
if 'efectivo' not in st.session_state:
    st.session_state.efectivo = 10000.0
    st.session_state.unidades = 0.0
    st.session_state.precio_compra = 0.0
    st.session_state.en_posicion = False
    st.session_state.historial = []

# --- BARRA LATERAL (AJUSTES) ---
st.sidebar.header("⚙️ Configuración")
ticker = st.sidebar.selectbox("Activo", ["BTC-USD", "ETH-USD", "AAPL", "TSLA"])
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

# --- FUNCION DE MERCADO ---
def obtener_precio(simbolo):
    try:
        activo = yf.Ticker(simbolo)
        hist = activo.history(period="1d", interval="1m")
        if not hist.empty:
            return float(hist['Close'].iloc[-1]), hist
    except:
        pass
    return None, pd.DataFrame()

precio_actual, datos_df = obtener_precio(ticker)

if precio_actual is not None:
    valor_en_activo = st.session_state.unidades * precio_actual
    patrimonio_total = st.session_state.efectivo + valor_en_activo

    # --- LÓGICA SEGÚN EL MODO ELEGIDO ---
    if modo_operacion == "🤖 Bot Automático":
        if not st.session_state.en_posicion and st.session_state.efectivo > 0:
            # Compra automática
            st.session_state.unidades = st.session_state.efectivo / precio_actual
            st.session_state.precio_compra = precio_actual
            st.session_state.efectivo = 0.0
            st.session_state.en_posicion = True
            st.session_state.historial.insert(0, {
                "Hora": time.strftime('%H:%M:%S'), "Tipo": "🤖 COMPRA BOT",
                "Precio": f"${precio_actual:,.2f}", "Detalle": f"Entrada automática en {ticker}"
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

    # --- MÉTRICAS PRINCIPALES (ESTILO APP BANCARIA) ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Patrimonio Total", f"${patrimonio_total:,.2f}", f"{patrimonio_total - 10000:+,.2f}$")
    col2.metric("Efectivo Libre", f"${st.session_state.efectivo:,.2f}")
    col3.metric(f"Precio {ticker}", f"${precio_actual:,.2f}")

    st.markdown("---")

    # --- PANEL DE ACCIÓN RÁPIDA (SI ESTÁS EN MODO MANUAL) ---
    if modo_operacion == "👤 Manual (Tú decides)":
        st.subheader("🎯 Panel de Compra / Venta Rápida")
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
                            "Precio": f"${precio_actual:,.2f}", "Detalle": f"Compra manual de {ticker}"
                        })
                        st.rerun()
            else:
                st.info("Ya tienes una posición abierta en este activo.")

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
                        "Precio": f"${precio_actual:,.2f}", "Detalle": f"Cierre manual | Resultado: {resultado:+,.2f}$"
                    })
                    st.rerun()
            else:
                st.warning("No tienes posiciones abiertas para vender.")
        st.markdown("---")

    # --- GRÁFICO ---
    st.subheader("📊 Gráfico de Cotización")
    if not datos_df.empty:
        st.line_chart(datos_df['Close'])

    # --- HISTORIAL ---
    st.subheader("📜 Registro de Operaciones")
    if len(st.session_state.historial) > 0:
        st.dataframe(pd.DataFrame(st.session_state.historial), use_container_width=True)
    else:
        st.info("Aún no hay operaciones registradas.")

else:
    st.error("Cargando datos del mercado...")
