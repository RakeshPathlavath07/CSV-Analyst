# # agent.py
# from langchain_groq import ChatGroq
# from langchain_core.messages import HumanMessage, SystemMessage
# import json
# import streamlit as st
# from config import (
#     LLM_MODEL, MAX_TOKENS, TEMPERATURE, ROUTER_PROMPT,
#     SQL_GENERATOR_PROMPT, SQL_FIXER_PROMPT, CHART_SUGGESTER_PROMPT,
#     RESULTS_INTERPRETER_PROMPT, # Import the new prompt
#     ERROR_ANALYZER_PROMPT, # New
#     QUERY_REFINER_PROMPT,   # New
#     FOLLOW_UP_SUGGESTER_PROMPT
# )

# class Agent:
#     def __init__(self):
#         self.llm = ChatGroq(
#             model=LLM_MODEL,
#             temperature=TEMPERATURE,
#             max_tokens=MAX_TOKENS,
#             api_key=st.secrets["GROQ_API_KEY"]
#         )

#     def invoke_llm(self, messages):
#         """A helper to invoke the LLM and handle potential errors."""
#         try:
#             return self.llm.invoke(messages)
#         except Exception as e:
#             st.error(f"LLM call failed: {e}")
#             return None

#     def route_request(self, user_prompt: str):
#         """Classifies the user's intent and routes to the correct tool."""
#         messages = [
#             SystemMessage(content=ROUTER_PROMPT),
#             HumanMessage(content=user_prompt)
#         ]
#         response = self.invoke_llm(messages)
#         if response:
#             try:
#                 return json.loads(response.content)
#             except json.JSONDecodeError:
#                 return {"tool": "sql_generator", "prompt": user_prompt}
#         return None

#     # MODIFIED: Now accepts chat_history
#     def generate_sql(self, user_prompt: str, schema: str, table_name: str, chat_history: list):
#         """Generates a SQL query based on the user's prompt and conversation history."""
        
#         # Format chat history for the prompt
#         history_str = "\n".join([f'{msg["role"]}: {msg.get("content") or msg.get("sql", "")}' for msg in chat_history])
        
#         prompt = SQL_GENERATOR_PROMPT.format(
#             schema=schema, 
#             table_name=table_name,
#             chat_history=history_str,
#             user_prompt=user_prompt
#         )
#         messages = [SystemMessage(content=prompt)]
        
#         response = self.invoke_llm(messages)
#         if response:
#             return response.content.strip().replace("```sql", "").replace("```", "").strip()
#         return None
    
#     # NEW: Method to analyze an error and propose solutions
#     def analyze_error(self, query: str, error: str, schema: str):
#         """Analyzes a SQL error and returns structured suggestions."""
#         prompt = ERROR_ANALYZER_PROMPT.format(schema=schema, query=query, error=error)
#         messages = [SystemMessage(content=prompt)]
#         response = self.invoke_llm(messages)
#         if response:
#             try:
#                 # The response content might be wrapped in markdown, clean it
#                 clean_response = response.content.strip().replace("```json", "").replace("```", "")
#                 return json.loads(clean_response)
#             except json.JSONDecodeError:
#                 return [] # Return empty list if JSON is invalid
#         return []

#     # NEW: Method to apply a chosen solution and regenerate the query
#     def regenerate_query_with_solution(self, user_prompt, solution, schema, table_name, chat_history):
#         """Regenerates a SQL query based on the user's chosen solution."""
#         history_str = "\n".join([f'{msg["role"]}: {msg.get("content") or msg.get("sql", "")}' for msg in chat_history])
        
#         prompt = QUERY_REFINER_PROMPT.format(
#             user_prompt=user_prompt,
#             strategy=solution['strategy'],
#             details=solution['details'],
#             schema=schema,
#             table_name=table_name,
#             chat_history=history_str
#         )
#         messages = [SystemMessage(content=prompt)]
#         response = self.invoke_llm(messages)
#         if response:
#             return response.content.strip().replace("```sql", "").replace("```", "").strip()
#         return None

#     def fix_sql(self, broken_query: str, error_message: str, schema: str, table_name: str):
#         """Attempts to fix a broken SQL query."""
#         prompt = SQL_FIXER_PROMPT.format(
#             broken_query=broken_query,
#             error_message=error_message,
#             schema=schema,
#             table_name=table_name
#         )
#         messages = [SystemMessage(content=prompt)]
#         response = self.invoke_llm(messages)
#         if response:
#             return response.content.strip().replace("```sql", "").replace("```", "").strip()
#         return None

#     def suggest_charts(self, df):
#         """Suggests chart types based on the DataFrame."""
#         if df is None or df.empty:
#             return []
        
#         prompt = CHART_SUGGESTER_PROMPT.format(
#             columns=list(df.columns),
#             data_sample=df.head().to_string()
#         )
#         messages = [SystemMessage(content=prompt)]
#         response = self.invoke_llm(messages)
#         if response:
#             try:
#                 return json.loads(response.content)
#             except json.JSONDecodeError:
#                 return []
#         return []

#     # NEW: Method to generate natural language summaries from results
#     def interpret_results(self, user_prompt: str, sql_query: str, result_df):
#         """Generates a natural language summary of the query result."""
#         if result_df is None or result_df.empty:
#             return "The query executed successfully but returned no results."
#         prompt = RESULTS_INTERPRETER_PROMPT.format(
#             user_prompt=user_prompt, sql_query=sql_query, data_result=result_df.head().to_string(index=False)
#         )
#         messages = [SystemMessage(content=prompt)]
#         response = self.invoke_llm(messages)
#         if response: return response.content
#         return "I retrieved the data but could not summarize it."
    
#     def suggest_follow_ups(self, user_prompt, result_df):
#         """Suggests follow-up questions based on the results."""
#         if result_df is None or result_df.empty: return []
#         prompt = FOLLOW_UP_SUGGESTER_PROMPT.format(
#             user_prompt=user_prompt, data_result=result_df.head(5).to_string()
#         )
#         messages = [SystemMessage(content=prompt)]
#         response = self.invoke_llm(messages)
#         if response:
#             try: return json.loads(response.content.strip())
#             except json.JSONDecodeError: return []
#         return []

# agent.py
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
        prompt = DATA_FETCH_PROMPT_FOR_VIZ.format(
            chart_type=viz_params.get("chart_type"),
            x_axis=viz_params.get("x_axis"),
            y_axis=viz_params.get("y_axis"),
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