from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import json
import streamlit as st
from config import (
    LLM_MODEL, MAX_TOKENS, TEMPERATURE, ROUTER_PROMPT,
    SQL_GENERATOR_PROMPT, ERROR_ANALYZER_PROMPT, QUERY_REFINER_PROMPT,
    ANALYST_INTERPRETER_PROMPT, DATA_FETCH_PROMPT_FOR_VIZ
)

class Agent:
    def __init__(self):
        self.llm = ChatGroq(model=LLM_MODEL, temperature=TEMPERATURE, max_tokens=MAX_TOKENS, api_key=st.secrets["GROQ_API_KEY"])

    def invoke_llm(self, messages):
        try: return self.llm.invoke(messages)
        except Exception as e: st.error(f"LLM call failed: {e}"); return None

    # MODIFIED: The router now needs the schema to make better decisions
    def route_request(self, user_prompt: str, schema: str):
        """Classifies the user's intent and extracts parameters."""
        prompt_with_input = ROUTER_PROMPT.format(user_prompt=user_prompt, schema=schema)
        messages = [SystemMessage(content=prompt_with_input)]
        response = self.invoke_llm(messages)
        if response:
            try:
                # Clean the response in case of markdown fences
                clean_json = response.content.strip().replace("```json", "").replace("```", "")
                return json.loads(clean_json)
            except json.JSONDecodeError:
                # Fallback if the router fails
                return {"tool": "run_sql_query", "parameters": {"prompt": user_prompt}}
        return None

    # NEW: A dedicated method for generating the simple SQL needed for a chart
    def generate_sql_for_viz(self, viz_params: dict, schema: str, table_name: str):
        """Generates a simple SELECT query to fetch data for a visualization."""
        y_axis_list = viz_params.get("y_axis", [])
        
        # Also include the secondary y_axis in the data fetch if it exists
        if "secondary_y_axis" in viz_params:
            y_axis_list.append(viz_params["secondary_y_axis"])
            
        y_axis_str = ", ".join(y_axis_list)

        prompt = DATA_FETCH_PROMPT_FOR_VIZ.format(
            chart_type=viz_params.get("chart_type"),
            x_axis=viz_params.get("x_axis"),
            y_axis_str=y_axis_str, # Use the formatted string
            table_name=table_name,
            schema=schema
        )
        messages = [SystemMessage(content=prompt)]
        response = self.invoke_llm(messages)
        if response:
            return response.content.strip().replace("```sql", "").replace("```", "").strip()
        return None

    # --- The rest of the methods are largely the same ---
    def generate_sql(self, user_prompt: str, schema: str, table_name: str, chat_history: list):
        history_str = "\n".join([f'{msg["role"]}: {msg.get("content") or msg.get("sql", "")}' for msg in chat_history])
        prompt = SQL_GENERATOR_PROMPT.format(schema=schema, table_name=table_name, chat_history=history_str, user_prompt=user_prompt)
        messages = [SystemMessage(content=prompt)]
        response = self.invoke_llm(messages)
        if response: return response.content.strip().replace("```sql", "").replace("```", "").strip()
        return None

    def analyze_error(self, query: str, error: str, schema: str):
        prompt = ERROR_ANALYZER_PROMPT.format(schema=schema, query=query, error=error)
        messages = [SystemMessage(content=prompt)]
        response = self.invoke_llm(messages)
        if response:
            try: return json.loads(response.content.strip().replace("```json", "").replace("```", ""))
            except json.JSONDecodeError: return []
        return []

    def regenerate_query_with_solution(self, user_prompt, failed_query, solution, schema, table_name, chat_history):
        history_str = "\n".join([f'{msg["role"]}: {msg.get("content") or msg.get("sql", "")}' for msg in chat_history])
        prompt = QUERY_REFINER_PROMPT.format(
            user_prompt=user_prompt, failed_query=failed_query, strategy=solution['strategy'],
            details=solution['details'], schema=schema, table_name=table_name, chat_history=history_str
        )
        messages = [SystemMessage(content=prompt)]
        response = self.invoke_llm(messages)
        if response: return response.content.strip().replace("```sql", "").replace("```", "").strip()
        return None

    def analyze_and_summarize_results(self, user_prompt: str, result_df):
        if result_df is None or result_df.empty:
            return "The query executed successfully but returned no data."
        prompt = ANALYST_INTERPRETER_PROMPT.format(
            user_prompt=user_prompt, data_result=result_df.to_string(index=False)
        )
        messages = [SystemMessage(content=prompt)]
        response = self.invoke_llm(messages)
        if response: return response.content
        return "I retrieved the data but could not provide an analysis."
