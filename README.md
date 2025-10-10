
# 💡 Conversational AI CSV Analyst

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-Streamlit-red.svg)](https://streamlit.io)

This project is a sophisticated, full-stack web application that deploys a **conversational AI agent** to serve as a personal data analyst. It moves beyond simple "Natural Language to SQL" by implementing a robust, multi-skilled agentic framework that allows users to query, manipulate, and visualize datasets through intuitive, natural language commands.

**The core mission:** Empower anyone to unlock insights from their data, simply by having a conversation.

---


### 🚀 The Problem & Our Solution

Traditional data analysis tools often have a steep learning curve, requiring knowledge of specific query languages (like SQL) or complex BI software. This creates a barrier between the data and the domain experts who need to understand it.

This project solves that problem by providing an intelligent intermediary:
*   **Problem:** Slow, manual, and expertise-driven data analysis.
*   **Solution:** A **resilient and proactive AI agent** that understands user intent, writes and fixes its own code, provides analytical summaries, and intelligently guides the user's exploration journey.

---

### 🛠️ Key Features & Technical Highlights

This application is more than a simple chatbot; it's a system of interconnected AI capabilities.

#### 1. **Smart Task Routing Agent**
The "brain" of the operation. Instead of a single model trying to do everything, a dedicated **Router Agent** analyzes each user prompt and the table schema to delegate the task to the appropriate specialized tool. It correctly distinguishes between:
*   **Data Analysis Requests** (requiring complex SQL generation).
*   **Visualization Requests** (requiring a two-step process: data fetching, then plotting).
*   **Conversational Chit-Chat**.

#### 2. **Recursive Self-Correction Loop**
This is the core of the agent's resilience. If a generated SQL query fails:
1.  The agent **catches the error** message from the database.
2.  The **Error Analysis Agent** is invoked to diagnose the root cause (e.g., data type mismatch, syntax error).
3.  It proposes **structured, user-friendly solutions** (e.g., "The 'price' column looks like text. Should I treat it as a number?").
4.  If the user accepts a fix, the **Query Refiner Agent** regenerates the code, applying the chosen strategy.
5.  This new code is re-executed. If it fails *again*, the loop repeats, analyzing the new error.

#### 3. **Stateful Conversational Memory**
The agent maintains the full context of the conversation. This allows for sophisticated, multi-turn interactions and follow-up questions, such as:
*   *User:* "Show me the total sales by country."
*   *(Agent shows a table)*
*   *User:* "Now just for the top 3."
*   *(Agent correctly applies an `ORDER BY ... LIMIT 3` to the previous query context)*

#### 4. **Proactive Analysis & Guidance**
The agent doesn't just answer questions; it actively helps the user think like an analyst.
*   **Automated Data Profiling:** On file upload, it instantly generates a comprehensive `ydata-profiling` report, giving an immediate overview of the dataset's health and statistics.
*   **AI-Generated Insights:** For every successful query, the **Analyst Agent** provides a rich, multi-paragraph response including:
    *   A direct, one-sentence **summary**.
    *   An insightful **observation** that highlights a key trend or outlier.
    *   A list of **suggested next questions** to guide the exploration.
*   **Dynamic Visualizations:** Generates interactive charts and plots on-demand using Plotly, correctly inferring the data needed for the visualization.

---

### 🏗️ Architecture & Tech Stack

This project is built on a modular, agentic framework designed for clarity and scalability.

*   **Frontend:** **Streamlit** (for the interactive web UI and chat components).
*   **AI Orchestration:** **LangChain** (for managing prompts, models, and agentic chains).
*   **Core LLM:** **Llama 3 (70B)** via the **Groq API** (for high-speed, high-quality language understanding and generation).
*   **Data Backend:** **DuckDB** (for high-performance, in-memory SQL execution).
*   **Data Manipulation:** **Pandas** (for data loading and structuring).
*   **Visualization:** **Plotly** (for creating rich, interactive charts).

---

### ⚙️ Installation & Usage

Follow these steps to run the project locally.

#### **1. Prerequisites**
*   Python 3.9+
*   A virtual environment tool (like `venv` or `conda`).

#### **2. Clone the Repository**
```bash
git clone https://github.com/RakeshPathlavath07/CSV-Analyst
cd CSV-Analyst
```

#### **3. Set Up the Environment**
Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```
Install the required dependencies:
```bash
pip install -r requirements.txt
```

#### **4. Configure API Keys**
You need a free Groq API key to power the agent.
1.  Create a file at this location: `.streamlit/secrets.toml`.
2.  Add your API key inside the file like this:
    ```toml
    GROQ_API_KEY = "gsk_YourSecretGroqApiKeyHere"
    ```

#### **5. Run the Application**
Launch the Streamlit app from your terminal:
```bash
streamlit run main.py
```
Your browser should automatically open to the application's local URL.

---

### 🗺️ Future Roadmap

This project has a strong foundation for future expansion into a more comprehensive, multi-agent platform:
*   [ ] **Data Engineering Agent:** An agent dedicated to more complex data cleaning, transformation, and feature engineering tasks.
*   [ ] **Persistent Sessions:** Save, load, and share analysis sessions and conversations.
*   [ ] **Expanded Visualization Agent:** Support for more complex chart types, multi-chart dashboards, and user customization.
*   [ ] **Database Connectors:** Allow the agent to connect directly to live databases (PostgreSQL, Snowflake, etc.) instead of just file uploads.

---

### 📜 License
This project is licensed under the MIT License. See the `LICENSE` file for details.
