import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from io import StringIO

# Theory spectra data (embedded for deployment)
THEORY_SPECTRA = {
    "SnCl6": {"wavenumbers": [290.84, 228.5, 152.4], "intensities": [417, 13.89, 90.5]},
    "SnBr6": {"wavenumbers": [174.59, 135.64, 95.51], "intensities": [1968.58, 61.18, 173.52]},
    "SnCl5Br": {"wavenumbers": [290.27, 288.23, 259.8, 226.45, 207.01, 158.88, 146.21, 130.05, 110.16], "intensities": [253.29, 7.4, 182.98, 10.97, 140.95, 6.35, 64.67, 62.64, 84.33]},
    "SnCl4Br2 (cis)": {"wavenumbers": [287.73, 284.61, 244.01, 223.06, 192.49, 155.6, 140.7, 130.56, 119.69, 103.7], "intensities": [239.22, 5.84, 223.61, 8.86, 323.86, 68.9, 1.85, 35.9, 59.62, 95.83]},
    "SnCl4Br2 (trans)": {"wavenumbers": [266.05809, 227.36, 149.22, 123.39, 117.22], "intensities": [510.16, 16.53, 60.2, 118.44, 23.91]},
    "SnCl3Br3 (fac)": {"wavenumbers": [285.14, 268.06, 196.28, 186.02, 148.36, 135.16, 121.61, 115.72, 101.6], "intensities": [240.45, 8.27, 494.54, 2.42, 91.09, 74.44, 23.82, 16.99, 106.58]},
    "SnCl3Br3 (mer)": {"wavenumbers": [281.75, 276.58, 243.85, 213.87, 178.86, 156.72, 138.98, 122.67, 114.97, 101.15], "intensities": [2.46, 177.25, 334.36, 10.2, 316.35, 19.72, 33.18, 62.17, 4.0, 65.71]},
    "SnCl2Br4 (cis)": {"wavenumbers": [276.38, 210.44, 190.86, 173.81, 158.42, 139.74, 122.19, 113.19, 104.68, 97.09], "intensities": [198.27, 15.21, 647.7, 318.57, 93.11, 73.2, 10.11, 42.92, 27.22, 65.06]},
    "SnCl2Br4 (trans)": {"wavenumbers": [244.76, 161.6, 135.91, 112.12, 100.61], "intensities": [559.22, 301.5, 6.74, 118.88, 14.98]},
    "SnCl1Br5": {"wavenumbers": [268.54, 208.14, 184.37, 150.98, 135.81, 123.88, 109.06, 101.27, 97.69], "intensities": [122.58, 14.5, 845.04, 109.05, 13.32, 19.24, 10.73, 66.04, 60.49]}
}

SPECTRUM_ORDER = [
    "SnCl6", "SnCl5Br", "SnCl4Br2 (cis)", "SnCl4Br2 (trans)",
    "SnCl3Br3 (fac)", "SnCl3Br3 (mer)", "SnCl2Br4 (cis)", 
    "SnCl2Br4 (trans)", "SnCl1Br5", "SnBr6"
]

def lorentzian(x, x0, intensity, gamma=4.0):
    """Generate Lorentzian peak."""
    return intensity * (gamma**2) / ((x - x0)**2 + gamma**2)

def generate_spectrum(wavenumbers, intensities, x_range, shift=0, gamma=4.0):
    """Convert discrete peaks to continuous spectrum."""
    spectrum = np.zeros_like(x_range)
    for wn, intensity in zip(wavenumbers, intensities):
        spectrum += lorentzian(x_range, wn + shift, intensity, gamma)
    return spectrum

def parse_xy_file(content):
    """Parse XY file content."""
    lines = content.strip().split('\n')
    x_data, y_data = [], []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.replace(',', ' ').replace('\t', ' ').split()
        if len(parts) >= 2:
            try:
                x_data.append(float(parts[0]))
                y_data.append(float(parts[1]))
            except ValueError:
                continue
    
    return np.array(x_data), np.array(y_data)

st.set_page_config(page_title="Raman Spectrum Fitting", layout="wide")

st.title("🔬 Raman Spectrum Fitting for SnX₆ Octahedra")
st.markdown("Fit experimental Raman spectra against theory spectra for Sn-halide octahedra (SnCl₆₋ₙBrₙ)")

# Sidebar for controls
st.sidebar.header("📁 Data Upload")
uploaded_file = st.sidebar.file_uploader(
    "Upload experimental spectrum (XY file)",
    type=['txt', 'xy', 'dat', 'csv'],
    help="Two-column file with wavenumber and intensity"
)

st.sidebar.header("⚙️ Peak Parameters")
gamma = st.sidebar.slider("Peak width (FWHM)", 1.0, 20.0, 4.0, 0.5,
                          help="Lorentzian line width parameter")
rigid_shift = st.sidebar.slider("Rigid wavenumber shift (cm⁻¹)", -50.0, 50.0, 0.0, 0.5,
                                help="Shift all theory spectra")

st.sidebar.header("📊 Coefficient Controls")

# Store coefficients in session state
if 'coefficients' not in st.session_state:
    st.session_state.coefficients = {name: 0.0 for name in SPECTRUM_ORDER}

# Reset button
if st.sidebar.button("Reset All Coefficients"):
    for name in SPECTRUM_ORDER:
        st.session_state.coefficients[name] = 0.0
    st.rerun()

# Coefficient sliders
coefficients = {}
for name in SPECTRUM_ORDER:
    coefficients[name] = st.sidebar.slider(
        name, 0.0, 2.0, 
        st.session_state.coefficients.get(name, 0.0), 
        0.01,
        key=f"coef_{name}"
    )
    st.session_state.coefficients[name] = coefficients[name]

# Main content area
x_range = np.linspace(0, 400, 2000)

# Generate fitted spectrum
fitted_spectrum = np.zeros_like(x_range)
individual_spectra = {}

for name in SPECTRUM_ORDER:
    if coefficients[name] > 0:
        spec_data = THEORY_SPECTRA[name]
        individual = generate_spectrum(
            spec_data['wavenumbers'], 
            spec_data['intensities'],
            x_range, 
            shift=rigid_shift,
            gamma=gamma
        )
        individual_spectra[name] = individual * coefficients[name]
        fitted_spectrum += individual_spectra[name]

# Create the plot
fig = go.Figure()

# Plot experimental data if uploaded
exp_x, exp_y = None, None
if uploaded_file is not None:
    content = uploaded_file.getvalue().decode('utf-8')
    exp_x, exp_y = parse_xy_file(content)
    
    # Filter to 0-400 range
    mask = (exp_x >= 0) & (exp_x <= 400)
    exp_x, exp_y = exp_x[mask], exp_y[mask]
    
    # Normalize experimental spectrum to max = 1000 (similar scale to theory)
    if len(exp_y) > 0 and np.max(exp_y) > 0:
        exp_y = exp_y * (1000.0 / np.max(exp_y))
        st.sidebar.success(f"✓ Loaded {len(exp_x)} points (normalized)")
    
    if len(exp_x) > 0:
        fig.add_trace(go.Scatter(
            x=exp_x, y=exp_y,
            mode='lines',
            name='Experimental',
            line=dict(color='black', width=2)
        ))

# Plot individual theory spectra (semi-transparent)
colors = [
    '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00',
    '#ffff33', '#a65628', '#f781bf', '#999999', '#66c2a5'
]

for i, name in enumerate(SPECTRUM_ORDER):
    if name in individual_spectra:
        fig.add_trace(go.Scatter(
            x=x_range, y=individual_spectra[name],
            mode='lines',
            name=name,
            line=dict(color=colors[i], width=1),
            opacity=0.5
        ))

# Plot fitted sum
if np.any(fitted_spectrum > 0):
    fig.add_trace(go.Scatter(
        x=x_range, y=fitted_spectrum,
        mode='lines',
        name='Fitted Sum',
        line=dict(color='red', width=2, dash='dash')
    ))

fig.update_layout(
    title="Raman Spectrum Fitting",
    xaxis_title="Wavenumber (cm⁻¹)",
    yaxis_title="Intensity (a.u.)",
    xaxis=dict(range=[0, 400], autorange='reversed'),
    height=600,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.02
    ),
    margin=dict(r=200)
)

st.plotly_chart(fig, use_container_width=True)

# Display active coefficients
st.subheader("Active Components")
active = {name: coef for name, coef in coefficients.items() if coef > 0}
if active:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Species Contributions:**")
        for name, coef in active.items():
            st.write(f"- {name}: {coef:.2f}")
    with col2:
        total = sum(active.values())
        if total > 0:
            st.markdown("**Relative Fractions:**")
            for name, coef in active.items():
                st.write(f"- {name}: {100*coef/total:.1f}%")
else:
    st.info("Adjust the coefficient sliders to add theory spectra to the fit.")

# Residual analysis if experimental data present
if exp_x is not None and len(exp_x) > 0 and np.any(fitted_spectrum > 0):
    st.subheader("Fit Quality")
    
    # Interpolate fitted to experimental x values
    fitted_interp = np.interp(exp_x, x_range, fitted_spectrum)
    
    residual = exp_y - fitted_interp
    ss_res = np.sum(residual**2)
    ss_tot = np.sum((exp_y - np.mean(exp_y))**2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    
    col1, col2 = st.columns(2)
    col1.metric("R²", f"{r_squared:.4f}")
    col2.metric("RMS Residual", f"{np.sqrt(np.mean(residual**2)):.2f}")
    
    # Residual plot
    fig_resid = go.Figure()
    fig_resid.add_trace(go.Scatter(
        x=exp_x, y=residual,
        mode='lines',
        name='Residual',
        line=dict(color='gray')
    ))
    fig_resid.add_hline(y=0, line_dash="dash", line_color="black")
    fig_resid.update_layout(
        title="Residual (Experimental - Fit)",
        xaxis_title="Wavenumber (cm⁻¹)",
        yaxis_title="Residual Intensity",
        xaxis=dict(range=[0, 400], autorange='reversed'),
        height=300
    )
    st.plotly_chart(fig_resid, use_container_width=True)

# Instructions
with st.expander("📖 Instructions"):
    st.markdown("""
    ### How to use this app:
    
    1. **Upload your experimental spectrum** using the file uploader in the sidebar
       - Accepts .txt, .xy, .dat, or .csv files
       - Format: two columns (wavenumber, intensity) separated by spaces, tabs, or commas
       - The spectrum is automatically normalized (max intensity = 1000)
       
    2. **Adjust the peak width (FWHM)** to match your experimental resolution
    
    3. **Apply a rigid shift** if your theory and experimental wavenumbers are offset
    
    4. **Adjust coefficients** for each SnX₆ species to fit the experimental spectrum
       - The fit updates in real-time as you move the sliders
       
    5. **View fit quality** metrics if experimental data is loaded
    
    ### Theory Spectra:
    The app includes 10 theory spectra for mixed Sn-halide octahedra:
    - **SnCl₆** and **SnBr₆** (end members)
    - **SnCl₅Br** and **SnClBr₅** (singly substituted)
    - **SnCl₄Br₂** (cis and trans isomers)
    - **SnCl₃Br₃** (fac and mer isomers)  
    - **SnCl₂Br₄** (cis and trans isomers)
    """)
