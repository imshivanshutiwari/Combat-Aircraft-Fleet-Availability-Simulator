import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from components.gauge_charts import get_dark_template
from simulation.optimizer import optimize_staffing

def render_optimization_tab(sim_params):
    st.markdown("""
    <div class="military-intel">
        <h4>AI DECISION SUPPORT — OPTIMAL MANNING SOLVER</h4>
        <p>This module uses stochastic hill-climbing optimization against the live 
        fleet simulation to mathematically determine the lowest-cost technician 
        manning structure that satisfies a commander-specified target Mission Capable Rate.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### CONSTRAINTS")
        target_mcr = st.slider("Target Minimum MCR (%)", 50, 95, 75) / 100.0
        max_iters = st.number_input("Solver Iterations (Max)", 10, 100, 30)
        
        if st.button("▶ RUN AI SOLVER", key="run_opt_btn", type="primary", use_container_width=True):
            st.session_state['opt_running'] = True
            
    with col2:
        if st.session_state.get('opt_running', False):
            # Run the optimizer
            st.markdown("### SOLVER PROGRESS")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(current, total):
                progress_bar.progress(current / total)
                status_text.text(f"Iteration {current}/{total}...")
                
            opt_result = optimize_staffing(
                target_mcr, 
                sim_params, 
                max_iterations=max_iters, 
                progress_callback=update_progress
            )
            
            st.session_state['opt_result'] = opt_result
            st.session_state['opt_running'] = False
            progress_bar.empty()
            status_text.empty()
            st.rerun()
            
        elif 'opt_result' in st.session_state:
            res = st.session_state['opt_result']
            st.markdown("### OPTIMIZED MANNING STRUCTURE")
            
            if not res['success']:
                st.error("⚠️ Target MCR unreachable even at maximum facility capacity.")
            
            best = res['best_config']
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("O-Level Techs", f"{best[0]}")
            m2.metric("I-Level Techs", f"{best[1]}")
            m3.metric("Depot Slots", f"{best[2]}")
            m4.metric("Annual Cost", f"${res['best_cost']:,.0f}", delta="Minimized", delta_color="inverse")
            
            st.info(f"Achieved Simulated MCR: **{res['best_mcr']*100:.1f}%**")
            
    # History Chart
    if 'opt_result' in st.session_state:
        st.markdown("---")
        df = st.session_state['opt_result']['history']
        
        fig = go.Figure()
        
        # Add MCR trace (right axis)
        fig.add_trace(
            go.Scatter(
                x=df['iter'], y=df['mcr'] * 100,
                name='Simulated MCR',
                mode='lines+markers',
                line=dict(color='#00FF88', width=3),
                yaxis='y2'
            )
        )
        
        # Add target line
        fig.add_hline(
            y=target_mcr * 100, 
            line_dash="dash", line_color="#FFB800",
            annotation_text="Target MCR",
            yref='y2'
        )
        
        # Add Cost trace (left axis)
        fig.add_trace(
            go.Scatter(
                x=df['iter'], y=df['cost'],
                name='Total Cost ($)',
                mode='lines',
                line=dict(color='#FF3B3B', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 59, 59, 0.1)'
            )
        )
        
        layout_args = get_dark_template()
        layout_args["title"] = "SOLVER TRAJECTORY — COST VS MCR"
        layout_args["xaxis"].update({"title": "Solver Iteration"})
        layout_args["yaxis"].update({
            "title": "Annual Manpower Cost ($)",
            "titlefont": dict(color="#FF3B3B"),
            "tickfont": dict(color="#FF3B3B")
        })
        layout_args["yaxis2"] = dict(
            title="Mission Capable Rate (%)",
            titlefont=dict(color="#00FF88"),
            tickfont=dict(color="#00FF88"),
            overlaying="y",
            side="right",
            range=[40, 100]
        )
        layout_args["legend"].update(dict(x=0.01, y=0.99))
        layout_args["height"] = 400
        
        fig.update_layout(**layout_args)
        
        st.plotly_chart(fig, use_container_width=True)
