# ui_components.py
import streamlit as st
import pandas as pd
from ydata_profiling import ProfileReport
import plotly.express as px

def initial_setup():
    st.set_page_config(page_title="Smart Router AI Agent", layout="wide")
    for key in ["agent", "data_manager", "chat_history", "df_states", "current_df_index", "user_choice", "active_chart", "profiled", "file_id", "queued_prompt"]:
        if key not in st.session_state:
            st.session_state[key] = None if key not in ["chat_history", "df_states"] else []
            if key == "current_df_index": st.session_state[key] = -1

def display_chat_history():
    """Displays all messages, and now renders charts from history."""
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

# --- CRITICAL FIX: The plotting function is now much more robust ---
def render_plotly_chart(chart_params, df):
    """
    Renders a Plotly chart by inferring axes from the dataframe, not the router's guess.
    """
    st.markdown("---")
    chart_type = chart_params.get("chart_type", "bar") # Default to bar chart if type is missing

    # Heuristic: For a 2-column dataframe, the first is X and the second is Y.
    # This is more reliable than trusting the LLM's parameter extraction for column names.
    if df.shape[1] < 2:
        st.error(f"❌ Chart generation failed: The retrieved data has {df.shape[1]} column(s), but 2 are required for a chart.")
        st.dataframe(df)
        return

    # Infer column names directly from the data that was successfully queried.
    x = df.columns[0]
    y = df.columns[1]
    
    title = f"{y.replace('_', ' ').title()} by {x.replace('_', ' ').title()}"

    try:
        st.subheader(title)
        if chart_type == "bar": fig = px.bar(df, x=x, y=y, title=title)
        elif chart_type == "pie": fig = px.pie(df, names=x, values=y, title=title)
        elif chart_type == "line": fig = px.line(df, x=x, y=y, title=title)
        elif chart_type == "scatter": fig = px.scatter(df, x=x, y=y, title=title)
        else:
            st.warning(f"⚠️ Chart type '{chart_type}' not supported. Defaulting to bar chart.")
            fig = px.bar(df, x=x, y=y, title=title)
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Failed to create chart '{title}': {e}")
