Of course. You've hit the exact limitations of the current system. My apologies that the error-fixing loop wasn't robust enough. Let's implement a major upgrade to address all three of your points:

1.  **Robust Error Fixing:** We will give the agent more context so it can make better fixes.
2.  **Greatly Improved Memory & Context:** We will overhaul the prompts to force the agent to prioritize conversation history, making it much better at follow-ups.
3.  **Proactive "Smart Follow-ups":** After every successful answer, the agent will now analyze the result and suggest 2-3 logical next questions for you to ask, making the interaction feel truly intelligent and guided.

This is a significant architectural enhancement. Here are the step-by-step changes.

---

### 1. `config.py` (Major Prompt Overhaul)

This is the most critical part. We are making the prompts much more sophisticated to guide the LLM's behavior more precisely.

**Action:** Replace the entire content of `config.py` with this new, enhanced version.

```python
# config.py

# --- LLM and Agent Settings ---
LLM_MODEL = "llama3-70b-8192"
MAX_TOKENS = 2048
TEMPERATURE = 0.0

# --- System Prompts ---

ROUTER_PROMPT = """
You are an expert AI agent router. Classify the user's intent into one of the following tools:
- `sql_generator`: For questions about the data, calculations, filtering, or plotting. This is the default.
- `general_greeting`: For simple hellos, thank yous, etc.
Respond with a single JSON object: {"tool": "tool_name", "prompt": "user's original prompt"}
"""

# ENHANCED: Now heavily emphasizes chat history for better memory.
SQL_GENERATOR_PROMPT = """
You are an expert DuckDB SQL assistant. Your primary goal is to generate a single, executable DuckDB SQL query to answer the user's question.

**CRITICAL INSTRUCTIONS:**
1.  **YOU MUST USE THE CONVERSATION HISTORY** to understand the current context. Look for previously applied filters, mentioned entities, or follow-up questions.
2.  The table name is `{table_name}`. The schema is: `{schema}`.
3.  Generate only the SQL query. No explanations.

**Conversation History:**
{chat_history}

**User's Current Question:** "{user_prompt}"

Based on all the above, generate the SQL query now.
"""

ERROR_ANALYZER_PROMPT = """
You are an expert SQL error analyst. A query has failed. Your task is to diagnose the root cause and propose concrete, actionable solutions.

**Schema:** {schema}
**Failed Query:**
```sql
{query}
```
**Error Message:** `{error}`

Analyze the error and the query. Respond with a JSON list of suggestion objects. Each object must have:
1.  `"description"`: A user-friendly explanation of the proposed action.
2.  `"strategy"`: A machine-readable keyword. Use one of: `RECAST_COLUMN_AS_NUMERIC`, `RECAST_COLUMN_AS_DATE`, `ASK_USER_CLARIFICATION`, `REWRITE_SYNTAX`.
3.  `"details"`: A dictionary with necessary context, like the column name.

Example for a data type error:
[
    {{"description": "The 'price' column seems to be text. Should I try to treat it as a number by removing symbols like '$'?", "strategy": "RECAST_COLUMN_AS_NUMERIC", "details": {{"column": "price"}} }}
]
Provide only the JSON list in your response.
"""

# ENHANCED: Now gets the failed query for better context on what to fix.
QUERY_REFINER_PROMPT = """
You are an expert DuckDB SQL assistant. A previous query failed, and the user has chosen a solution. Your task is to regenerate the query correctly.

**User's Original Goal:** "{user_prompt}"
**The Query That Failed:**
```sql
{failed_query}
```
**Chosen Solution to Apply:**
- **Strategy:** `{strategy}`
- **Details:** `{details}`

**Table Schema:** {schema}
**Table Name:** {table_name}

Based on the user's goal and their chosen solution, generate a new, single, executable DuckDB SQL query.
- For `RECAST_COLUMN_AS_NUMERIC`, use `CAST(REGEXP_REPLACE(column, '[^0-9.]', '', 'g') AS REAL)` to aggressively clean and convert the specified column.
- For `REWRITE_SYNTAX`, fix the syntax of the failed query to achieve the user's goal.

Generate only the final SQL query.
"""

# ENHANCED: Gets the query for better context, leading to better verbal explanations.
RESULTS_INTERPRETER_PROMPT = """
You are an insight generator. Your goal is to provide a concise, natural language answer based on a data query result.

**Original Question:** "{user_prompt}"
**The SQL Query Used:**
```sql
{sql_query}
```
**Data Result:**
```
{data_result}
```

Based on the data, provide a clear, one or two-sentence summary that directly answers the question. Start with a direct statement, not "The data shows...".
"""

# NEW: The prompt for generating proactive "Smart Follow-ups"
FOLLOW_UP_SUGGESTER_PROMPT = """
You are a proactive data analyst. Based on the user's last question and the result, your goal is to suggest 2-3 logical and insightful follow-up questions.

**User's Last Question:** "{user_prompt}"
**Data Result:**
```
{data_result}
```

Think about what the next logical steps in an analysis would be. Examples:
- If the user asked for an average, suggest looking at the median or distribution.
- If the user looked at top categories, suggest a deep dive into the top one.
- If the user got a total, suggest breaking it down by a dimension (like region or time).

Respond with a JSON list of simple, clear follow-up questions.
Example format:
["What is the sales trend over time?", "Which sub-category is most profitable?"]
"""
```

---

### 2. `agent.py` (Adding New Capabilities)

We'll add the new `suggest_follow_ups` method and update the signatures of the other methods to pass more context.

**Action:** Replace the content of `agent.py` with this.

```python
# agent.py
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import json
import streamlit as st
from config import (
    LLM_MODEL, MAX_TOKENS, TEMPERATURE, ROUTER_PROMPT,
    SQL_GENERATOR_PROMPT, SQL_FIXER_PROMPT, CHART_SUGGESTER_PROMPT,
    RESULTS_INTERPRETER_PROMPT, ERROR_ANALYZER_PROMPT,
    QUERY_REFINER_PROMPT, FOLLOW_UP_SUGGESTER_PROMPT # New
)

class Agent:
    def __init__(self):
        self.llm = ChatGroq(
            model=LLM_MODEL, temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
            api_key=st.secrets["GROQ_API_KEY"]
        )

    def invoke_llm(self, messages):
        try:
            return self.llm.invoke(messages)
        except Exception as e:
            st.error(f"LLM call failed: {e}")
            return None

    def route_request(self, user_prompt: str):
        # ... (this method remains unchanged) ...
        messages = [SystemMessage(content=ROUTER_PROMPT), HumanMessage(content=user_prompt)]
        response = self.invoke_llm(messages)
        if response:
            try: return json.loads(response.content)
            except json.JSONDecodeError: return {"tool": "sql_generator", "prompt": user_prompt}
        return None

    def generate_sql(self, user_prompt: str, schema: str, table_name: str, chat_history: list):
        # ... (this method remains unchanged, but relies on the improved prompt) ...
        history_str = "\n".join([f'{msg["role"]}: {msg.get("content") or msg.get("sql", "")}' for msg in chat_history])
        prompt = SQL_GENERATOR_PROMPT.format(
            schema=schema, table_name=table_name, chat_history=history_str, user_prompt=user_prompt
        )
        messages = [SystemMessage(content=prompt)]
        response = self.invoke_llm(messages)
        if response: return response.content.strip().replace("```sql", "").replace("```", "").strip()
        return None

    def analyze_error(self, query: str, error: str, schema: str):
        # ... (this method remains unchanged) ...
        prompt = ERROR_ANALYZER_PROMPT.format(schema=schema, query=query, error=error)
        messages = [SystemMessage(content=prompt)]
        response = self.invoke_llm(messages)
        if response:
            try: return json.loads(response.content.strip().replace("```json", "").replace("```", ""))
            except json.JSONDecodeError: return []
        return []

    # MODIFIED: Now accepts 'failed_query' for better context
    def regenerate_query_with_solution(self, user_prompt, failed_query, solution, schema, table_name):
        """Regenerates a SQL query based on the user's chosen solution."""
        prompt = QUERY_REFINER_PROMPT.format(
            user_prompt=user_prompt, failed_query=failed_query,
            strategy=solution['strategy'], details=solution['details'],
            schema=schema, table_name=table_name
        )
        messages = [SystemMessage(content=prompt)]
        response = self.invoke_llm(messages)
        if response: return response.content.strip().replace("```sql", "").replace("```", "").strip()
        return None

    # MODIFIED: Now accepts 'sql_query' for better context
    def interpret_results(self, user_prompt: str, sql_query: str, result_df):
        """Generates a natural language summary of the query result."""
        if result_df is None or result_df.empty:
            return "The query executed successfully but returned no results."
        prompt = RESULTS_INTERPRETER_PROMPT.format(
            user_prompt=user_prompt, sql_query=sql_query, data_result=result_df.head().to_string(index=False)
        )
        messages = [SystemMessage(content=prompt)]
        response = self.invoke_llm(messages)
        if response: return response.content
        return "I retrieved the data but could not summarize it."

    def suggest_charts(self, df):
        # ... (this method remains unchanged) ...
        if df is None or df.empty: return []
        prompt = CHART_SUGGESTER_PROMPT.format(columns=list(df.columns), data_sample=df.head().to_string())
        messages = [SystemMessage(content=prompt)]
        response = self.invoke_llm(messages)
        if response:
            try: return json.loads(response.content)
            except json.JSONDecodeError: return []
        return []

    # NEW: Method to generate smart follow-up questions
    def suggest_follow_ups(self, user_prompt, result_df):
        """Suggests follow-up questions based on the results."""
        if result_df is None or result_df.empty: return []
        prompt = FOLLOW_UP_SUGGESTER_PROMPT.format(
            user_prompt=user_prompt, data_result=result_df.head(5).to_string()
        )
        messages = [SystemMessage(content=prompt)]
        response = self.invoke_llm(messages)
        if response:
            try: return json.loads(response.content.strip())
            except json.JSONDecodeError: return []
        return []
```

---

### 3. `ui_components.py` (Adding the Follow-up Buttons)

We need to render the new follow-up suggestions as clickable buttons.

**Action:** Replace the content of `ui_components.py` with this.

```python
# ui_components.py
import streamlit as st
import pandas as pd
from ydata_profiling import ProfileReport
from streamlit_pandas_profiling import st_profile_report
import plotly.express as px

# ... (initial_setup and file_uploader_and_profiling functions remain the same) ...
def initial_setup():
    st.set_page_config(page_title="Proactive AI Data Agent", layout="wide")
    if "agent" not in st.session_state: st.session_state.agent = None
    if "data_manager" not in st.session_state: st.session_state.data_manager = None
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    if 'df_states' not in st.session_state: st.session_state.df_states = []
    if 'current_df_index' not in st.session_state: st.session_state.current_df_index = -1
    if "user_choice" not in st.session_state: st.session_state.user_choice = None
    if "active_chart" not in st.session_state: st.session_state.active_chart = None
    if "profiled" not in st.session_state: st.session_state.profiled = False
    if "queued_prompt" not in st.session_state: st.session_state.queued_prompt = None

def display_chat_history():
    """Displays the conversation history, including interactive elements."""
    for i, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            if "content" in message: st.markdown(message["content"])
            if "sql" in message: st.code(message["sql"], language="sql")
            if "dataframe" in message: st.dataframe(message["dataframe"])
            
            if "error_suggestions" in message:
                st.error(message["error_message"])
                for j, suggestion in enumerate(message["error_suggestions"]):
                    if st.button(suggestion["description"], key=f"suggestion_{i}_{j}"):
                        st.session_state.user_choice = {"message_index": i, "suggestion": suggestion, "failed_query": message["failed_query"]}
                        st.rerun()

            if "charts" in message and message["charts"]: render_chart_suggestions(message["charts"], message["chart_df"], i)
            
            # NEW: Render follow-up suggestions as buttons
            if "follow_ups" in message and message["follow_ups"]:
                st.markdown("**Suggested follow-up questions:**")
                cols = st.columns(len(message["follow_ups"]))
                for j, question in enumerate(message["follow_ups"]):
                    with cols[j]:
                        if st.button(question, key=f"follow_up_{i}_{j}"):
                            # Set the prompt in session state and rerun to process it
                            st.session_state.queued_prompt = question
                            st.rerun()

def file_uploader_and_profiling(data_manager):
    uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if uploaded_file:
        if not st.session_state.get("file_id") == uploaded_file.id:
            st.session_state.profiled = False
            st.session_state.file_id = uploaded_file.id
        
        if not st.session_state.profiled:
            with st.spinner("Loading data and generating profile..."):
                success, error = data_manager.load_data(uploaded_file)
                if success:
                    st.sidebar.success("File Loaded Successfully!")
                    with st.expander("📊 View Data Profile Report", expanded=False):
                        pr = ProfileReport(data_manager.get_current_df(), title="Data Profile")
                        st_profile_report(pr)
                    st.session_state.profiled = True
                else:
                    st.sidebar.error(f"Error: {error}")
    return uploaded_file is not None

# ... (render_chart_suggestions and render_plotly_chart functions remain the same) ...
def render_chart_suggestions(suggestions, df, message_index):
    st.write("Here are some suggested charts:")
    if not suggestions: return
    num_cols = min(len(suggestions), 4)
    cols = st.columns(num_cols)
    for idx, suggestion in enumerate(suggestions):
        with cols[idx % num_cols]:
            if st.button(suggestion.get("title", f"Chart {idx+1}"), key=f"chart_btn_{message_index}_{idx}"):
                st.session_state.active_chart = {"suggestion": suggestion, "df": df}
    if st.session_state.active_chart: render_plotly_chart(st.session_state.active_chart["suggestion"], st.session_state.active_chart["df"])

def render_plotly_chart(suggestion, df):
    try:
        st.subheader(suggestion.get("title", "Chart"))
        fig_func = getattr(px, suggestion.get("type", "bar"))
        fig = fig_func(df, x=suggestion.get("x"), y=suggestion.get("y"))
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to create chart '{suggestion.get('title')}': {e}")```

---

### 4. `main_app.py` (Orchestrating the New Flow)

This is the final step, where we wire everything together.

**Action:** Replace the content of your main app file with this.

```python
# main_app.py or main.py
import streamlit as st
from agent import Agent
from data_manager import DataManager
from ui_components import initial_setup, display_chat_history, file_uploader_and_profiling

def process_prompt(user_prompt: str, agent: Agent, data_manager: DataManager):
    """Handles the logic for processing a user prompt."""
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"): st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            routed_request = agent.route_request(user_prompt)
            tool = routed_request.get("tool", "sql_generator")

            if tool == "sql_generator":
                schema = data_manager.get_schema_string()
                query = agent.generate_sql(user_prompt, schema, data_manager.table_name, st.session_state.chat_history)
                
                if not query:
                    response = {"role": "assistant", "content": "Sorry, I couldn't generate a SQL query for that."}
                else:
                    result_df, error = data_manager.execute_query(query)
                    if error:
                        suggestions = agent.analyze_error(query, error, schema)
                        if suggestions:
                            response = {"role": "assistant", "content": "I encountered an issue. Here are some options:",
                                        "error_message": f"Error: {error}", "error_suggestions": suggestions, "failed_query": query}
                        else:
                            response = {"role": "assistant", "content": f"Query failed with an unrecoverable error: {error}", "sql": query}
                    else:
                        summary = agent.interpret_results(user_prompt, query, result_df)
                        charts = agent.suggest_charts(result_df)
                        follow_ups = agent.suggest_follow_ups(user_prompt, result_df)
                        response = {"role": "assistant", "content": summary, "dataframe": result_df, "sql": query,
                                    "charts": charts, "chart_df": result_df, "follow_ups": follow_ups}
            else: # General greeting
                response = {"role": "assistant", "content": "Hello! How can I help you with your data today?"}

            st.session_state.chat_history.append(response)

def main():
    initial_setup()

    st.title("🚀 Proactive AI Data Agent")
    st.write("With robust memory, smarter error fixing, and proactive follow-up suggestions.")

    if st.session_state.agent is None:
        try: st.session_state.agent = Agent()
        except Exception: st.error("Please provide your GROQ_API_KEY in .streamlit/secrets.toml") ; st.stop()
    if st.session_state.data_manager is None: st.session_state.data_manager = DataManager()
    
    agent = st.session_state.agent
    data_manager = st.session_state.data_manager

    with st.sidebar:
        st.header("Controls")
        file_loaded = file_uploader_and_profiling(data_manager)
        if file_loaded:
            if st.button("Undo", disabled=(st.session_state.current_df_index <= 0)): data_manager.undo()
            if st.button("Redo", disabled=(st.session_state.current_df_index >= len(st.session_state.df_states) - 1)): data_manager.redo()

    if not file_loaded: st.info("Please upload a CSV or Excel file in the sidebar to begin.") ; st.stop()
        
    st.dataframe(data_manager.get_current_df())

    # --- Handle user's choice from an error suggestion ---
    if st.session_state.user_choice:
        choice = st.session_state.user_choice
        st.session_state.user_choice = None
        
        original_prompt = next((msg["content"] for msg in reversed(st.session_state.chat_history) if msg["role"] == "user"), None)
        
        if original_prompt:
            with st.chat_message("assistant"):
                with st.spinner("Applying solution and retrying..."):
                    schema = data_manager.get_schema_string()
                    new_query = agent.regenerate_query_with_solution(
                        original_prompt, choice["failed_query"], choice["suggestion"], schema, data_manager.table_name
                    )
                    if new_query:
                        result_df, error = data_manager.execute_query(new_query)
                        if error:
                            response = {"role": "assistant", "content": f"The fix also failed. Error: {error}", "sql": new_query}
                        else:
                            summary = agent.interpret_results(original_prompt, new_query, result_df)
                            charts = agent.suggest_charts(result_df)
                            follow_ups = agent.suggest_follow_ups(original_prompt, result_df)
                            response = {"role": "assistant", "content": summary, "dataframe": result_df, "sql": new_query,
                                        "charts": charts, "chart_df": result_df, "follow_ups": follow_ups}
                    else:
                        response = {"role": "assistant", "content": "I wasn't able to apply the fix successfully."}
                    st.session_state.chat_history.append(response)
        st.rerun()

    display_chat_history()

    # --- Handle user input (from text box or follow-up buttons) ---
    prompt_to_process = None
    if st.session_state.queued_prompt:
        prompt_to_process = st.session_state.queued_prompt
        st.session_state.queued_prompt = None
    elif user_prompt := st.chat_input("Ask a question about your data..."):
        prompt_to_process = user_prompt

    if prompt_to_process:
        process_prompt(prompt_to_process, agent, data_manager)
        st.rerun()

if __name__ == "__main__":
    main()
```

### Relaunch and Test

Save all the files and restart your Streamlit app. You should now experience a significantly more intelligent agent:

1.  **Test Memory:** Ask a question like "show me sales by country." Then, in the next turn, ask "just for the top 3." The agent should now correctly generate a `...ORDER BY ... LIMIT 3` query.
2.  **Test Error Fixing:** Upload a file where a number column is stored as text (e.g., "$1,234.56"). Ask for the "average price." The agent should fail, then offer to clean and recast the column. When you click the suggestion, it should succeed.
3.  **Test Follow-ups:** After any successful query, you will now see 2-3 blue buttons with suggested next questions. Clicking one will automatically run that query for you.