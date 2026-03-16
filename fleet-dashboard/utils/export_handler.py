"""Export handler for CSV/JSON downloads."""

import json
import io
import pandas as pd
import streamlit as st


def render_export_panel(result, mc_df=None):
    """
    Render the export data section with download buttons.

    Parameters
    ----------
    result : dict
        Single simulation results.
    mc_df : pd.DataFrame or None
        Monte Carlo summary results.
    """
    st.markdown("#### DATA EXPORT")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_csv = result['kpi_df'].to_csv(index=False)
        st.download_button(
            "📊 KPI TIME SERIES",
            kpi_csv,
            "kpi_timeseries.csv",
            "text/csv",
            key="dl_kpi",
        )

    with c2:
        if result.get('maint_log'):
            maint_df = pd.DataFrame(result['maint_log'])
            maint_csv = maint_df.to_csv(index=False)
        else:
            maint_csv = "No maintenance events"
        st.download_button(
            "🔧 MAINTENANCE LOG",
            maint_csv,
            "maintenance_log.csv",
            "text/csv",
            key="dl_maint",
        )

    with c3:
        if result.get('stock_df') is not None and len(result['stock_df']) > 0:
            stock_csv = result['stock_df'].to_csv(index=False)
        else:
            stock_csv = "No stock data"
        st.download_button(
            "📦 INVENTORY DATA",
            stock_csv,
            "inventory_data.csv",
            "text/csv",
            key="dl_stock",
        )

    with c4:
        if mc_df is not None:
            mc_csv = mc_df.to_csv(index=False)
        else:
            mc_csv = "Run Monte Carlo first"
        st.download_button(
            "🎲 MONTE CARLO RESULTS",
            mc_csv,
            "monte_carlo_results.csv",
            "text/csv",
            key="dl_mc",
        )

    # JSON config export
    config = {
        'fleet_size': result.get('fleet_size', 12),
        'mcr': result.get('mcr', 0),
        'fmcr': result.get('fmcr', 0),
        'pam': result.get('pam', 0),
        'total_sorties': result.get('total_sorties', 0),
        'total_hours': result.get('total_hours', 0),
    }
    config_json = json.dumps(config, indent=2)
    st.download_button(
        "📋 SIMULATION CONFIG (JSON)",
        config_json,
        "simulation_config.json",
        "application/json",
        key="dl_config",
    )
