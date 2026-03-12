
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="BI Comercial", layout="wide")

st.title("📊 BI Comercial Inteligente")
st.write("Sube tu archivo Excel de ventas para analizar clientes, productos y evolución del negocio.")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx","xls"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    required_cols = ['Fecha','Cliente','Producto','Cantidad','Facturacion']
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Faltan columnas necesarias: {missing}")
        st.stop()

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Año'] = df['Fecha'].dt.year
    df['Mes'] = df['Fecha'].dt.month
    df['Periodo'] = df['Fecha'].dt.to_period('M').astype(str)

    st.sidebar.header("Filtros")

    years = sorted(df['Año'].unique())
    selected_years = st.sidebar.multiselect("Años", years, default=years)

    clientes = sorted(df['Cliente'].unique())
    selected_clientes = st.sidebar.multiselect("Clientes", clientes, default=clientes)

    df = df[df['Año'].isin(selected_years)]
    df = df[df['Cliente'].isin(selected_clientes)]

    total_fact = df['Facturacion'].sum()
    total_clientes = df['Cliente'].nunique()
    total_productos = df['Producto'].nunique()
    total_unidades = df['Cantidad'].sum()

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Facturación", f"€ {total_fact:,.0f}")
    col2.metric("Clientes activos", total_clientes)
    col3.metric("Productos vendidos", total_productos)
    col4.metric("Unidades vendidas", f"{total_unidades:,.0f}")

    st.header("👥 Análisis de Clientes")

    cliente_fact = df.groupby('Cliente').agg(
        facturacion=('Facturacion','sum'),
        unidades=('Cantidad','sum'),
        productos=('Producto','nunique')
    ).reset_index()

    cliente_fact = cliente_fact.sort_values('facturacion', ascending=False)

    total = cliente_fact['facturacion'].sum()
    cliente_fact['% facturacion'] = cliente_fact['facturacion'] / total * 100
    cliente_fact['acumulado'] = cliente_fact['facturacion'].cumsum() / total

    def clasif(x):
        if x <= 0.8:
            return 'A'
        elif x <= 0.95:
            return 'B'
        else:
            return 'C'

    cliente_fact['ABC'] = cliente_fact['acumulado'].apply(clasif)

    c1,c2 = st.columns(2)

    with c1:
        st.dataframe(cliente_fact)

    with c2:
        fig = px.bar(cliente_fact.head(15), x='Cliente', y='facturacion', title="Top clientes")
        st.plotly_chart(fig, use_container_width=True)

    st.header("⚠️ Clientes en riesgo")

    mensual = df.groupby(['Cliente','Periodo'])['Facturacion'].sum().reset_index()
    pivot = mensual.pivot(index='Cliente', columns='Periodo', values='Facturacion').fillna(0)

    if pivot.shape[1] >= 2:

        pivot['ultimo'] = pivot.iloc[:,-1]
        pivot['anterior'] = pivot.iloc[:,-2]

        pivot['variacion_%'] = (pivot['ultimo'] - pivot['anterior']) / pivot['anterior'].replace(0,np.nan) * 100

        riesgo = pivot.sort_values('variacion_%')
        st.dataframe(riesgo[['ultimo','anterior','variacion_%']].head(20))

    st.header("📦 Análisis de Productos")

    prod = df.groupby('Producto').agg(
        unidades=('Cantidad','sum'),
        facturacion=('Facturacion','sum'),
        clientes=('Cliente','nunique')
    ).reset_index()

    prod = prod.sort_values('unidades', ascending=False)

    c3,c4 = st.columns(2)

    with c3:
        st.dataframe(prod)

    with c4:
        fig2 = px.bar(prod.head(15), x='Producto', y='unidades', title="Productos más vendidos")
        st.plotly_chart(fig2, use_container_width=True)

    st.header("📈 Evolución de ventas")

    ventas_mes = df.groupby('Periodo')['Facturacion'].sum().reset_index()

    fig3 = px.line(ventas_mes, x='Periodo', y='Facturacion', markers=True)
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("Sube un archivo Excel para comenzar.")
