# data_manager.py
import streamlit as st
import pandas as pd
import duckdb
import re

class DataManager:
    def __init__(self, table_name="main_table"):
        self.conn = duckdb.connect(database=':memory:', read_only=False)
        self.table_name = table_name

    def load_data(self, uploaded_file):
        """Loads data from an uploaded file into DuckDB and initializes state."""
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Clean column names for SQL compatibility
            df.columns = [re.sub(r'[^0-9a-zA-Z_]', '', col).strip() for col in df.columns]

            self.conn.execute(f"DROP TABLE IF EXISTS {self.table_name};")
            self.conn.register('df_temp', df)
            self.conn.execute(f'CREATE TABLE {self.table_name} AS SELECT * FROM df_temp;')
            self.update_state(df)
            return True, None
        except Exception as e:
            return False, str(e)

    def update_state(self, df):
        """Adds a new DataFrame state to the history."""
        st.session_state.df_states.append(df)
        st.session_state.current_df_index = len(st.session_state.df_states) - 1

    def get_current_df(self):
        """Returns the current active DataFrame."""
        if st.session_state.df_states:
            return st.session_state.df_states[st.session_state.current_df_index]
        return None

    def get_schema_string(self):
        """Gets the table schema as a string."""
        df = self.get_current_df()
        if df is not None:
            return ", ".join([f"{col} ({dtype})" for col, dtype in df.dtypes.items()])
        return ""

    def execute_query(self, query: str):
        """Executes a SQL query and returns the result as a DataFrame."""
        try:
            result_df = self.conn.execute(query).df()
            # If the query modifies data (e.g., a hypothetical UPDATE), we would update state here.
            # For now, we assume most queries are SELECT.
            # A more advanced version would parse the query to check for DML statements.
            return result_df, None
        except Exception as e:
            return None, str(e)

    def undo(self):
        """Reverts to the previous DataFrame state."""
        if st.session_state.current_df_index > 0:
            st.session_state.current_df_index -= 1

    def redo(self):
        """Moves to the next DataFrame state."""
        if st.session_state.current_df_index < len(st.session_state.df_states) - 1:
            st.session_state.current_df_index += 1