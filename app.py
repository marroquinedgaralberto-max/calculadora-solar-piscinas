import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(layout="wide")

# ---------------- HEADER ----------------
st.markdown("# 🔥 Calculadora Solar Piscinas PRO")
st.markdown("### 💼 Modelo técnico real (ingeniería)")

# ---------------- CLIENTE ----------------
st.sidebar.header("📋 Cliente")
cliente = st.sidebar.text_input("Nombre cliente")
proyecto = st.sidebar.text_input("Proyecto")

# ---------------- CIUDADES ----------------
ciudades = {
    "Bogotá": {"rad":4.5, "temp":15},
    "Tunja": {"rad":4.3, "temp":14},
    "Pasto": {"rad":4.2, "temp":16},
    "Manizales": {"rad":4.5, "temp":20},
    "Armenia": {"rad":4.7, "temp":23},
    "Pereira": {"rad":4.6, "temp":23},
    "Medellín": {"rad":4.8, "temp":24},
    "Cali": {"rad":5.0, "temp":26},
    "Bucaramanga": {"rad":5.2, "temp":24}
}

# ---------------- INPUTS ----------------
st.sidebar.header("⚙️ Parámetros")

ciudad = st.sidebar.selectbox("Ciudad", list(ciudades.keys()))
temp_ini = st.sidebar.number_input("Temp inicial", value=float(ciudades[ciudad]["temp"]))
temp_fin = st.sidebar.number_input("Temp objetivo", value=30.0)

area = st.sidebar.number_input("Área piscina (m²)", value=36.0)
prof = st.sidebar.number_input("Profundidad (m)", value=1.5)

tipo = st.sidebar.selectbox("Piscina", ["Exterior","Cubierta"])
manta = st.sidebar.selectbox("Manta térmica", ["No","Sí"])

costo_kwh = st.sidebar.number_input("Costo kWh", value=800.0)
costo_gas = st.sidebar.number_input("Costo gas", value=2500.0)
margen = st.sidebar.slider("Margen (%)",10,100,30)

# ---------------- PRECIOS ----------------
st.sidebar.header("💰 Equipos")

precio_placa = st.sidebar.number_input("Placa plana", value=1200000.0)
precio_heat = st.sidebar.number_input("Heat pipe", value=2200000.0)
precio_pp = st.sidebar.number_input("Polipropileno", value=600000.0)
precio_mariposa = st.sidebar.number_input("Mariposa", value=2500000.0)

# ---------------- MODELO REAL ----------------

delta = temp_fin - temp_ini

# FACTOR TERMICO
if tipo == "Exterior" and manta == "No":
    factor_termico = 1.2
elif tipo == "Exterior" and manta == "Sí":
    factor_termico = 0.7
else:
    factor_termico = 0.5

energia_dia = area * delta * factor_termico

rad = ciudades[ciudad]["rad"]

# ---------------- FUNCION ----------------
def sistema(area_c, eff, precio):

    factor_real = 0.7

    produccion = rad * area_c * eff * factor_real

    n = energia_dia / produccion

    inv = n * precio
    venta = inv * (1 + margen/100)

    ahorro_kwh = energia_dia * 365 * costo_kwh
    ahorro_gas = energia_dia * 365 * 0.1 * costo_gas

    flujo = [-inv] + [ahorro_kwh]*10
    tir = npf.irr(flujo)
    if tir is None or np.isnan(tir):
        tir = 0

    roi_elec = inv / ahorro_kwh
    roi_gas = inv / ahorro_gas

    co2 = energia_dia * 365 * 0.2

    return n, inv, venta, ahorro_kwh, roi_elec, roi_gas, tir, co2

# ---------------- SISTEMAS ----------------
placa = sistema(1.8, 0.5, precio_placa)
heat = sistema(2.4, 0.65, precio_heat)
pp = sistema(3.8, 0.8, precio_pp)
mariposa = sistema(6.8, 0.7, precio_mariposa)

# ---------------- DATAFRAME ----------------
df = pd.DataFrame({
    "Sistema":["Placa","Heat Pipe","Polipropileno","Mariposa"],
    "Colectores":[placa[0],heat[0],pp[0],mariposa[0]],
    "Inversión":[placa[1],heat[1],pp[1],mariposa[1]],
    "Venta":[placa[2],heat[2],pp[2],mariposa[2]],
    "ROI eléctrico":[placa[4],heat[4],pp[4],mariposa[4]],
    "ROI gas":[placa[5],heat[5],pp[5],mariposa[5]],
    "TIR %":[placa[6]*100,heat[6]*100,pp[6]*100,mariposa[6]*100],
    "CO2":[placa[7],heat[7],pp[7],mariposa[7]]
}).sort_values("ROI eléctrico")

# ---------------- KPIs ----------------
st.markdown("## 📊 Indicadores clave")

c1, c2, c3 = st.columns(3)
c1.metric("Energía diaria", f"{round(energia_dia,1)} kWh")
c2.metric("ΔT", f"{round(delta,1)} °C")
c3.metric("CO2 evitado", f"{round(energia_dia*365*0.2)} kg/año")

# ---------------- DIMENSIONAMIENTO ----------------
st.markdown("## 📦 Dimensionamiento del sistema")

for i in df.index:
    fila = df.loc[i]
    st.write(f"🔹 {fila['Sistema']}: {round(fila['Colectores'],1)} colectores")

# ---------------- TABLA ----------------
st.markdown("## 🏆 Comparación")
st.dataframe(df, use_container_width=True)

# ---------------- GRAFICAS ----------------
st.markdown("## 📈 Análisis")

col1, col2 = st.columns(2)

with col1:
    st.bar_chart(df.set_index("Sistema")["ROI eléctrico"])

with col2:
    st.bar_chart(df.set_index("Sistema")["Inversión"])

# ---------------- RECOMENDACION ----------------
mejor = df.iloc[0]
st.success(f"🔥 Sistema recomendado: {mejor['Sistema']}")

# ---------------- PDF ----------------
def generar_pdf():
    doc = SimpleDocTemplate("propuesta.pdf")
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("PROPUESTA SOLAR", styles["Title"]))
    content.append(Spacer(1,10))

    content.append(Paragraph(f"Cliente: {cliente}", styles["Normal"]))
    content.append(Paragraph(f"Proyecto: {proyecto}", styles["Normal"]))
    content.append(Spacer(1,10))

    content.append(Paragraph(f"Sistema recomendado: {mejor['Sistema']}", styles["Heading2"]))
    content.append(Spacer(1,10))

    tabla = [["Sistema","Colectores","Inversión"]]

    for i in df.index:
        fila = df.loc[i]
        tabla.append([
            fila["Sistema"],
            round(fila["Colectores"],1),
            f"${round(fila['Inversión'],0):,.0f}"
        ])

    t = Table(tabla)
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),1,colors.black)]))

    content.append(t)

    doc.build(content)
    return "propuesta.pdf"

if st.button("📄 Generar PDF"):
    archivo = generar_pdf()
    with open(archivo, "rb") as f:
        st.download_button("Descargar", f, file_name=archivo)
