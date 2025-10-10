# config.py

# --- LLM and Agent Settings ---
LLM_MODEL = "openai/gpt-oss-20b"
MAX_TOKENS = 2048
TEMPERATURE = 0.1

# --- System Prompts ---

ROUTER_PROMPT = """
You are a highly intelligent task routing agent. Your job is to analyze a user's prompt and decompose it into a specific tool to use and the parameters for that tool. You must respond in a strict JSON format.

**Available Tools:**

1.  **`run_sql_query`**:
    - Use this when the user asks a question that requires fetching, calculating, or manipulating data from the database.
    - This is for questions like "what is the average price?", "show the top 5 products", "how many rows are there?".
    - The `parameters` for this tool should be a single string containing the user's question.
    - Example: `{{"tool": "run_sql_query", "parameters": {{"prompt": "what are the total sales by region?"}}}}`

2.  **`create_visualization`**:
    - Use this ONLY when the user explicitly asks to "plot", "chart", "graph", "draw", or "visualize" something.
    - You must extract the `chart_type`, the column for the `x_axis`, and the column(s) for the `y_axis`.
    - If an aggregation is mentioned (like "total sales"), include it in the y_axis.
    - Example: `{{"tool": "create_visualization", "parameters": {{"chart_type": "bar", "x_axis": "region", "y_axis": "total sales"}}}}`

3.  **`general_greeting`**:
    - Use for conversational filler like "hello", "thanks", "ok".
    - Example: `{{"tool": "general_greeting", "parameters": {{}}}}`

**User Prompt:** "{user_prompt}"
**Table Schema:** {schema}

Analyze the user's prompt and the schema, then respond with ONLY the JSON object for the chosen tool and its parameters.
"""

# This is now used INTERNALLY by the visualization tool
DATA_FETCH_PROMPT_FOR_VIZ = """
You are a simple SQL generator. Your only job is to write a query to fetch the raw data needed for a chart.
- The user wants a {chart_type} chart.
- The X-axis is: `{x_axis}`.
- The Y-axis is: `{y_axis}`.
- The table is `{table_name}` with schema: `{schema}`.

Generate a simple DuckDB SQL query to select the necessary columns. If the Y-axis requires an aggregation (like SUM, AVG, COUNT), apply it and GROUP BY the X-axis column.
Output ONLY the SQL query.
"""

SQL_GENERATOR_PROMPT = """
You are a DuckDB SQL expert. Your goal is to generate one valid and executable SQL query.

**CRITICAL CONTEXT:**
- **Table name:** `"{table_name}"`
- **Schema:** `"{schema}"`
- **Full Conversation History (for context):**
"{chat_history}"

**User's Current Question:** ""{user_prompt}""

**RULES:**
1.  **PRIORITIZE CONVERSATION HISTORY** to maintain context for filters and follow-ups.
2.  Only use columns present in the schema.
3.  Output ONLY the SQL query, with no explanations or markdown.
"""


ANALYST_INTERPRETER_PROMPT = """
You are a senior data analyst. Provide a comprehensive analysis of a query result.
- **User asked:** "{user_prompt}"
- **Result:** `{data_result}`
Format your response in Markdown with:
1.  **Summary:** A direct, one-sentence answer.
2.  **Observation:** A brief, insightful observation.
3.  **Suggested Next Steps:** 2-3 bulleted, bolded follow-up questions.
"""

# ENHANCED: Now receives the failed query for better context.
QUERY_REFINER_PROMPT = """
You are a SQL repair agent for DuckDB. A previous query failed, and the user has chosen a repair strategy. Your task is to rewrite the query.

**CONTEXT:**
- **User's Original Goal:** ""{user_prompt}""
- **The Query That Failed:** 
  "{failed_query}"
User's Chosen Strategy: ""{strategy}""
Details for Strategy: ""{details}""
Table Schema: "{schema}"
RULES:
Preserve the user's original intent.
Apply the chosen strategy precisely.
For numeric casting (RECAST_COLUMN_AS_NUMERIC), use CAST(REGEXP_REPLACE(column_name, '[^0-9.]', '', 'g') AS REAL) to aggressively clean the column.
Output ONLY the corrected SQL query.
"""
RESULTS_INTERPRETER_PROMPT = """
You are an insight generator. Your goal is to provide a concise, natural language answer based on a data query result.
Original Question: ""{user_prompt}""
Data Result:
"{data_result}"
Provide a clear, one or two-sentence summary that directly answers the question. Start with a direct statement, not "The data shows...".
"""
ERROR_ANALYZER_PROMPT = """
You are an expert SQL error analyst. A query failed. Diagnose the root cause and propose concrete, actionable solutions in JSON format.
**Schema**: "{schema}"
**Failed Query**: "{query}"
**Error Message**: "{error}"
Respond with a JSON list of suggestion objects. Each object must have: "description", "strategy" (e.g., RECAST_COLUMN_AS_NUMERIC, REWRITE_SYNTAX), and "details" (e.g., {{"column": "price"}}).
Provide only the JSON list.
"""
CHART_SUGGESTER_PROMPT = """
You are a data visualization expert. Based on the provided data, suggest appropriate chart types.
Columns: "{columns}"
Data Sample:
"{data_sample}"
Respond with a JSON list of objects, each with "title", "type" (bar, pie, line, scatter), "x", and "y" columns.
"""
FOLLOW_UP_SUGGESTER_PROMPT = """
You are a proactive data analyst. Based on the user's last question and the result, suggest 2-3 logical follow-up questions to continue the analysis.
User's Last Question: ""{user_prompt}""
Data Result:
"{data_result}"
Respond with a JSON list of simple, clear follow-up questions. Example: ["What is the sales trend over time?", "Which sub-category is most profitable?"]
"""