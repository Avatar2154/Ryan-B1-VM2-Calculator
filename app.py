import streamlit as st
import numpy as np
import streamlit.components.v1 as components
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _build_pdf_report(input_rows, output_rows):
    """Create a simple multi-page PDF report for download."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    left_margin = 40
    line_height = 16
    y = page_height - 48

    def _new_page():
        nonlocal y
        pdf.showPage()
        y = page_height - 48

    def _line(text, bold=False):
        nonlocal y
        if y < 48:
            _new_page()
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
        pdf.drawString(left_margin, y, text)
        y -= line_height

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _line("NZBC B1/VM2 Bearing Capacity Report", bold=True)
    _line(f"Generated: {timestamp}")
    y -= 6

    _line("Inputs", bold=True)
    for label, value in input_rows:
        _line(f"- {label}: {value}")

    y -= 6
    _line("Bearing Capacity Check Outputs", bold=True)
    for label, value in output_rows:
        _line(f"- {label}: {value}")

    pdf.save()
    return buffer.getvalue()


def _build_printable_html_report(input_rows, output_rows):
    """Create a print-friendly HTML report for browser printing."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    input_items = "".join([f"<tr><td>{label}</td><td>{value}</td></tr>" for label, value in input_rows])
    output_items = "".join([f"<tr><td>{label}</td><td>{value}</td></tr>" for label, value in output_rows])

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>B1/VM2 Bearing Capacity Report</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      color: #1f2937;
      margin: 24px;
      line-height: 1.4;
    }}
    h1 {{
      font-size: 22px;
      margin: 0 0 8px 0;
    }}
    h2 {{
      font-size: 16px;
      margin: 22px 0 8px 0;
      border-bottom: 1px solid #d1d5db;
      padding-bottom: 4px;
    }}
    p.meta {{
      margin: 0;
      color: #4b5563;
      font-size: 13px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
      font-size: 13px;
    }}
    td {{
      border: 1px solid #e5e7eb;
      padding: 8px;
      vertical-align: top;
    }}
    td:first-child {{
      width: 46%;
      font-weight: 600;
      background: #f9fafb;
    }}
    .actions {{
      margin-top: 18px;
      display: flex;
      gap: 10px;
    }}
    button {{
      border: 1px solid #9ca3af;
      background: #ffffff;
      border-radius: 6px;
      padding: 8px 12px;
      cursor: pointer;
    }}
    @media print {{
      .actions {{
        display: none;
      }}
      body {{
        margin: 12mm;
      }}
    }}
  </style>
</head>
<body>
  <h1>NZBC B1/VM2 Bearing Capacity Report</h1>
  <p class="meta">Generated: {timestamp}</p>
  <p class="meta">Prepared from current Streamlit inputs and computed outputs.</p>

  <h2>Inputs</h2>
  <table>
    <tbody>
      {input_items}
    </tbody>
  </table>

  <h2>Bearing Capacity Check Outputs</h2>
  <table>
    <tbody>
      {output_items}
    </tbody>
  </table>

  <div class="actions">
    <button onclick="window.print()">Print / Save as PDF</button>
  </div>
</body>
</html>"""

st.set_page_config(page_title="NZBC B1/VM2 Advanced Foundation Tool", page_icon="🇳🇿", layout="wide")

st.title("🇳🇿 Professional B1/VM2 Bearing Capacity Calculator")
# Property warning notice subtitle
st.markdown("⚠️ *This app is the property of Ryan. No unauthorised use accepted.*")

st.markdown("""
Adheres to the **New Zealand Building Code Verification Method B1/VM2**. 
Automates effective area eccentricities, load orientations, and short/long-term soil behaviors.
""")

# --- Side-by-Side Configuration Columns ---
col_case, col_geom, col_loads = st.columns(3)

with col_case:
    st.header("⏳ 1. Design Case & Soil")
    design_case = st.selectbox(
        "Design Load Case", 
        ["Static (Long-Term / Drained)", "Seismic / Short-Term (Undrained)"],
        help="Seismic and short-term cases use undrained analysis (Su). Static cases use drained parameters (c', phi')."
    )
    
    st.markdown("---")
    if design_case == "Seismic / Short-Term (Undrained)":
        st.subheader("💧 Cohesive Soil Properties")
        Su = st.number_input("Undrained Shear Strength, Su (kPa)", min_value=1.0, value=50.0, step=5.0)
        c_calc = Su
        phi_deg = 0.0
        st.caption("🔒 System locked to Undrained State (ϕ = 0° as per B1/VM2 guidelines).")
    else:
        st.subheader("🪨 Drained Soil Properties")
        c_calc = st.number_input("Effective Cohesion, c' (kPa)", min_value=0.0, value=5.0, step=1.0)
        phi_deg = st.slider("Effective Internal Friction Angle, ϕ' (degrees)", min_value=0, max_value=45, value=30, step=1)
    
    gamma = st.number_input("Soil Total Unit Weight, γ (kN/m³)", min_value=10.0, value=18.0, step=0.5)

with col_geom:
    st.header("📐 2. Footing Dimensions")
    footing_type = st.selectbox("Footing Shape Configuration", ["Rectangular Pad", "Continuous Strip"])
    B_raw = st.number_input("Gross Footing Width, B (m)", min_value=0.1, value=1.5, step=0.1)
    
    if footing_type == "Rectangular Pad":
        L_raw = st.number_input("Gross Footing Length, L (m)", min_value=0.1, value=2.0, step=0.1)
    else:
        L_raw = 100000.0  # Strip footing approximation
        
    Df = st.number_input("Foundation Embedment Depth, Df (m)", min_value=0.0, value=0.6, step=0.1)
    
    st.markdown("---")
    st.subheader("🏗️ Foundation Material")
    gamma_concrete = st.number_input("Unit Weight of Concrete, γ_c (kN/m³)", min_value=20.0, value=24.0, step=0.5)
    
    st.markdown("---")
    st.subheader("⚖️ Load Factor (Foundation Self-Weight Only)")
    with st.expander("ℹ️ Show Load Factor Guidance (NZS 1170.0)"):
        st.info(
            "This load factor applies **ONLY to the self-weight of the foundation**, not the structural loads.\n\n"
            "- **1.35**: Use if Permanent Action Only case (E_d = 1.35G) is critical\n"
            "- **1.2**: Use if Permanent + Imposed case (E_d = 1.2G + 1.5Q) is critical\n\n"
            "⚠️ **Confirm with your structural engineer which load case is critical for your project.**\n"
            "The structural engineer will provide factored vertical loads already adjusted for their critical case."
        )
    load_factor = st.number_input("Load Factor for Foundation Self-Weight (γ_f)", min_value=1.0, value=1.35, step=0.05)
    
    st.markdown("---")
    st.subheader("💧 Groundwater Table")
    gw_active = st.checkbox("Enable Groundwater Table", value=False)
    if gw_active:
        dw = st.number_input("Water Depth from Ground Surface (m)", min_value=0.0, value=0.4, step=0.1)
        gamma_w = 9.81
    else:
        dw = 999.0
        gamma_w = 0.0

with col_loads:
    st.header("🏋️ 3. Design Actions (ULS)")
    
    st.subheader("📥 Vertical Loads (from Structural Engineer)")
    V_unfactored = st.number_input("Unfactored Vertical Load, V (kN)", min_value=0.0, value=300.0, step=10.0, help="Unfactored structural load (typically 0.9G)")
    V_factored = st.number_input("Factored Vertical Load, V* (kN)", min_value=0.0, value=400.0, step=10.0, help="Factored design load (already factored by structural engineer)")
    
    st.markdown("**Bending Moments (Factored - from Structural Engineer):**")
    M_B_factored = st.number_input("Factored Moment about B-axis, M_B* (kN·m)", min_value=0.0, value=15.0, step=5.0, help="Factored moment at footing base")
    if footing_type == "Rectangular Pad":
        M_L_factored = st.number_input("Factored Moment about L-axis, M_L* (kN·m)", min_value=0.0, value=10.0, step=5.0, help="Factored moment at footing base")
    else:
        M_L_factored = 0.0

    st.markdown("**Lateral Loading - Parallel to Width (B):**")
    H_unfactored_B = st.number_input("Unfactored Horizontal Load (B-direction), H (kN)", min_value=0.0, value=20.0, step=5.0, help="Unfactored horizontal load parallel to width")
    H_factored_B = st.number_input("Factored Horizontal Load (B-direction), H* (kN)", min_value=0.0, value=35.0, step=5.0, help="Factored design horizontal load parallel to width")
    
    st.markdown("**Lateral Loading - Parallel to Length (L):**")
    H_unfactored_L = st.number_input("Unfactored Horizontal Load (L-direction), H (kN)", min_value=0.0, value=0.0, step=5.0, help="Unfactored horizontal load parallel to length")
    H_factored_L = st.number_input("Factored Horizontal Load (L-direction), H* (kN)", min_value=0.0, value=0.0, step=5.0, help="Factored design horizontal load parallel to length")
    
    phi_g = st.slider("Geotechnical Reduction Factor (𝜙_g)", min_value=0.40, max_value=0.90, value=0.50, step=0.05)

# --- B1/VM2 Computational Core Engine ---

# 1. Calculate foundation self-weight
footing_area = B_raw * L_raw
V_foundation_unfactored = footing_area * Df * gamma_concrete
V_foundation_factored = V_foundation_unfactored * load_factor

# 2. Calculate total vertical loads
# For eccentricity: use 0.9 × unfactored loads
V_eccentricity = (0.9 * V_unfactored) + (0.9 * V_foundation_unfactored)
# For bearing capacity check: use factored structural + factored foundation
V_capacity_check = V_factored + V_foundation_factored

# 3. Determine critical horizontal load direction and induced moments
# Check which direction has larger factored horizontal load
if H_factored_B >= H_factored_L:
    H_factored_critical = H_factored_B
    h_direction = "Parallel to Width (B)"
else:
    H_factored_critical = H_factored_L
    h_direction = "Parallel to Length (L)"

# Calculate induced moments from factored horizontal forces
M_B_induced = H_factored_B * Df
M_L_induced = H_factored_L * Df

# Total moments = factored input moments + induced moments from lever arm
M_B_total = M_B_factored + M_B_induced
M_L_total = M_L_factored + M_L_induced

# 4. Deduce Meyerhof Effective Dimensions from Overturning Moments
# Using 0.9 × unfactored loads for eccentricity
e_B = M_B_total / V_eccentricity if V_eccentricity > 0 else 0
e_L = M_L_total / V_eccentricity if V_eccentricity > 0 else 0

B_prime = B_raw - 2 * e_B
L_prime = L_raw - 2 * e_L

# Overturning safety check boundary
if B_prime <= 0 or L_prime <= 0:
    st.error("❌ STRUCTURAL CRITICAL FAILURE: Combined moments cause total eccentricity tension! Footing will overturn. Increase footing size, decrease lateral force, or increase depth.")
    st.stop()

A_prime = B_prime * L_prime
phi_rad = np.radians(phi_deg)


# 5. Advanced Groundwater Surcharge Rules

# Surcharge (q) remains as you had it (correct logic)
if gw_active and dw <= Df:
    q_surcharge = (dw * gamma) + ((Df - dw) * (gamma - gamma_w))
else:
    q_surcharge = Df * gamma

# --- UPDATED γ′ LOGIC (KEY FIX) ---
# Apply 2B influence depth below footing base for third term (γ′)

if gw_active:
    influence_depth = Df + 2.0 * B_prime  # 2B below foundation base
    
    if dw <= Df:
        # Water above base → fully submerged
        gamma_prime = gamma - gamma_w

    elif dw <= influence_depth:
        # Water within 2B → assume full buoyant effect (B1/VM2 conservative simplification)
        gamma_prime = gamma - gamma_w

    else:
        # Water too deep → no reduction
        gamma_prime = gamma
else:
    gamma_prime = gamma

# 6. Classic Vesic Bearing Capacity Factors
if phi_deg == 0:
    Nc = 5.14
    Nq = 1.0
    Ngamma = 0.0
else:
    # CLEAN MATH FIX: Calculated as pure, un-altered Nq standard mathematical constant
    Nq = np.exp(np.pi * np.tan(phi_rad)) * (np.tan(np.pi/4 + phi_rad/2))**2
    Nc = (Nq - 1.0) / np.tan(phi_rad)
    # MODIFIER: Only Ngamma uses the 2 * (Nq - 1) calculation configuration
    Ngamma = 2.0 * (Nq - 1.0) * np.tan(phi_rad)

# 7. Load Inclination Multipliers (with Explicit Direction Exponents)
# Use factored vertical load for capacity calculations
denominator_c = A_prime * c_calc + V_capacity_check * np.tan(phi_rad)

if phi_deg == 0:
    lambda_iq = 1.0
    lambda_igamma = 1.0
    lambda_ic = 1.0 - (H_factored_critical / (5.14 * A_prime * c_calc)) if (A_prime * c_calc) > 0 else 0.0
    exponent_m = 0.0
else:
    if h_direction == "Parallel to Width (B)":
        exponent_m = (2.0 + (B_prime / L_prime)) / (1.0 + (B_prime / L_prime))
    else:
        exponent_m = (2.0 + (L_prime / B_prime)) / (1.0 + (L_prime / B_prime))
        
    if H_factored_critical >= denominator_c:
        st.error("❌ HORIZONTAL FORCE SLIDING EQUILIBRIUM BREACHED: Pure sliding failure condition. Increase footing area or decrease lateral force.")
        lambda_iq = lambda_igamma = lambda_ic = 0.0
    else:
        lambda_iq = (1.0 - (H_factored_critical / denominator_c)) ** exponent_m
        lambda_igamma = (1.0 - (H_factored_critical / denominator_c)) ** (exponent_m + 1.0)
        lambda_ic = lambda_iq - ((1.0 - lambda_iq) / (Nc * np.tan(phi_rad)))

# 8. Foundation Geometry Shape Modifiers
if phi_deg == 0:
    lambda_cs = 1.0 + 0.2 * (B_prime / L_prime)
    lambda_qs = 1.0
    lambda_gammas = 1.0
else:
    lambda_cs = 1.0 + (B_prime / L_prime) * (Nq / Nc) * (lambda_iq / lambda_ic) if lambda_ic > 0 else 1.0
    lambda_qs = 1.0 + (B_prime / L_prime) * np.tan(phi_rad) * lambda_iq
    
    # CORRECTED CORE MATH: Changed the baseline multiplier reduction constant directly to 0.4
    lambda_gammas = max(0.6, 1.0 - 0.4 * (B_prime / L_prime))


# 9. Foundation Embedment Depth Modifiers
if Df == 0:
    lambda_cd = lambda_qd = lambda_gammad = 1.0
else:
    if phi_deg == 0:
        lambda_cd = 1.0 + 0.4 * (Df / B_prime)
        lambda_qd = 1.0
    else:
        lambda_qd = 1.0 + 2.0 * np.tan(phi_rad) * ((1.0 - np.sin(phi_rad))**2) * (Df / B_prime)
        lambda_cd = lambda_qd - (1.0 - lambda_qd) / (Nc * np.tan(phi_rad))
    lambda_gammad = 1.0

# 10. Synthesize Ultimate & Design Soil Capacity Values
term1 = c_calc * Nc * lambda_cs * lambda_cd * lambda_ic
term2 = q_surcharge * Nq * lambda_qs * lambda_qd * lambda_iq
term3 = 0.5 * gamma_prime * B_prime * Ngamma * lambda_gammas * lambda_gammad * lambda_igamma

qu = term1 + term2 + term3
qd = qu * phi_g

# 11. Calculate factored bearing pressure using effective area
q_factored = V_capacity_check / A_prime

# 12. Calculate CDR (Capacity Demand Ratio)
# CDR = Resistance / Demand = q_d / q_factored
# CDR > 1.0 means design is adequate (resistance exceeds demand)
CDR = qd / q_factored if q_factored > 0 else float('inf')

# --- Results Presentation Layer ---
st.write("---")
st.subheader("📊 Vertical Load Summary")

load_col1, load_col2, load_col3, load_col4 = st.columns(4)

with load_col1:
    st.metric(label="Structural Load (Unfactored)", value=f"{V_unfactored:.1f} kN")

with load_col2:
    st.metric(label="Structural Load (Factored)", value=f"{V_factored:.1f} kN")

with load_col3:
    st.metric(label="Foundation Self-Weight", value=f"{V_foundation_unfactored:.1f} kN", help=f"Area: {footing_area:.2f} m² × Depth: {Df:.2f} m × γ_c: {gamma_concrete:.1f} kN/m³")

with load_col4:
    st.metric(label="Foundation SW (Factored)", value=f"{V_foundation_factored:.1f} kN", help=f"Self-weight × {load_factor}")

load_summary_col1, load_summary_col2 = st.columns(2)

with load_summary_col1:
    st.write("**For Eccentricity Calculation (0.9 × Unfactored):**")
    st.write(f"*   0.9 × V_struct: {0.9 * V_unfactored:.2f} kN")
    st.write(f"*   0.9 × V_foundation: {0.9 * V_foundation_unfactored:.2f} kN")
    st.write(f"*   **V_eccentricity: {V_eccentricity:.2f} kN**")

with load_summary_col2:
    st.write("**For Bearing Capacity Check (Factored):**")
    st.write(f"*   V_struct (factored): {V_factored:.2f} kN")
    st.write(f"*   V_foundation (factored): {V_foundation_factored:.2f} kN")
    st.write(f"*   **V_capacity_check: {V_capacity_check:.2f} kN**")

st.write("---")
with st.expander("📋 Moment & Eccentricity Analysis (click to open)"):
    st.caption("📌 **NZS 1170.0 Table 4.2.1:** Eccentricity uses 0.9 × unfactored vertical load with factored horizontal load (worst-case overturning)")

    moment_col1, moment_col2, moment_col3 = st.columns(3)

    with moment_col1:
        st.markdown("**About B-axis (Width Direction):**")
        st.write(f"*   Direct Moment (factored): {M_B_factored:.2f} kN·m")
        st.write(f"*   Induced (H* × D_f): {M_B_induced:.2f} kN·m")
        st.write(f"*   **Total M_B: {M_B_total:.2f} kN·m**")
        st.write(f"*   Eccentricity e_B: {e_B:.4f} m")
        st.write(f"*   Middle third limit (B/6): {B_raw/6:.4f} m")
        middle_third_check_B = "✅ ACCEPTABLE" if e_B <= B_raw/6 else "❌ UNACCEPTABLE"
        st.write(f"*   **{middle_third_check_B}**")

    with moment_col2:
        st.markdown("**About L-axis (Length Direction):**")
        st.write(f"*   Direct Moment (factored): {M_L_factored:.2f} kN·m")
        st.write(f"*   Induced (H* × D_f): {M_L_induced:.2f} kN·m")
        st.write(f"*   **Total M_L: {M_L_total:.2f} kN·m**")
        st.write(f"*   Eccentricity e_L: {e_L:.4f} m")
        st.write(f"*   Middle third limit (L/6): {L_raw/6:.4f} m")
        middle_third_check_L = "✅ ACCEPTABLE" if e_L <= L_raw/6 else "❌ UNACCEPTABLE"
        st.write(f"*   **{middle_third_check_L}**")

    with moment_col3:
        st.markdown("**Effective Footing Dimensions (Meyerhof):**")
        st.write(f"*   Gross Width: {B_raw:.3f} m")
        st.write(f"*   **Effective Width (B'): {B_prime:.3f} m**")
        st.write(f"*   Gross Length: {L_raw:.3f} m")
        st.write(f"*   **Effective Length (L'): {L_prime:.3f} m**")
        st.write(f"*   **Effective Area (A'): {A_prime:.3f} m²**")

st.write("---")
st.subheader("🔍 Bearing Pressure Check (Ultimate Limit State)")
st.caption("**Capacity Demand Ratio (CDR):** CDR = q_d / q = Resistance / Demand. **CDR ≥ 1.0 = ADEQUATE**")

pressure_col1, pressure_col2, pressure_col3 = st.columns(3)

with pressure_col1:
    st.metric(label="Factored Bearing Demand (q)", value=f"{q_factored:.1f} kPa", help=f"V_capacity / A' = {V_capacity_check:.1f} / {A_prime:.3f}")

with pressure_col2:
    st.metric(label="Factored Bearing Resistance (q_d)", value=f"{qd:.1f} kPa", help=f"q_u × φ_g = {qu:.1f} × {phi_g:.2f}")

with pressure_col3:
    if CDR >= 1.0:
        st.metric(label="Capacity Demand Ratio (CDR)", value=f"{CDR:.2f}", delta="✅ ADEQUATE", delta_color="inverse")
    else:
        st.metric(label="Capacity Demand Ratio (CDR)", value=f"{CDR:.2f}", delta="❌ INADEQUATE", delta_color="off")

# Detailed bearing capacity result
if CDR >= 1.0:
    st.success(f"✅ **BEARING CAPACITY ADEQUATE:** CDR = {CDR:.2f} ≥ 1.0 (Resistance {(CDR-1.0)*100:.1f}% greater than Demand)")
else:
    st.error(f"❌ **BEARING CAPACITY INADEQUATE:** CDR = {CDR:.2f} < 1.0 (Demand exceeds Resistance by {(1.0-CDR)*100:.1f}%)")

st.write("---")
st.subheader("📊 Ultimate Geotechnical Capacity Results")

res_col1, res_col2, res_col3 = st.columns(3)
res_col1.metric(label="Ultimate Geotechnical Capacity (q_u)", value=f"{qu:.1f} kPa")
res_col2.metric(label="Geotechnical Reduction Factor (𝜙_g)", value=f"{phi_g:.2f}")
res_col3.metric(label="Design Geotechnical Capacity (q_d)", value=f"{qd:.1f} kPa")

pdf_input_rows = [
    ("Design Case", design_case),
    ("Footing Type", footing_type),
    ("Gross Width B", f"{B_raw:.3f} m"),
    ("Gross Length L", f"{L_raw:.3f} m"),
    ("Embedment Depth Df", f"{Df:.3f} m"),
    ("Soil Unit Weight gamma", f"{gamma:.2f} kN/m3"),
    ("Concrete Unit Weight gamma_c", f"{gamma_concrete:.2f} kN/m3"),
    ("Load Factor gamma_f", f"{load_factor:.2f}"),
    ("Groundwater Enabled", "Yes" if gw_active else "No"),
    ("Groundwater Depth", f"{dw:.3f} m" if gw_active else "N/A"),
    ("Factored Vertical Load V*", f"{V_factored:.2f} kN"),
    ("Unfactored Vertical Load V", f"{V_unfactored:.2f} kN"),
    ("Factored Moment M_B*", f"{M_B_factored:.2f} kN.m"),
    ("Factored Moment M_L*", f"{M_L_factored:.2f} kN.m"),
    ("Factored Horizontal Load H_B*", f"{H_factored_B:.2f} kN"),
    ("Factored Horizontal Load H_L*", f"{H_factored_L:.2f} kN"),
    ("Geotechnical Reduction Factor phi_g", f"{phi_g:.2f}"),
]

if design_case == "Seismic / Short-Term (Undrained)":
    pdf_input_rows.insert(1, ("Undrained Shear Strength Su", f"{Su:.2f} kPa"))
else:
    pdf_input_rows.insert(1, ("Effective Cohesion c'", f"{c_calc:.2f} kPa"))
    pdf_input_rows.insert(2, ("Friction Angle phi'", f"{phi_deg:.1f} deg"))

pdf_output_rows = [
    ("Critical Horizontal Direction", h_direction),
    ("V_eccentricity", f"{V_eccentricity:.2f} kN"),
    ("V_capacity_check", f"{V_capacity_check:.2f} kN"),
    ("Effective Width B'", f"{B_prime:.3f} m"),
    ("Effective Length L'", f"{L_prime:.3f} m"),
    ("Effective Area A'", f"{A_prime:.3f} m2"),
    ("Factored Bearing Demand q", f"{q_factored:.2f} kPa"),
    ("Ultimate Geotechnical Capacity q_u", f"{qu:.2f} kPa"),
    ("Design Geotechnical Capacity q_d", f"{qd:.2f} kPa"),
    ("Capacity Demand Ratio CDR", f"{CDR:.3f}"),
    ("Bearing Capacity Status", "ADEQUATE" if CDR >= 1.0 else "INADEQUATE"),
]

pdf_data = _build_pdf_report(pdf_input_rows, pdf_output_rows)
st.download_button(
    "📄 Download PDF Report (Inputs + Bearing Capacity Outputs)",
    data=pdf_data,
    file_name="b1_vm2_bearing_capacity_report.pdf",
    mime="application/pdf",
)

html_report = _build_printable_html_report(pdf_input_rows, pdf_output_rows)
st.download_button(
    "🖨️ Download Print-Friendly HTML Report",
    data=html_report,
    file_name="b1_vm2_bearing_capacity_report.html",
    mime="text/html",
)
with st.expander("🖥️ Preview Print-Friendly HTML Report"):
    st.caption("Use browser print (Ctrl/Cmd+P) in this preview for hardcopy or Save as PDF.")
    components.html(html_report, height=600, scrolling=True)

with st.expander("📝 Click to View Full Calculation Equation Expansion (Step-by-Step Multiplication)"):
    st.markdown("**Governing Ultimate Capacity Equation ($q_u$):**")
    st.latex(r"q_u = (c \times N_c \times \lambda_{cs} \times \lambda_{cd} \times \lambda_{ic}) + (q \times N_q \times \lambda_{qs} \times \lambda_{qd} \times \lambda_{iq}) + (0.5 \times \gamma' \times B' \times N_\gamma \times \lambda_{\gamma s} \times \lambda_{\gamma d} \times \lambda_{i\gamma})")
    
    st.markdown("**Your Values Multiplied Out:**")
    st.latex(rf"q_u = ({c_calc:.2f}\ \text{{×}}\ {Nc:.2f}\ \text{{×}}\ {lambda_cs:.2f}\ \text{{×}}\ {lambda_cd:.2f}\ \text{{×}}\ {lambda_ic:.2f}) + ({q_surcharge:.2f}\ \text{{×}}\ {Nq:.2f}\ \text{{×}}\ {lambda_qs:.2f}\ \text{{×}}\ {lambda_qd:.2f}\ \text{{×}}\ {lambda_iq:.2f}) + (0.5\ \text{{×}}\ {gamma_prime:.2f}\ \text{{×}}\ {B_prime:.2f}\ \text{{×}}\ {Ngamma:.2f}\ \text{{×}}\ {lambda_gammas:.2f}\ \text{{×}}\ {lambda_gammad:.2f}\ \text{{×}}\ {lambda_igamma:.2f})")
    
    st.markdown("**Calculated Partial Terms:**")
    st.write(f"*   **Cohesion Term:** {term1:.2f} kPa")
    st.write(f"*   **Surcharge Term ($q$):** {term2:.2f} kPa")
    st.write(f"*   **Soil Weight Term ($\gamma'$):** {term3:.2f} kPa")
    st.write(f"🚀 **Summed Ultimate Capacity ($q_u$):** {qu:.2f} kPa")
    
    st.markdown("**Design Capacity Verification ($q_d$):**")
    st.latex(rf"q_d = {qu:.2f}\ \text{{×}}\ {phi_g:.2f} = {qd:.2f}\ \text{{kPa}}")

# Consolidated Structural Audit Panel
st.write("---")
st.subheader("📊 Bearing Capacity Factors")
audit_col1, audit_col2, audit_col3 = st.columns(3)

with audit_col1:
    st.markdown("**Classical Factors ($N$):**")
    st.write(f"*   **$N_c$ (Cohesion Multiplier):** {Nc:.3f}")
    st.write(f"*   **$N_q$ (Surcharge Multiplier):** {Nq:.3f}")
    st.write(f"*   **$N_\gamma$ (Self-Weight Multiplier):** {Ngamma:.3f}")
    
    st.markdown("**Horizontal Loads Summary:**")
    st.write(f"*   **H_B (factored):** {H_factored_B:.2f} kN")
    st.write(f"*   **H_L (factored):** {H_factored_L:.2f} kN")
    st.write(f"*   **Critical direction:** {h_direction}")
    st.write(f"*   **Lever Arm (D_f):** {Df:.2f} m")

with audit_col2:
    st.markdown("**Geometry Modifying Factors ($\lambda$):**")
    st.write(rf"*   $\lambda_{{cs}}$ (Cohesion Shape): {lambda_cs:.3f}")
    st.write(rf"*   $\lambda_{{qs}}$ (Surcharge Shape): {lambda_qs:.3f}")
    st.write(rf"*   $\lambda_{{\gamma s}}$ (Soil Weight Modifier): {lambda_gammas:.3f}")
    st.write(rf"*   $\lambda_{{cd}}$ (Cohesion Depth): {lambda_cd:.3f}")
    st.write(rf"*   $\lambda_{{qd}}$ (Surcharge Depth): {lambda_qd:.3f}")
    st.write(rf"*   $\lambda_{{\gamma d}}$ (Weight Depth): {lambda_gammad:.3f}")

with audit_col3:
    st.markdown("**Load Inclination Factors ($\lambda_i$):**")
    st.write(f"*   Load Exponent ($m$): {exponent_m:.3f}")
    st.write(rf"*   $\lambda_{{ic}}$ (Cohesion Inclination): {lambda_ic:.3f}")
    st.write(rf"*   $\lambda_{{iq}}$ (Surcharge Inclination): {lambda_iq:.3f}")
    st.write(rf"*   $\lambda_{{i\gamma}}$ (Weight Inclination): {lambda_igamma:.3f}")


