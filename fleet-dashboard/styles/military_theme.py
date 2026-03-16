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
    /* ===== GOOGLE FONTS IMPORT ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono:wght@400;700&display=swap');

    /* ===== PAGE BACKGROUND & BASE TYPOGRAPHY ===== */
    .stApp {
        background-color: #050A14;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }

    /* ===== HEADERS & TITLES ===== */
    h1, h2, h3, .ops-title {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        letter-spacing: 2px !important;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.2);
    }
    .ops-subtitle {
        color: #FFB800 !important;
        font-weight: 700;
        letter-spacing: 1px;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background-color: #02050A;
        border-right: 1px solid #1A3A5C;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown h4 {
        color: #FFB800 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.1rem !important;
    }

    /* ===== METRIC CARDS ===== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #0A1425 0%, #15253A 100%);
        border: 1px solid #2A5080;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        text-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
    }
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: #A0C0E0 !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0A1425;
        border-bottom: 2px solid #1A3A5C;
        padding: 0 20px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #A0C0E0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem !important;
        font-weight: 700 !important;
        padding: 15px 25px;
    }
    .stTabs [aria-selected="true"] {
        color: #00FF88 !important;
        border-bottom: 2px solid #00FF88 !important;
    }

    /* ===== BUTTONS ===== */
    .stButton > button {
        background: linear-gradient(135deg, #1A3A5C 0%, #2A5080 100%);
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 1px solid #4A70A0;
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 6px;
        padding: 0.5rem 1rem;
    }
    .stButton > button:hover {
        border-color: #00FF88;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
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
        background-color: #0A1425 !important;
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
        padding: 4px 12px !important;
        border-radius: 4px !important;
        font-size: 0.85rem !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: bold;
        letter-spacing: 1px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
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

    /* ===== MILITARY INTEL / ALERT BOXES ===== */
    .military-intel, .stAlert {
        background: rgba(10, 20, 37, 0.95) !important;
        border: 1px solid #FFB800 !important;
        border-left: 6px solid #FFB800 !important;
        border-radius: 4px;
        padding: 16px;
        margin: 16px 0;
        color: #FFFFFF !important;
        font-size: 1.05rem !important;
        line-height: 1.6 !important;
    }
    .military-intel h4 {
        color: #FFB800 !important;
        font-family: 'Courier New', monospace;
        margin-top: 0;
        font-size: 1.2rem !important;
        margin-bottom: 12px !important;
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

    /* ===== SELECTBOX & INPUTS ===== */
    div[data-baseweb="select"], div[data-baseweb="input"] {
        background-color: #0A1425 !important;
        border: 1px solid #1A3A5C !important;
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
    
    /* Global scrollbar for premium feel */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #050A14;
    }
    ::-webkit-scrollbar-thumb {
        background: #1A3A5C;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #2A5080;
    }
    """
