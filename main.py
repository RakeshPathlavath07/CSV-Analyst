# import streamlit as st
# from agent import Agent
# from data_manager import DataManager
# from ui_components import initial_setup, display_chat_history, file_uploader_and_profiling

# # -----------------------------------------------------------
# # 🔧 PROCESSING USER PROMPTS (Modular Function)
# # -----------------------------------------------------------
# def process_prompt(user_prompt: str, agent: Agent, data_manager: DataManager):
#     """Handles the logic for processing a user prompt."""
#     st.session_state.chat_history.append({"role": "user", "content": user_prompt})
#     with st.chat_message("user"):
#         st.markdown(user_prompt)

#     with st.chat_message("assistant"):
#         with st.spinner("Thinking..."):
#             routed_request = agent.route_request(user_prompt)
#             tool = routed_request.get("tool", "sql_generator") if routed_request else "sql_generator"

#             # --- SQL Query Generation ---
#             if tool == "sql_generator":
#                 schema = data_manager.get_schema_string()
#                 query = agent.generate_sql(user_prompt, schema, data_manager.table_name, st.session_state.chat_history)

#                 if not query:
#                     response = {"role": "assistant", "content": "Sorry, I couldn't generate a SQL query for that."}
#                 else:
#                     result_df, error = data_manager.execute_query(query)

#                     if error:
#                         suggestions = agent.analyze_error(query, error, schema)
#                         if suggestions:
#                             response = {
#                                 "role": "assistant",
#                                 "content": "I encountered an issue with that query. Here are a few options:",
#                                 "error_message": f"Error: {error}",
#                                 "error_suggestions": suggestions
#                             }
#                         else:
#                             response = {
#                                 "role": "assistant",
#                                 "content": f"Query failed with an unrecoverable error: {error}",
#                                 "sql": query
#                             }
#                     else:
#                         summary = agent.interpret_results(user_prompt, query, result_df)
#                         charts = agent.suggest_charts(result_df)
#                         follow_ups = agent.suggest_follow_ups(user_prompt, result_df)
#                         response = {
#                             "role": "assistant",
#                             "content": summary,
#                             "dataframe": result_df,
#                             "sql": query,
#                             "charts": charts,
#                             "chart_df": result_df,
#                             "follow_ups": follow_ups
#                         }

#             # --- Non-SQL (greetings / general queries) ---
#             else:
#                 response = {"role": "assistant", "content": "Hello! How can I help you with your data today?"}

#             st.session_state.chat_history.append(response)

# # -----------------------------------------------------------
# # ⚙️ MAIN APPLICATION
# # -----------------------------------------------------------
# def main():
#     """Main function to run the Streamlit app."""
#     initial_setup()

#     st.title("🚀 Unified AI Data Agent")
#     st.write("Smarter, interactive, and proactive — with memory, clarifications, and adaptive retries.")

#     # --- Initialize Agent & Data Manager ---
#     if st.session_state.agent is None:
#         try:
#             st.session_state.agent = Agent()
#         except Exception:
#             st.error("Please provide your GROQ_API_KEY in .streamlit/secrets.toml")
#             st.stop()

#     if st.session_state.data_manager is None:
#         st.session_state.data_manager = DataManager()

#     if "user_choice" not in st.session_state:
#         st.session_state.user_choice = None

#     agent = st.session_state.agent
#     data_manager = st.session_state.data_manager

#     # --- Sidebar Controls ---
#     with st.sidebar:
#         st.header("⚙️ Controls")
#         file_loaded = file_uploader_and_profiling(data_manager)
#         if file_loaded:
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.button("Undo", disabled=(st.session_state.current_df_index <= 0), on_click=data_manager.undo)
#             with col2:
#                 st.button("Redo", disabled=(st.session_state.current_df_index >= len(st.session_state.df_states) - 1), on_click=data_manager.redo)

#     # --- Main View ---
#     if not file_loaded:
#         st.info("📁 Please upload a CSV or Excel file in the sidebar to begin.")
#         st.stop()

#     st.dataframe(data_manager.get_current_df())

#     # -----------------------------------------------------------
#     # 🧩 Handle user's fix/clarification choice (smart retry)
#     # -----------------------------------------------------------
#     if st.session_state.user_choice:
#         choice = st.session_state.user_choice
#         st.session_state.user_choice = None  # Reset after handling

#         suggestion = choice.get("suggestion")
#         message_index = choice.get("message_index", len(st.session_state.chat_history) - 1)

#         # Find the original user query
#         original_prompt = ""
#         for i in range(message_index, -1, -1):
#             if st.session_state.chat_history[i]["role"] == "user":
#                 original_prompt = st.session_state.chat_history[i]["content"]
#                 break

#         # --- Clarification Strategy ---
#         if suggestion.get("strategy") == "ASK_USER_CLARIFICATION":
#             response = {"role": "assistant", "content": "Could you please provide more details or clarify your request?"}
#             st.session_state.chat_history.append(response)

#         # --- Retry with Fix Strategy ---
#         else:
#             with st.chat_message("assistant"):
#                 with st.spinner("Applying solution and retrying..."):
#                     schema = data_manager.get_schema_string()
#                     new_query = agent.regenerate_query_with_solution(
#                         original_prompt, suggestion, schema, data_manager.table_name, st.session_state.chat_history
#                     )

#                     if new_query:
#                         result_df, error = data_manager.execute_query(new_query)
#                         if error:
#                             response = {
#                                 "role": "assistant",
#                                 "content": f"The fix also failed. Error: {error}",
#                                 "sql": new_query
#                             }
#                         else:
#                             summary = agent.interpret_results(original_prompt, result_df)
#                             charts = agent.suggest_charts(result_df)
#                             follow_ups = agent.suggest_follow_ups(original_prompt, result_df)
#                             response = {
#                                 "role": "assistant",
#                                 "content": summary,
#                                 "dataframe": result_df,
#                                 "sql": new_query,
#                                 "charts": charts,
#                                 "chart_df": result_df,
#                                 "follow_ups": follow_ups
#                             }
#                     else:
#                         response = {"role": "assistant", "content": "I wasn't able to apply the fix successfully."}

#                     st.session_state.chat_history.append(response)

#         st.rerun()

#     # -----------------------------------------------------------
#     # 💬 Display chat history and take new input
#     # -----------------------------------------------------------
#     display_chat_history()

#     user_prompt = st.chat_input("Ask a question about your data...")
#     if user_prompt:
#         process_prompt(user_prompt, agent, data_manager)
#         st.rerun()

# # -----------------------------------------------------------
# # 🚀 Run App
# # -----------------------------------------------------------
# if __name__ == "__main__":
#     main()
# main.py
import streamlit as st
from agent import Agent
from data_manager import DataManager
from ui_components import initial_setup, display_chat_history, file_uploader_and_profiling

def generate_and_run_query(agent: Agent, data_manager: DataManager, user_prompt: str, query_to_run: str = None):
    """
    Unified function to generate/run a query, handle errors recursively, and produce a complete response.
    """
    schema = data_manager.get_schema_string()
    
    # If a specific query is provided (from a fix), use it. Otherwise, generate a new one.
    query = query_to_run if query_to_run else agent.generate_sql(
        user_prompt, schema, data_manager.table_name, st.session_state.chat_history
    )

    if not query:
        return {"role": "assistant", "content": "Sorry, I was unable to generate a SQL query for your request."}

    result_df, error = data_manager.execute_query(query)

    if error:
        # If execution fails, analyze the error and propose solutions.
        suggestions = agent.analyze_error(query, error, schema)
        if suggestions:
            return {
                "role": "assistant", "content": "I encountered an issue with that query. Here are some options:",
                "error_message": f"Error: {error}", "error_suggestions": suggestions,
                "failed_query": query # IMPORTANT: Pass the failed query for the next attempt
            }
        else:
            return {"role": "assistant", "content": f"Query failed with an unrecoverable error: {error}", "sql": query}
    else:
        # If execution succeeds, generate the full analysis.
        analysis = agent.analyze_and_summarize_results(user_prompt, result_df)
        return {"role": "assistant", "content": analysis, "dataframe": result_df, "sql": query}

def main():
    initial_setup()
    st.title("💡 Robust AI Data Agent")
    st.write("Now with a resilient, recursive error-fixing loop and reliable context.")

    # --- Setup ---
    if st.session_state.agent is None:
        try: st.session_state.agent = Agent()
        except Exception as e: st.error(f"Please provide your GROQ_API_KEY: {e}"); st.stop()
    if st.session_state.data_manager is None: st.session_state.data_manager = DataManager()
    
    agent, data_manager = st.session_state.agent, st.session_state.data_manager

    # --- Sidebar and File Upload ---
    with st.sidebar:
        st.header("⚙️ Controls")
        file_loaded = file_uploader_and_profiling(data_manager)
        if file_loaded:
            st.button("Undo", on_click=data_manager.undo); st.button("Redo", on_click=data_manager.redo)
    if not file_loaded: st.info("📁 Please upload a file to begin."); st.stop()
    
    st.dataframe(data_manager.get_current_df())
    display_chat_history()

    # --- UNIFIED TASK PROCESSING ---
    # This new logic determines which task to perform in this script run.
    task_to_process = None
    
    # Priority 1: A user has clicked a suggestion button.
    if st.session_state.user_choice:
        choice = st.session_state.user_choice
        st.session_state.user_choice = None # Consume the choice immediately
        
        # Find the original user prompt that led to this error chain
        original_prompt = next((msg["content"] for msg in reversed(st.session_state.chat_history) if msg["role"] == "user"), None)
        
        if original_prompt and "failed_query" in choice and "suggestion" in choice:
            task_to_process = {
                "type": "fix_query",
                "original_prompt": original_prompt,
                "choice": choice
            }

    # Priority 2: A user has clicked a follow-up question.
    elif st.session_state.queued_prompt:
        task_to_process = {
            "type": "new_prompt",
            "prompt": st.session_state.queued_prompt
        }
        st.session_state.queued_prompt = None # Consume the prompt

    # Priority 3: A user has typed a new question.
    elif user_prompt := st.chat_input("Ask a question or request a chart..."):
        task_to_process = {
            "type": "new_prompt",
            "prompt": user_prompt
        }

    # --- EXECUTE THE DETERMINED TASK ---
    if task_to_process:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = {}
                # --- Task: Handle a NEW prompt from user ---
                if task_to_process["type"] == "new_prompt":
                    prompt = task_to_process["prompt"]
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    
                    schema = data_manager.get_schema_string()
                    # Route the request to decide if it's a query or a chart
                    routed_request = agent.route_request(prompt, schema)
                    tool = routed_request.get("tool", "run_sql_query")
                    params = routed_request.get("parameters", {})

                    if tool == "create_visualization":
                        # Visualization workflow...
                        viz_sql = agent.generate_sql_for_viz(params, schema, data_manager.table_name)
                        if viz_sql:
                            chart_data, error = data_manager.execute_query(viz_sql)
                            if error:
                                response = {"role": "assistant", "content": f"I tried to get data for your chart, but hit an error: {error}", "sql": viz_sql}
                            else:
                                response = {"role": "assistant", "content": f"Here is the {params.get('chart_type', 'chart')} you requested.", "sql": viz_sql, "chart_params": params, "chart_df": chart_data}
                        else:
                            response = {"role": "assistant", "content": "I understood you want a chart, but I couldn't figure out the data to retrieve."}

                    else: # Default to run_sql_query
                        # This is the entry point for the recursive query function
                        response = generate_and_run_query(agent, data_manager, prompt)

                # --- Task: Handle a FIX chosen by the user ---
                elif task_to_process["type"] == "fix_query":
                    st.write("Applying the suggested fix...")
                    choice = task_to_process["choice"]
                    original_prompt = task_to_process["original_prompt"]
                    
                    # Generate the new, corrected query
                    new_query = agent.regenerate_query_with_solution(
                        original_prompt, choice["failed_query"], choice["suggestion"], 
                        data_manager.get_schema_string(), data_manager.table_name, st.session_state.chat_history
                    )
                    
                    # --- RECURSIVE CALL ---
                    # Feed the new query back into the same robust processing function.
                    # This is what enables the recursive error handling.
                    response = generate_and_run_query(agent, data_manager, original_prompt, new_query)

                st.session_state.chat_history.append(response)
        st.rerun()

if __name__ == "__main__":
    main()