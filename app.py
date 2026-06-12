import streamlit as st
import numpy as np

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
    V_structural = st.number_input("Structural Vertical Load, V*_struct (kN)", min_value=0.0, value=300.0, step=10.0, help="Design load from superstructure (applied at top of foundation)")
    
    # Calculate foundation self-weight
    footing_area = B_raw * L_raw
    V_foundation = footing_area * Df * gamma_concrete
    V_star = V_structural + V_foundation
    
    st.markdown("**Direct Bending Moments at Footing Base:**")
    M_B_input = st.number_input("Moment about B-axis (at toe), M_B* (kN·m)", min_value=0.0, value=15.0, step=5.0, help="Directly applied at footing base")
    if footing_type == "Rectangular Pad":
        M_L_input = st.number_input("Moment about L-axis (at toe), M_L* (kN·m)", min_value=0.0, value=10.0, step=5.0, help="Directly applied at footing base")
    else:
        M_L_input = 0.0

    st.markdown("**Lateral Loading (Applied at Top of Foundation):**")
    H_star = st.number_input("Horizontal Design Load, H* (kN)", min_value=0.0, value=35.0, step=5.0, help="Applied at top of foundation (ground level)")
    h_direction = st.selectbox(
        "Horizontal Load Direction", 
        ["Parallel to Width (B)", "Parallel to Length (L)"],
        help="Determines the orientation exponent 'm' for inclination calculations."
    )
    
    phi_g = st.slider("Geotechnical Reduction Factor (𝜙_g)", min_value=0.40, max_value=0.90, value=0.50, step=0.05)

# --- B1/VM2 Computational Core Engine ---

# 1. Calculate induced moments from horizontal force applied at top of foundation
#    Horizontal load acts at elevation of ground surface, creating lever arm of Df
M_B_induced = H_star * Df if h_direction == "Parallel to Width (B)" else 0.0
M_L_induced = H_star * Df if h_direction == "Parallel to Length (L)" else 0.0

# Total moments = input moments + induced moments from lever arm
M_B_total = M_B_input + M_B_induced
M_L_total = M_L_input + M_L_induced

# 2. Deduce Meyerhof Effective Dimensions from Overturning Moments
e_B = M_B_total / V_star if V_star > 0 else 0
e_L = M_L_total / V_star if V_star > 0 else 0

B_prime = B_raw - 2 * e_B
L_prime = L_raw - 2 * e_L

# Overturning safety check boundary
if B_prime <= 0 or L_prime <= 0:
    st.error("❌ STRUCTURAL CRITICAL FAILURE: Combined moments cause total eccentricity tension! Footing will overturn. Increase footing size, decrease lateral force, or increase depth.")
    st.stop()

A_prime = B_prime * L_prime
phi_rad = np.radians(phi_deg)

# 3. Advanced Groundwater Surcharge Rules
if gw_active and dw <= Df:
    q_surcharge = (dw * gamma) + ((Df - dw) * (gamma - gamma_w))
else:
    q_surcharge = Df * gamma

if gw_active:
    if dw <= Df:
        gamma_prime = gamma - gamma_w
    elif dw < (Df + B_prime):
        gamma_prime = gamma - gamma_w + ((dw - Df) / B_prime) * gamma_w
    else:
        gamma_prime = gamma
else:
    gamma_prime = gamma

# 4. Classic Vesic Bearing Capacity Factors
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

# 5. Load Inclination Multipliers (with Explicit Direction Exponents)
denominator_c = A_prime * c_calc + V_star * np.tan(phi_rad)

if phi_deg == 0:
    lambda_iq = 1.0
    lambda_igamma = 1.0
    lambda_ic = 1.0 - (H_star / (5.14 * A_prime * c_calc)) if (A_prime * c_calc) > 0 else 0.0
    exponent_m = 0.0
else:
    if h_direction == "Parallel to Width (B)":
        exponent_m = (2.0 + (B_prime / L_prime)) / (1.0 + (B_prime / L_prime))
    else:
        exponent_m = (2.0 + (L_prime / B_prime)) / (1.0 + (L_prime / B_prime))
        
    if H_star >= denominator_c:
        st.error("❌ HORIZONTAL FORCE SLIDING EQUILIBRIUM BREACHED: Pure sliding failure condition. Increase footing area or decrease lateral force.")
        lambda_iq = lambda_igamma = lambda_ic = 0.0
    else:
        lambda_iq = (1.0 - (H_star / denominator_c)) ** exponent_m
        lambda_igamma = (1.0 - (H_star / denominator_c)) ** (exponent_m + 1.0)
        lambda_ic = lambda_iq - ((1.0 - lambda_iq) / (Nc * np.tan(phi_rad)))

# 6. Foundation Geometry Shape Modifiers
if phi_deg == 0:
    lambda_cs = 1.0 + 0.2 * (B_prime / L_prime)
    lambda_qs = 1.0
    lambda_gammas = 1.0
else:
    lambda_cs = 1.0 + (B_prime / L_prime) * (Nq / Nc) * (lambda_iq / lambda_ic) if lambda_ic > 0 else 1.0
    lambda_qs = 1.0 + (B_prime / L_prime) * np.tan(phi_rad) * lambda_iq
    
    # CORRECTED CORE MATH: Changed the baseline multiplier reduction constant directly to 0.4
    lambda_gammas = max(0.6, 1.0 - 0.4 * (B_prime / L_prime))


# 7. Foundation Embedment Depth Modifiers
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

# 8. Synthesize Ultimate & Design Soil Capacity Values
term1 = c_calc * Nc * lambda_cs * lambda_cd * lambda_ic
term2 = q_surcharge * Nq * lambda_qs * lambda_qd * lambda_iq
term3 = 0.5 * gamma_prime * B_prime * Ngamma * lambda_gammas * lambda_gammad * lambda_igamma

qu = term1 + term2 + term3
qd = qu * phi_g

# --- Results Presentation Layer ---
st.write("---")
st.subheader("📊 Vertical Load Summary")

load_col1, load_col2, load_col3 = st.columns(3)

with load_col1:
    st.metric(label="Structural Load (V*_struct)", value=f"{V_structural:.1f} kN")

with load_col2:
    st.metric(label="Foundation Self-Weight", value=f"{V_foundation:.1f} kN", help=f"Area: {footing_area:.2f} m² × Depth: {Df:.2f} m × γ_c: {gamma_concrete:.1f} kN/m³")

with load_col3:
    st.metric(label="Total Vertical Load (V*)", value=f"{V_star:.1f} kN")

st.write("---")
st.subheader("📊 Ultimate Geotechnical Capacity Results")

res_col1, res_col2, res_col3 = st.columns(3)
res_col1.metric(label="Ultimate Geotechnical Capacity (q_u)", value=f"{qu:.1f} kPa")
res_col2.metric(label="Geotechnical Reduction Factor (𝜙_g)", value=f"{phi_g:.2f}")
res_col3.metric(label="Design Geotechnical Capacity (q_d)", value=f"{qd:.1f} kPa")

# Interactive Full Calculation Equation Breakdowns
st.write("---")
st.subheader("📋 Moment & Eccentricity Analysis")

moment_col1, moment_col2, moment_col3 = st.columns(3)

with moment_col1:
    st.markdown("**About B-axis (Width Direction):**")
    st.write(f"*   Direct Moment: {M_B_input:.2f} kN·m")
    st.write(f"*   Induced (H × D_f): {M_B_induced:.2f} kN·m")
    st.write(f"*   **Total M_B: {M_B_total:.2f} kN·m**")
    st.write(f"*   Eccentricity e_B: {e_B:.3f} m")

with moment_col2:
    st.markdown("**About L-axis (Length Direction):**")
    st.write(f"*   Direct Moment: {M_L_input:.2f} kN·m")
    st.write(f"*   Induced (H × D_f): {M_L_induced:.2f} kN·m")
    st.write(f"*   **Total M_L: {M_L_total:.2f} kN·m**")
    st.write(f"*   Eccentricity e_L: {e_L:.3f} m")

with moment_col3:
    st.markdown("**Effective Footing Dimensions (Meyerhof):**")
    st.write(f"*   Gross Width: {B_raw:.3f} m")
    st.write(f"*   **Effective Width (B'): {B_prime:.3f} m**")
    st.write(f"*   Gross Length: {L_raw:.3f} m")
    st.write(f"*   **Effective Length (L'): {L_prime:.3f} m**")
    st.write(f"*   **Effective Area (A'): {A_prime:.3f} m²**")

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
    
    st.markdown("**Horizontal Load Summary:**")
    st.write(f"*   **H* (at top):** {H_star:.2f} kN")
    st.write(f"*   **Direction:** {h_direction}")
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
