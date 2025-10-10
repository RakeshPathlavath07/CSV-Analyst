# ui_components.py
import streamlit as st
import pandas as pd
from ydata_profiling import ProfileReport
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def initial_setup():
    st.set_page_config(page_title="Advanced AI Visualizer", layout="wide")
    for key in ["agent", "data_manager", "chat_history", "df_states", "current_df_index", "user_choice", "active_chart", "profiled", "file_id", "queued_prompt"]:
        if key not in st.session_state:
            st.session_state[key] = None if key not in ["chat_history", "df_states"] else []
            if key == "current_df_index": st.session_state[key] = -1

def display_chat_history():
    """Displays all messages, and renders charts from history."""
    for i, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            if message.get("content"): st.markdown(message["content"])
            if message.get("sql"):
                with st.expander("View SQL Query"):
                    st.code(message["sql"], language="sql")
            
            if message.get("chart_params") and isinstance(message.get("chart_df"), pd.DataFrame):
                render_plotly_chart(message["chart_params"], message["chart_df"])

            elif isinstance(message.get("dataframe"), pd.DataFrame):
                st.dataframe(message["dataframe"])

            if message.get("error_suggestions"):
                st.error(message.get("error_message", "An error occurred."))
                for j, suggestion in enumerate(message["error_suggestions"]):
                    if st.button(suggestion.get("description"), key=f"suggestion_{i}_{j}"):
                        st.session_state.user_choice = {"suggestion": suggestion, "failed_query": message.get("failed_query")}
                        st.rerun()

def file_uploader_and_profiling(data_manager):
    uploaded_file = st.sidebar.file_uploader("📁 Upload CSV or Excel", type=["csv", "xlsx"])
    if uploaded_file:
        if st.session_state.get("file_id") != uploaded_file.file_id:
            st.session_state.profiled = False
            st.session_state.file_id = uploaded_file.file_id
        if not st.session_state.profiled:
            with st.spinner("🔍 Loading and profiling data..."):
                success, error = data_manager.load_data(uploaded_file)
                if success:
                    st.sidebar.success("✅ File loaded successfully!")
                    with st.expander("📊 View Data Profile Report"):
                        pr = ProfileReport(data_manager.get_current_df(), title="Data Profile")
                        st.components.v1.html(pr.to_html(), height=600, scrolling=True)
                    st.session_state.profiled = True
                else:
                    st.sidebar.error(f"❌ Error loading file: {error}")
    return uploaded_file is not None

# --- CRITICAL FIX: The plotting logic is now corrected ---
def render_plotly_chart(chart_params, df):
    """
    Renders complex, multi-series, and combination Plotly charts with corrected logic.
    """
    st.markdown("---")
    
    primary_chart_type = chart_params.get("chart_type", "bar")
    x = chart_params.get("x_axis")
    y_axes = chart_params.get("y_axis", [])
    
    if not isinstance(y_axes, list): y_axes = [y_axes]

    # --- Safety Checks ---
    if not all([x, y_axes]): st.error("❌ Chart failed: Missing x_axis or y_axis parameters."); return
    all_cols = [x] + y_axes
    if "secondary_y_axis" in chart_params: all_cols.append(chart_params["secondary_y_axis"])
    for col in all_cols:
        if col not in df.columns:
            st.error(f"❌ Chart failed: Column '{col}' not found. Available: {list(df.columns)}"); return

    # --- Figure Initialization ---
    has_secondary_axis = "secondary_y_axis" in chart_params
    if has_secondary_axis:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
    else:
        fig = go.Figure()

    # --- Plot Primary Y-Axes ---
    # This loop no longer uses the 'secondary_y' argument, fixing the bug.
    for y_col in y_axes:
        if primary_chart_type == "bar":
            fig.add_trace(go.Bar(x=df[x], y=df[y_col], name=y_col))
        elif primary_chart_type == "line":
            fig.add_trace(go.Scatter(x=df[x], y=df[y_col], mode='lines+markers', name=y_col))
        elif primary_chart_type == "scatter":
            fig.add_trace(go.Scatter(x=df[x], y=df[y_col], mode='markers', name=y_col))

    # --- Plot Secondary Y-Axis (if applicable) ---
    # This is the ONLY place where secondary_y=True is used, which is correct.
    if has_secondary_axis:
        sec_y = chart_params["secondary_y_axis"]
        sec_type = chart_params.get("secondary_chart_type", "line")
        
        if sec_type == "line":
            fig.add_trace(go.Scatter(x=df[x], y=df[sec_y], name=f"{sec_y} (right axis)", mode='lines'), secondary_y=True)
        elif sec_type == "bar":
            fig.add_trace(go.Bar(x=df[x], y=df[sec_y], name=f"{sec_y} (right axis)"), secondary_y=True)
        
        fig.update_yaxes(title_text=sec_y.replace("_", " ").title(), secondary_y=True)

    # --- Final Touches and Rendering ---
        # --- Final Touches and Rendering ---
    title = f"{', '.join(y_axes).title()} vs. {x.title()}"
    fig.update_layout(title_text=title, legend_title_text="Metrics")
    fig.update_xaxes(title_text=x.replace("_", " ").title())
    if has_secondary_axis:
        fig.update_yaxes(title_text=", ".join(y_axes).replace("_", " ").title(), secondary_y=False)
    else:
        fig.update_yaxes(title_text=", ".join(y_axes).replace("_", " ").title())

    st.subheader(title)
    st.plotly_chart(fig, use_container_width=True)
