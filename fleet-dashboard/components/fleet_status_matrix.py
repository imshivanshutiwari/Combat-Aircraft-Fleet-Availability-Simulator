"""Fleet status matrix - HTML/CSS aircraft status cards."""

import streamlit as st


STATUS_BADGE = {
    'FMC': ('FMC', 'badge-fmc', 'military-card-fmc'),
    'PMC': ('PMC', 'badge-pmc', 'military-card-pmc'),
    'NMC_maintenance': ('NMC-M', 'badge-nmc', 'military-card-nmc'),
    'NMC_parts': ('PAM', 'badge-pam', 'military-card-pam'),
    'NMC_depot': ('DEPOT', 'badge-depot', 'military-card-nmc'),
    'sortie': ('SORTIE', 'badge-fmc', 'military-card-fmc'),
}


def _health_bar(value, label):
    """Generate HTML for a small health bar."""
    pct = max(0, min(100, int(value * 100)))
    if pct >= 70:
        fill_class = 'health-fill-good'
    elif pct >= 40:
        fill_class = 'health-fill-warn'
    else:
        fill_class = 'health-fill-crit'
    return (
        f'<div style="display:flex;align-items:center;gap:4px;">'
        f'<span style="font-size:0.6rem;color:#7A9CC0;width:24px;">{label}</span>'
        f'<div class="health-bar" style="flex:1;">'
        f'<div class="health-fill {fill_class}" style="width:{pct}%;"></div>'
        f'</div>'
        f'<span style="font-size:0.6rem;color:#7A9CC0;width:24px;">{pct}%</span>'
        f'</div>'
    )


def render_fleet_matrix(fleet):
    """
    Render the 3×4 fleet status matrix as HTML cards.

    Parameters
    ----------
    fleet : list
        List of Aircraft objects from simulation.
    """
    st.markdown("#### FLEET STATUS MATRIX")

    cards_html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;">'

    for ac in fleet:
        status = ac.status
        badge_label, badge_class, card_class = STATUS_BADGE.get(
            status, ('UNK', 'badge-nmc', 'military-card-nmc'))

        eng_h = ac.subs['engine'].health
        avi_h = ac.subs['avionics'].health
        hyd_h = ac.subs['hydraulics'].health
        afr_h = ac.subs['airframe'].health

        cards_html += (
            f'<div class="military-card {card_class}" style="padding:10px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="font-family:monospace;font-size:0.9rem;font-weight:bold;color:#E0E8FF;">'
            f'AC-{ac.id:02d}'
            f'</span>'
            f'<span class="status-badge {badge_class}">{badge_label}</span>'
            f'</div>'
            f'<div style="margin-top:6px;">'
            f'{_health_bar(eng_h, "ENG")}'
            f'{_health_bar(avi_h, "AVI")}'
            f'{_health_bar(hyd_h, "HYD")}'
            f'{_health_bar(afr_h, "AFR")}'
            f'</div>'
            f'<div style="display:flex;justify-content:space-between;margin-top:6px;'
            f'font-size:0.65rem;color:#7A9CC0;">'
            f'<span>{ac.hours:.0f} FH</span>'
            f'<span>{ac.sorties} SORTIES</span>'
            f'</div>'
            f'</div>'
        )

    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)


def render_maintenance_pipeline(result):
    """Render maintenance bay status panels."""
    st.markdown("#### MAINTENANCE PIPELINE")
    c1, c2, c3 = st.columns(3)

    maint_log = result.get('maint_log', [])
    o_count = sum(1 for e in maint_log if e['tier'] == 'O')
    i_count = sum(1 for e in maint_log if e['tier'] == 'I')
    d_count = sum(1 for e in maint_log if e['tier'] == 'D')

    for col, tier, label, count, color in [
        (c1, 'O', 'O-LEVEL (SQUADRON)', o_count, '#2060A0'),
        (c2, 'I', 'I-LEVEL (WORKSHOP)', i_count, '#A06020'),
        (c3, 'D', 'DEPOT (OVERHAUL)', d_count, '#A02020'),
    ]:
        with col:
            avg_time = 0
            tier_events = [e for e in maint_log if e['tier'] == tier]
            if tier_events:
                avg_time = sum(e['down'] for e in tier_events) / len(tier_events)
            st.markdown(f"""
<div class="military-card" style="border-left:4px solid {color};">
    <div style="color:#7A9CC0;font-size:0.7rem;letter-spacing:1px;">{label}</div>
    <div style="font-family:monospace;font-size:1.4rem;color:#E0E8FF;margin:4px 0;">
        {count} REPAIRS
    </div>
    <div style="color:#7A9CC0;font-size:0.65rem;">
        Mean downtime: {avg_time:.1f} hrs
    </div>
</div>
""", unsafe_allow_html=True)


def render_parts_status(result):
    """Render parts warehouse status."""
    st.markdown("#### PARTS WAREHOUSE STATUS")
    parts = {'engine': 'ENGINE', 'avionics': 'AVIONICS',
             'hydraulics': 'HYDRAULICS', 'airframe': 'AIRFRAME'}
    cols = st.columns(4)

    stock_df = result.get('stock_df', None)
    for col, (name, label) in zip(cols, parts.items()):
        with col:
            final_stock = 0
            if stock_df is not None and len(stock_df) > 0 and name in stock_df.columns:
                final_stock = int(stock_df[name].iloc[-1])
            from simulation.engine import INVENTORY_PARAMS
            r = INVENTORY_PARAMS[name]['r']
            color = '#00FF88' if final_stock > r else ('#FFB800' if final_stock > 0 else '#FF3B3B')
            st.markdown(f"""
<div class="military-card" style="text-align:center;">
    <div style="color:#7A9CC0;font-size:0.65rem;letter-spacing:1px;">{label}</div>
    <div style="font-family:monospace;font-size:1.8rem;color:{color};
                text-shadow:0 0 10px {color};margin:4px 0;">
        {final_stock}
    </div>
    <div style="color:#7A9CC0;font-size:0.6rem;">
        Reorder at: {r}
    </div>
</div>
""", unsafe_allow_html=True)
