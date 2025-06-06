
import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
from PIL import Image

def parse_dta_content(lines):
    header = {}
    tests = []
    current_test_name = None
    in_header = False
    in_body = False
    for line in lines:
        line = line.strip()
        if line == "<HEADER>":
            in_header = True
            continue
        elif line == "<\HEADER>":
            in_header = False
            continue
        elif line == "<BODY>":
            in_body = True
            continue
        elif line == "<\BODY>":
            in_body = False
            continue
        if in_header and "=" in line:
            key, value = line.split("=", 1)
            header[key] = value
        elif in_body:
            if line.startswith("<TEST="):
                current_test_name = line.replace("<TEST=", "").replace(">", "")
            elif line.startswith("<\TEST>"):
                current_test_name = None
            elif current_test_name:
                parts = line.split(",")
                tests.append({
                    "TEST_NAME": current_test_name,
                    "VAL1": parts[0] if len(parts) > 0 else None,
                    "VAL2": parts[1] if len(parts) > 1 else None,
                    "VAL3": parts[2] if len(parts) > 2 else None,
                    "VAL4": parts[3] if len(parts) > 3 else None
                })
    return header, pd.DataFrame(tests)

class ReportPDF(FPDF):
    def header(self):
        if logo_bytes:
            self.image(logo_bytes, x=10, y=10, w=40)
        self.set_font("Arial", "B", 16)
        self.set_xy(60, 15)
        self.cell(0, 10, "INFORME DE SEGURIDAD ELÉCTRICA", ln=True, align="L")
        self.set_font("Arial", "", 10)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

    def section_title(self, title):
        self.set_font("Arial", "B", 11)
        self.set_fill_color(220, 220, 220)
        self.cell(0, 8, title, ln=True, fill=True)

    def field(self, label, value):
        self.set_font("Arial", "B", 10)
        self.cell(50, 8, f"{label}:", border=1)
        self.set_font("Arial", "", 10)
        self.cell(0, 8, value, border=1, ln=True)

    def build_header_section(self, header):
        self.section_title("INFORMACIÓN GENERAL")
        for label, key in [
            ("Fecha de la prueba", "DATEOFTEST"),
            ("Hora de la prueba", "TIMEOFTEST"),
            ("Operador", "ESA615OPID"),
            ("Equipo probado", "DUTEQUIPNUM"),
            ("Duración (segundos)", "TESTDURATION"),
            ("Norma aplicada", "STANDARD"),
            ("Clasificación", "CLASSIFICATION"),
            ("Voltaje de aislamiento", "INSVOLTAGE"),
            ("Polaridad inversa", "REVERSEPOL"),
        ]:
            self.field(label, header.get(key, "-"))
        self.ln(5)

    def build_results_table(self, df):
        self.section_title("RESULTADOS DE PRUEBA")
        self.set_font("Arial", "B", 10)
        self.set_fill_color(200, 200, 200)
        self.cell(60, 8, "Nombre de prueba", border=1, fill=True)
        self.cell(25, 8, "Valor 1", border=1, fill=True)
        self.cell(25, 8, "Valor 2", border=1, fill=True)
        self.cell(35, 8, "Valor 3", border=1, fill=True)
        self.cell(20, 8, "Resultado", border=1, ln=True, fill=True)
        self.set_font("Arial", "", 9)
        for _, row in df.iterrows():
            self.cell(60, 8, row["TEST_NAME"], border=1)
            self.cell(25, 8, str(row["VAL1"]), border=1)
            self.cell(25, 8, str(row["VAL2"]), border=1)
            self.cell(35, 8, str(row["VAL3"]), border=1)
            self.cell(20, 8, str(row["VAL4"]), border=1, ln=True)

    def add_observations_and_signature(self, observaciones, conclusion, equipo_utilizado):
        self.ln(8)
        self.section_title("OBSERVACIONES / COMENTARIOS")
        self.set_font("Arial", "", 10)
        self.multi_cell(0, 8, observaciones)
        self.ln(5)
        self.section_title("EQUIPO UTILIZADO")
        
        self.cell(70, 8, equipo_utilizado, ln=True)
        self.ln(5)
        self.section_title("CONCLUSIÓN DE LA PRUEBA")
        self.set_font("Arial", "B", 12)
        self.set_text_color(0, 128, 0)
        
        self.set_font("Arial", "B", 12)
        if conclusion == "APROBADO":
            self.set_text_color(0, 128, 0)
        else:
            self.set_text_color(200, 0, 0)
        self.cell(0, 10, f"TEST: {conclusion}", ln=True)
        self.set_text_color(0, 0, 0)
    
        self.set_text_color(0, 0, 0)
        self.ln(5)
        self.section_title("FIRMA DEL TÉCNICO RESPONSABLE")
        self.ln(25)
        self.set_x(120)  # mueve el inicio del campo hacia la derecha
        self.line(self.get_x(), self.get_y(), self.get_x() + 70, self.get_y())
        self.ln(5)
        self.set_x(120)
        self.cell(60, 8, "Firma técnico responsable", ln=True, align="R")


st.title("Generador de Informes de seguridad eléctrica")
dta_file = st.file_uploader("Subí el archivo .DTA del Fluke ESA615", type=["dta"])
logo_file = st.file_uploader("Subí el logo de tu empresa (PNG o JPG)", type=["png", "jpg", "jpeg"])

if dta_file and logo_file:
    logo_image = Image.open(logo_file).convert("RGB")
    logo_bytes = "logo_temp.png"
    logo_image.save(logo_bytes)

    lines = dta_file.read().decode("utf-8").splitlines()
    header_data, df_tests = parse_dta_content(lines)

    pdf = ReportPDF()
    pdf.add_page()
    pdf.build_header_section(header_data)
    pdf.build_results_table(df_tests)
    
    # Sección editable de observaciones
    observaciones = st.text_area("Observaciones / Comentarios", value="Ninguna observación relevante durante la ejecución de la prueba. El equipo se encontraba en condiciones estables durante todo el procedimiento.", height=100)
        
    equipo_utilizado = st.text_input("Equipo utilizado", value="Analizador de seguridad eléctrica FLUKE ESA615")
    resultado_opciones = ["APROBADO", "RECHAZADO"]
    conclusion = st.selectbox("Resultado final de la prueba", options=resultado_opciones, index=0)
    pdf.add_observations_and_signature(observaciones, conclusion, equipo_utilizado)
    
    
    

    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))

    nombre_equipo = header_data.get("DUTEQUIPNUM", "equipo")
    nombre_archivo = f"Informe {nombre_equipo}.pdf"

    st.download_button(
        "Descargar informe PDF",
        data=pdf_output.getvalue(),
        file_name=nombre_archivo
)

