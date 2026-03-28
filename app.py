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
st.markdown("### 💼 Cotizador técnico + financiero")

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
prof = st.sidebar.number_input("Profundidad (m)", value=0.5)
dias = st.sidebar.slider("Días calentamiento",1,7,3)

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

# ---------------- FACTORES ----------------
factor = 1
if tipo == "Exterior":
    factor *= 1.3
if manta == "Sí":
    factor *= 0.6

# ---------------- CALCULOS ----------------
rad = ciudades[ciudad]["rad"]
vol = area * prof
delta = temp_fin - temp_ini

energia_total = (vol * 1000 * delta) / 860
energia_dia = (energia_total / dias) * factor

def sistema(area_c, eff, precio):
    prod = rad * area_c * eff
    n = energia_dia / prod
    inv = n * precio

    ahorro_kwh = energia_dia * 365 * costo_kwh
    ahorro_gas = energia_dia * 365 * 0.1 * costo_gas

    flujo = [-inv] + [ahorro_kwh]*10
    tir = npf.irr(flujo)
    if tir is None or np.isnan(tir):
        tir = 0

    roi_elec = inv / ahorro_kwh
    roi_gas = inv / ahorro_gas
    co2 = energia_dia * 365 * 0.2

    venta = inv * (1 + margen/100)

    return n, inv, venta, ahorro_kwh, roi_elec, roi_gas, tir, co2

placa = sistema(2,0.5,precio_placa)
heat = sistema(3,0.65,precio_heat)
pp = sistema(3.7,0.75,precio_pp)
mariposa = sistema(4.8,0.7,precio_mariposa)

df = pd.DataFrame({
    "Sistema":["Placa","Heat Pipe","Polipropileno","Mariposa"],

    "Colectores":[
        round(placa[0],1),
        round(heat[0],1),
        round(pp[0],1),
        round(mariposa[0],1)
    ],

    "Inversión":[placa[1],heat[1],pp[1],mariposa[1]],
    "Venta":[placa[2],heat[2],pp[2],mariposa[2]],

    "ROI eléctrico":[placa[4],heat[4],pp[4],mariposa[4]],
    "ROI gas":[placa[5],heat[5],pp[5],mariposa[5]],

    "TIR %":[placa[6]*100,heat[6]*100,pp[6]*100,mariposa[6]*100],

    "CO2":[placa[7],heat[7],pp[7],mariposa[7]]
}).sort_values("ROI eléctrico")

st.markdown("## 📦 Dimensionamiento del sistema")

for i in df.index:
    fila = df.loc[i]
    st.write(f"🔹 {fila['Sistema']}: {fila['Colectores']} colectores")

# ---------------- KPIs ----------------
st.markdown("## 📊 Indicadores clave")

c1, c2, c3 = st.columns(3)
c1.metric("Energía diaria", f"{round(energia_dia,1)} kWh")
c2.metric("Volumen", f"{round(vol,1)} m³")
c3.metric("CO2 evitado", f"{round(energia_dia*365*0.2)} kg/año")

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

# ---------------- AHORRO ----------------
st.markdown("### 💰 Ahorro acumulado")

años = list(range(1,11))
ahorro = [placa[3]*i for i in años]
st.line_chart(pd.DataFrame({"Año":años,"Ahorro":ahorro}).set_index("Año"))

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

    doc.build(content)

    return "propuesta.pdf"   # ✅ AQUÍ SÍ

if st.button("📄 Generar PDF"):
    archivo = generar_pdf()

    with open(archivo, "rb") as f:
        st.download_button("⬇️ Descargar PDF", f, file_name=archivo)
