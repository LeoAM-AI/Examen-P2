import streamlit as st
import yfinance as yf
import numpy as np
import plotly.graph_objects as go

# Título
st.sidebar.title("📊 Visualizador de Estrategias de Opciones")
st.sidebar.write("Creado por Leonardo Aguilar")

# Inputs del usuario
ticker = st.sidebar.text_input("Ingresa el ticker (ej. AAPL):").upper()

# Obtener fechas de expiración dinámicas
expiration_date = None
if ticker:
    try:
        stock = yf.Ticker(ticker)
        expirations = stock.options
        if expirations:
            expiration_date = st.sidebar.selectbox("Selecciona la fecha de expiración:", expirations)
        else:
            st.sidebar.warning("Este ticker no tiene opciones disponibles.")
    except Exception as e:
        st.sidebar.error(f"Error al obtener datos del ticker: {e}")
        expirations = []

# Resto de inputs
estrategia = st.sidebar.selectbox("Selecciona una estrategia:", ["", "Long Call", "Long Put", "Short Call", "Short Put"])
strike_price = st.sidebar.number_input("Strike Price ($):", min_value=0.0, step=0.5)

# Solo intentamos obtener la prima si todo está completo
prima = None
if ticker and expiration_date and strike_price > 0 and estrategia:
    opt_chain = stock.option_chain(expiration_date)
    if estrategia in ["Long Call", "Short Call"]:
        options = opt_chain.calls
    else:
        options = opt_chain.puts

    # Buscar la prima correspondiente
    match = options[options['strike'] == strike_price]
    if not match.empty:
        prima = float(match['lastPrice'].iloc[0])
    else:
        prima = 0
        st.sidebar.warning("No se encontró la prima para ese strike.")

# Continuar si todo está listo
if ticker and estrategia and expiration_date and strike_price > 0 and prima is not None:
    hist = stock.history(period="1d")
    if hist.empty:
        st.error("No se pudo obtener el precio del activo.")
    else:
        spot_price = float(hist['Close'][-1])
        prices = np.linspace(spot_price * 0.5, spot_price * 1.8, 100)

        # Calcular Payoff
        if estrategia == "Long Call":
            payoff = np.maximum(prices - strike_price, 0) - prima
            net_credit = f"Net Debit: ${prima:.2f}"
            max_profit = "Ilimitado"
            max_loss = f"${prima:.2f}"
        elif estrategia == "Long Put":
            payoff = np.maximum(strike_price - prices, 0) - prima
            net_credit = f"Net Debit: ${prima:.2f}"
            max_profit = f"${strike_price - prima:.2f}"
            max_loss = f"${prima:.2f}"
        elif estrategia == "Short Call":
            payoff = -np.maximum(prices - strike_price, 0) + prima
            net_credit = f"Net Credit: ${prima:.2f}"
            max_profit = f"${prima:.2f}"
            max_loss = "Ilimitado"
        elif estrategia == "Short Put":
            payoff = -np.maximum(strike_price - prices, 0) + prima
            net_credit = f"Net Credit: ${prima:.2f}"
            max_profit = f"${prima:.2f}"
            max_loss = f"${strike_price - prima:.2f}"

        # Mostrar resumen
        st.title("📈 Resumen de la Estrategia Seleccionada")
        st.table({
            "Ticker": [ticker],
            "Precio Actual": [f"${spot_price:.2f}"],
            "Expiración": [expiration_date],
            "Strike": [strike_price],
            "Prima (último)": [f"${prima:.2f}"],
            "Net Debit / Credit": [net_credit],
            "Max Profit": [max_profit],
            "Max Loss": [max_loss]
        })

        # Mostrar gráfico
        st.header("Visualización de la Estrategia")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=prices, y=payoff, mode='lines', name='Payoff (Ganancia / Pérdida)', line=dict(color='blue')))
        fig.add_vline(x=strike_price, line=dict(color='red', dash='dash'), annotation_text='Strike Price', annotation_position="top right")
        fig.add_vline(x=spot_price, line=dict(color='orange', dash='dot'), annotation_text='Spot Price',  annotation_position="top left")
        fig.update_layout(
            title=f'Payoff: {estrategia}',
            xaxis_title='Precio del Subyacente al Vencimiento',
            yaxis_title='Ganancia / Pérdida  ($)',
            template='plotly_white',
            legend=dict(x=0.02, y=0.98)
        )
        st.plotly_chart(fig)
        

else:
    st.warning("Completa todos los campos (ticker, expiración, estrategia, strike) para continuar.")

