import streamlit as st
import numpy as np

st.set_page_config(page_title="NZBC B1/VM2 Advanced Calculator", page_icon="🇳🇿", layout="wide")

st.title("🇳🇿 B1/VM2 Bearing Capacity Calculator (Advanced)")
st.markdown("""
Adheres strictly to the **New Zealand Building Code Verification Method B1/VM2**.
Includes shape, depth, **load inclination factors**, and **groundwater table** variations.
""")

# Layout main panels
col_geom, col_soil, col_loads = st.columns(3)

with col_geom:
    st.header("📐 Geometry & Water")
    footing_type = st.selectbox("Footing Shape", ["Rectangular / Pad", "Continuous / Strip"])
    B = st.number_input("Effective Width, B' (m)", min_value=0.1, value=1.5, step=0.1)
    
    if footing_type == "Rectangular / Pad":
        L = st.number_input("Effective Length, L' (m)", min_value=0.1, value=2.0, step=0.1)
    else:
        L = 100000.0 # Approximation of infinity for strip footings
        
    Df = st.number_input("Embedment Depth, Df (m)", min_value=0.0, value=0.6, step=0.1)
    
    st.markdown("---")
    st.subheader("💧 Groundwater Table")
    gw_active = st.checkbox("Enable Groundwater Table Effects", value=False)
    if gw_active:
        dw = st.number_input("Water Depth from Ground Surface, dw (m)", min_value=0.0, value=0.4, step=0.1)
        gamma_w = 9.81  # kN/m³
    else:
        dw = 999.0
        gamma_w = 0.0

with col_soil:
    st.header("🪨 Soil Properties")
    c = st.number_input("Cohesion, c' or Su (kPa)", min_value=0.0, value=5.0, step=1.0)
    phi_deg = st.slider("Internal Friction Angle, ϕ' (degrees)", min_value=0, max_value=45, value=28)
    gamma_dry = st.number_input("Bulk Unit Weight, γ (kN/m³)", min_value=10.0, value=18.0, step=0.5)
    
    if gw_active:
        gamma_sat = st.number_input("Saturated Unit Weight, γ_sat (kN/m³)", min_value=12.0, value=20.0, step=0.5)
    else:
        gamma_sat = gamma_dry

with col_loads:
    st.header("🏋️ Design Action Loads")
    st.markdown("Enter *Ultimate Limit State (ULS)* design loads acting on the foundation base:")
    V_star = st.number_input("Vertical Design Load, V* (kN)", min_value=1.0, value=250.0, step=10.0)
    H_star = st.number_input("Horizontal Design Load, H* (kN)", min_value=0.0, value=40.0, step=5.0)
    phi_g = st.slider("Geotechnical Reduction Factor (𝜙_g)", min_value=0.40, max_value=0.90, value=0.50, step=0.05)

# --- B1/VM2 Mathematical Core ---
phi_rad = np.radians(phi_deg)

# 1. Groundwater Mechanics (Effective stress adjustments)
# Calculate surcharge stress (q) at foundation base level
if gw_active and dw <= Df:
    q_surcharge = (dw * gamma_dry) + ((Df - dw) * (gamma_sat - gamma_w))
else:
    q_surcharge = Df * gamma_dry

# Calculate effective unit weight (gamma_prime) for the wedge zone below the foundation base
if gw_active:
    if dw <= Df:
        gamma_prime = gamma_sat - gamma_w
    elif dw < (Df + B):
        # Linear interpolation for water table within the wedge depth B below base
        gamma_prime = gamma_dry + ((dw - Df) / B) * (gamma_sat - gamma_w - gamma_dry)
    else:
        gamma_prime = gamma_dry
else:
    gamma_prime = gamma_dry

# 2. Classical Vesic Bearing Capacity Factors
if phi_deg == 0:
    Nc = 5.14
    Nq = 1.0
    Ngamma = 0.0
else:
    Nq = np.exp(np.pi * np.tan(phi_rad)) * (np.tan(np.pi/4 + phi_rad/2))**2
    Nc = (Nq - 1.0) / np.tan(phi_rad)
    Ngamma = 2.0 * (Nq + 1.0) * np.tan(phi_rad)

# 3. Load Inclination Factors (lambda_i) - Brinch-Hansen / Vesic Formulas
# Prevent division errors if cohesion or area components equal zero
A_prime = B * L
denominator_c = A_prime * c + V_star * np.tan(phi_rad)

if phi_deg == 0:
    # Undrained clay scenario
    lambda_iq = 1.0
    lambda_igamma = 1.0
    lambda_ic = 1.0 - (H_star / (5.14 * A_prime * c))
else:
    # General soil formulation
    exponent_m = (2.0 + (B / L)) / (1.0 + (B / L))  # Assuming load acts parallel to B'
    
    if H_star >= (V_star * np.tan(phi_rad) + A_prime * c):
        st.error("❌ High lateral force causing immediate sliding failure! Reduce H* or increase footing size.")
        lambda_iq = lambda_igamma = lambda_ic = 0.0
    else:
        lambda_iq = (1.0 - (H_star / denominator_c)) ** exponent_m
        lambda_igamma = (1.0 - (H_star / denominator_c)) ** (exponent_m + 1.0)
        lambda_ic = lambda_iq - ((1.0 - lambda_iq) / (Nc * np.tan(phi_rad)))

# 4. Shape Correction Factors (lambda_s)
if phi_deg == 0:
    lambda_cs = 1.0 + 0.2 * (B / L)
    lambda_qs = 1.0
    lambda_gammas = 1.0
else:
    lambda_cs = 1.0 + (B / L) * (Nq / Nc) * lambda_iq / lambda_ic if lambda_ic > 0 else 1.0
    lambda_qs = 1.0 + (B / L) * np.tan(phi_rad) * lambda_iq
    lambda_gammas = max(0.6, 1.0 - 0.4 * (B / L) * (lambda_igamma / lambda_qs) if lambda_qs > 0 else 1.0)

# 5. Depth Correction Factors (lambda_d) for shallow conditions (Df <= B)
if Df == 0:
    lambda_cd = lambda_qd = lambda_gammad = 1.0
else:
    if phi_deg == 0:
        lambda_cd = 1.0 + 0.4 * (Df / B)
        lambda_qd = 1.0
    else:
        lambda_qd = 1.0 + 2.0 * np.tan(phi_rad) * ((1.0 - np.sin(phi_rad))**2) * (Df / B)
        lambda_cd = lambda_qd - (1.0 - lambda_qd) / (Nc * np.tan(phi_rad))
    lambda_gammad = 1.0

# 6. Combined Ultimate Bearing Capacity Evaluation
term1 = c * Nc * lambda_cs * lambda_cd * lambda_ic
term2 = q_surcharge * Nq * lambda_qs * lambda_qd * lambda_iq
term3 = 0.5 * gamma_prime * B * Ngamma * lambda_gammas * lambda_gammad * lambda_igamma

qu = term1 + term2 + term3
qd = qu * phi_g

# --- Results Presentation ---
st.write("---")
st.subheader("📊 Ultimate Limit State Results")

res_col1, res_col2, res_col3 = st.columns(3)
res_col1.metric(label="Ultimate Bearing Capacity (q_u)", value=f"{qu:.1f} kPa")
res_col2.metric(label="Geotechnical Reduction Factor (𝜙_g)", value=f"{phi_g:.2f}")
res_col3.metric(label="Design Bearing Capacity (q_d)", value=f"{qd:.1f} kPa")

# Design Safety Audit Area
st.write("---")
st.subheader("🔍 Verification Factor Breakdown")
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    with st.expander("Classical Factors (N)"):
        st.latex(r"N_c = " + f"{Nc:.3f}")
        st.latex(r"N_q = " + f"{Nq:.3f}")
        st.latex(r"N_\gamma = " + f"{Ngamma:.3f}")

with col_b2:
    with st.expander("Modifying Factors (𝝀)"):
        st.write("**Shape:**")
        st.write(f"λ_cs: {lambda_cs:.2f} | λ_qs: {lambda_qs:.2f} | λ_γs: {lambda_gammas:.2f}")
        st.write("**Depth:**")
        st.write(f"λ_cd: {lambda_cd:.2f} | λ_qd: {lambda_qd:.2f} | λ_γd: {lambda_gammad:.2f}")
        st.write("**Load Inclination:**")
        st.write(f"λ_ic: {lambda_ic:.2f} | λ_iq: {lambda_iq:.2f} | λ_iγ: {lambda_igamma:.2f}")

with col_b3:
    with st.expander("Soil Loading Stresses"):
        st.write(f"**Effective Base Surcharge ($q$):** {q_surcharge:.2f} kPa")
        st.write(f"**Effective Wedge Weight ($\gamma'$):** {gamma_prime:.2f} kN/m³")
        if gw_active:
            st.caption("Water table layer adjustments active.")
