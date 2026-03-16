"""
Military Operations Center CSS theme.

Provides a complete dark military theme for all Streamlit elements.
"""


def inject_military_css():
    """
    Return the complete CSS string for the military ops center theme.

    Apply with st.markdown(f'<style>{inject_military_css()}</style>',
                           unsafe_allow_html=True)

    Returns
    -------
    str
        Complete CSS stylesheet.
    """
    return """
    /* ===== PAGE BACKGROUND ===== */
    .stApp {
        background-color: #0A0F1A;
        color: #E0E8FF;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background-color: #060B14;
        border-right: 1px solid #1A3A5C;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #FFB800;
        font-family: 'Courier New', monospace;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* ===== METRIC CARDS ===== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #0D1B2A 0%, #1B2838 100%);
        border: 1px solid #1A3A5C;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 0 15px rgba(26, 58, 92, 0.3);
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-family: 'Courier New', monospace;
        font-size: 2.2rem;
        font-weight: bold;
        text-shadow: 0 0 10px currentColor, 0 0 20px currentColor;
    }
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: #7A9CC0;
        font-size: 0.8rem;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-family: 'Courier New', monospace;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0D1B2A;
        border-bottom: 2px solid #1A3A5C;
        gap: 0;
    }
    .stTabs [data-baseweb="tab"] {
        color: #7A9CC0;
        font-family: 'Courier New', monospace;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: 10px 20px;
        border-bottom: 2px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #FFB800 !important;
        border-bottom: 2px solid #FFB800 !important;
    }

    /* ===== BUTTONS ===== */
    .stButton > button {
        background: linear-gradient(135deg, #1A3A5C 0%, #2A5080 100%);
        color: #E0E8FF;
        border: 1px solid #3A6090;
        font-family: 'Courier New', monospace;
        letter-spacing: 1px;
        text-transform: uppercase;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2A5080 0%, #3A70A0 100%);
        box-shadow: 0 0 10px rgba(42, 80, 128, 0.5);
        border-color: #FFB800;
    }

    /* ===== EXECUTE BUTTON (primary) ===== */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #8B6914 0%, #D4A017 100%);
        color: #0A0F1A;
        font-weight: bold;
        border: 2px solid #FFB800;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 20px rgba(255, 184, 0, 0.4);
    }

    /* ===== SLIDERS ===== */
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background-color: #FFB800;
    }
    .stSlider [data-baseweb="slider"] [data-testid="stTickBar"] {
        background: #1A3A5C;
    }

    /* ===== DATAFRAMES ===== */
    .stDataFrame {
        border: 1px solid #1A3A5C;
        border-radius: 4px;
    }
    .stDataFrame thead th {
        background-color: #0D1B2A !important;
        color: #FFB800 !important;
        font-family: 'Courier New', monospace;
        letter-spacing: 1px;
    }
    .stDataFrame tbody td {
        background-color: #0A0F1A !important;
        color: #E0E8FF !important;
        font-family: 'Courier New', monospace;
    }
    .stDataFrame tbody tr:nth-of-type(even) td {
        background-color: #0D1420 !important;
    }

    /* ===== PLOTLY CHARTS ===== */
    .js-plotly-plot {
        border: 1px solid #1A3A5C;
        border-radius: 4px;
    }

    /* ===== CUSTOM CARDS ===== */
    .military-card {
        background: linear-gradient(135deg, #0D1B2A 0%, #1B2838 100%);
        border: 1px solid #1A3A5C;
        border-radius: 8px;
        padding: 16px;
        margin: 4px 0;
    }
    .military-card-fmc { border-left: 4px solid #00FF88; }
    .military-card-pmc { border-left: 4px solid #FFB800; }
    .military-card-nmc { border-left: 4px solid #FF3B3B; }
    .military-card-pam { border-left: 4px solid #FF6600; }

    /* ===== STATUS BADGES ===== */
    .status-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 0.75rem;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        letter-spacing: 1px;
    }
    .badge-fmc { background: #00FF88; color: #0A0F1A; }
    .badge-pmc { background: #FFB800; color: #0A0F1A; }
    .badge-nmc { background: #FF3B3B; color: #FFFFFF; }
    .badge-pam { background: #FF6600; color: #FFFFFF; }
    .badge-depot { background: #444466; color: #FFFFFF; }

    /* ===== HEALTH BARS ===== */
    .health-bar {
        height: 6px;
        border-radius: 3px;
        background: #1A2030;
        margin: 2px 0;
        overflow: hidden;
    }
    .health-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.5s ease;
    }
    .health-fill-good { background: linear-gradient(90deg, #00CC66, #00FF88); }
    .health-fill-warn { background: linear-gradient(90deg, #CC8800, #FFB800); }
    .health-fill-crit { background: linear-gradient(90deg, #CC2222, #FF3B3B); }

    /* ===== RECOMMENDATION BOX ===== */
    .military-intel {
        background: #0D1B2A;
        border: 1px solid #FFB800;
        border-left: 4px solid #FFB800;
        border-radius: 4px;
        padding: 16px;
        margin: 16px 0;
    }
    .military-intel h4 {
        color: #FFB800;
        font-family: 'Courier New', monospace;
        margin-top: 0;
    }

    /* ===== KEY FINDING BOX ===== */
    .key-finding {
        background: linear-gradient(135deg, #0D1B2A 0%, #1A2838 100%);
        border: 2px solid #FFB800;
        border-radius: 8px;
        padding: 24px;
        margin: 16px 0;
        text-align: center;
    }
    .key-finding .number {
        font-family: 'Courier New', monospace;
        font-size: 3rem;
        font-weight: bold;
        color: #FFB800;
        text-shadow: 0 0 20px rgba(255, 184, 0, 0.5);
    }

    /* ===== TITLE STYLING ===== */
    .ops-title {
        font-family: 'Courier New', monospace;
        font-size: 1.8rem;
        color: #E0E8FF;
        letter-spacing: 4px;
        text-transform: uppercase;
        font-weight: bold;
        margin-bottom: 0;
    }
    .ops-subtitle {
        font-family: 'Courier New', monospace;
        font-size: 0.75rem;
        color: #FFB800;
        letter-spacing: 2px;
    }
    .ops-divider {
        border: none;
        border-top: 1px solid #FFB800;
        margin: 8px 0 16px 0;
    }

    /* ===== TOGGLE ===== */
    [data-testid="stToggle"] span {
        color: #E0E8FF;
    }

    /* ===== SELECTBOX ===== */
    [data-baseweb="select"] {
        background-color: #0D1B2A;
    }

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        background-color: #0D1B2A;
        color: #7A9CC0;
        font-family: 'Courier New', monospace;
    }

    /* ===== PROGRESS BAR ===== */
    .stProgress > div > div {
        background-color: #FFB800;
    }

    /* ===== WARNING/INFO BOXES ===== */
    .stAlert {
        background-color: #1A1A10;
        border: 1px solid #FFB800;
        color: #FFB800;
    }

    /* ===== FLOATING EXPORT BUTTON ===== */
    .export-fab {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        background: #1A3A5C;
        border: 1px solid #3A6090;
        border-radius: 50%;
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    """
