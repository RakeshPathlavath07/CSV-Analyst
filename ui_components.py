# # ui_components.py

# import streamlit as st
# import pandas as pd
# from ydata_profiling import ProfileReport
# from streamlit_pandas_profiling import st_profile_report
# import plotly.express as px
# import json
# import os

# # ======================================================
# #  INITIAL SETUP AND MEMORY MANAGEMENT
# # ======================================================

# def initial_setup():
#     """Configures the Streamlit page and initializes session state."""
#     st.set_page_config(page_title="Collaborative AI Data Agent", layout="wide")

#     # --- Initialize session state variables ---
#     default_state = {
#         "agent": None,
#         "data_manager": None,
#         "chat_history": [],
#         "df_states": [],
#         "current_df_index": -1,
#         "user_choice": None,
#         "active_chart": None,
#         "profiled": False,
#         "queued_prompt": None,
#         "recent_queries": [],
#     }

#     for key, value in default_state.items():
#         if key not in st.session_state:
#             st.session_state[key] = value

#     # --- Optional persistent chat memory ---
#     load_chat_history()


# def save_chat_history():
#     """Save chat history to a local JSON file for persistence across sessions."""
#     try:
#         if not os.path.exists("chat_logs"):
#             os.makedirs("chat_logs")

#         with open("chat_logs/chat_memory.json", "w") as f:
#             json.dump(st.session_state.chat_history, f)
#     except Exception as e:
#         st.sidebar.warning(f"⚠️ Could not save chat history: {e}")


# def load_chat_history():
#     """Load chat history from disk if available."""
#     try:
#         if os.path.exists("chat_logs/chat_memory.json"):
#             with open("chat_logs/chat_memory.json", "r") as f:
#                 st.session_state.chat_history = json.load(f)
#     except Exception:
#         st.session_state.chat_history = []


# def add_message(role, content, **kwargs):
#     """Safely add a message to chat history."""
#     message = {"role": role, "content": content}
#     message.update(kwargs)
#     st.session_state.chat_history.append(message)

#     # Keep only recent 15 messages to manage token length
#     st.session_state.chat_history = st.session_state.chat_history[-15:]

#     save_chat_history()


# # ======================================================
# #  CHAT DISPLAY AND INTERACTIONS
# # ======================================================

# def display_chat_history():
#     """Displays all messages, SQL, data, and error/follow-up suggestions."""
#     for i, message in enumerate(st.session_state.chat_history):
#         with st.chat_message(message["role"]):
            
#             # --- Display main content ---
#             if message.get("content"):
#                 st.markdown(message["content"])

#             if message.get("sql"):
#                 st.code(message["sql"], language="sql")

#             if isinstance(message.get("dataframe"), pd.DataFrame):
#                 st.dataframe(message["dataframe"])

#             # --- Display SQL error and fix suggestions ---
#             if message.get("error_suggestions"):
#                 st.error(message.get("error_message", "An error occurred."))
#                 for j, suggestion in enumerate(message["error_suggestions"]):
#                     button_key = f"suggestion_{i}_{j}"
#                     desc = suggestion.get("description", "Fix suggestion")
#                     conf = suggestion.get("confidence", None)

#                     # Optional confidence display
#                     label = f"{desc} ({round(conf*100,1)}% confident)" if conf else desc

#                     if st.button(label, key=button_key):
#                         st.session_state.user_choice = {
#                             "message_index": i,
#                             "suggestion": suggestion,
#                         }
#                         st.rerun()

#             # --- Chart Suggestions ---
#             if message.get("charts"):
#                 render_chart_suggestions(message["charts"], message.get("chart_df"), message_index=i)

#             # --- Follow-up Questions ---
#             if message.get("follow_ups"):
#                 st.markdown("**💡 Suggested follow-up questions:**")
#                 cols = st.columns(len(message["follow_ups"]))
#                 for j, question in enumerate(message["follow_ups"]):
#                     with cols[j]:
#                         if st.button(question, key=f"follow_up_{i}_{j}"):
#                             st.session_state.queued_prompt = question
#                             st.rerun()


# # ======================================================
# #  FILE UPLOAD & PROFILING
# # ======================================================

# def file_uploader_and_profiling(data_manager):
#     """Handles file upload, loads data, and generates profiling report."""
#     uploaded_file = st.sidebar.file_uploader("📁 Upload CSV or Excel", type=["csv", "xlsx"])

#     if uploaded_file:
#         st.session_state.profiled = False
#         with st.spinner("🔍 Loading and profiling data..."):
#             success, error = data_manager.load_data(uploaded_file)
#             if success:
#                 st.sidebar.success("✅ File loaded successfully!")

#                 df = data_manager.get_current_df()
#                 if not st.session_state.profiled:
#                     with st.expander("📊 View Data Profile Report", expanded=True):
#                         pr = ProfileReport(df, title="Data Profile", explorative=True)
#                         st_profile_report(pr)
#                     st.session_state.profiled = True
#             else:
#                 st.sidebar.error(f"❌ Error loading file: {error}")

#     return uploaded_file is not None and uploaded_file is not False


# # ======================================================
# #  CHART SUGGESTIONS & PLOTTING
# # ======================================================

# def render_chart_suggestions(suggestions, df, message_index):
#     """Renders chart suggestion buttons."""
#     if not suggestions:
#         return

#     st.write("📈 **Suggested Charts:**")
#     num_cols = min(len(suggestions), 4)
#     cols = st.columns(num_cols)

#     for idx, suggestion in enumerate(suggestions):
#         with cols[idx % num_cols]:
#             button_key = f"chart_btn_{message_index}_{idx}"
#             title = suggestion.get("title", f"Chart {idx+1}")
#             if st.button(title, key=button_key):
#                 st.session_state.active_chart = {"suggestion": suggestion, "df": df}

#     if st.session_state.active_chart:
#         render_plotly_chart(
#             st.session_state.active_chart["suggestion"],
#             st.session_state.active_chart["df"]
#         )


# def render_plotly_chart(suggestion, df):
#     """Safely renders the Plotly chart based on suggestion."""
#     if df is None or df.empty:
#         st.warning("⚠️ No data available for chart rendering.")
#         return

#     chart_type = suggestion.get("type")
#     x = suggestion.get("x")
#     y = suggestion.get("y")

#     if not all([chart_type, x, y]):
#         st.error("❌ Missing fields (type, x, y) in chart suggestion.")
#         return

#     try:
#         st.subheader(suggestion.get("title", "Chart"))
#         if chart_type == "bar":
#             fig = px.bar(df, x=x, y=y)
#         elif chart_type == "pie":
#             fig = px.pie(df, names=x, values=y)
#         elif chart_type == "line":
#             fig = px.line(df, x=x, y=y)
#         elif chart_type == "scatter":
#             fig = px.scatter(df, x=x, y=y)
#         else:
#             st.warning(f"⚠️ Chart type '{chart_type}' not supported yet.")
#             return

#         st.plotly_chart(fig, use_container_width=True)

#     except Exception as e:
#         st.error(f"❌ Failed to create chart '{suggestion.get('title', 'Chart')}': {e}")

# ui_components.py
import streamlit as st
import pandas as pd
from ydata_profiling import ProfileReport
from streamlit_pandas_profiling import st_profile_report
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
                        st_profile_report(pr)
                    st.session_state.profiled = True
                else:
                    st.sidebar.error(f"❌ Error loading file: {error}")
    # --- CRITICAL FIX: Corrected the variable name typo ---
    return uploaded_file is not None

def render_plotly_chart(chart_params, df):
    """Renders a Plotly chart based on the parameters from the smart router."""
    st.markdown("---")
    chart_type = chart_params.get("chart_type")
    x = chart_params.get("x_axis")
    y = chart_params.get("y_axis")
    title = f"{y} by {x}".title()

    if not all([chart_type, x, y]):
        st.error(f"❌ Chart generation failed: Missing parameters. Received: {chart_params}")
        return
    
    if x not in df.columns or y not in df.columns:
        st.error(f"❌ Chart generation failed: Columns '{x}' or '{y}' not found. Available: {list(df.columns)}")
        return

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