"""
backend/services/agent_service.py — LangChain agent using LangGraph.
Uses ChatGroq + langgraph create_react_agent (modern LangChain 1.x pattern).
Built once as a module-level singleton.
"""

import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from config import GROQ_API_KEY, GROQ_MODEL
from backend.services import data_service, chart_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Chart registry — stores the last generated chart so the LLM is never
# given a raw base64 string (would overflow context and cause hangs).
# ---------------------------------------------------------------------------
_chart_registry: dict = {"base64": None, "type": None}

# ---------------------------------------------------------------------------
# System prompt — built dynamically from actual dataset at startup
# ---------------------------------------------------------------------------
def _build_system_prompt() -> str:
    """
    Compute key dataset facts once at startup and inject them into the system
    prompt. This way no numbers are ever hardcoded — if the CSV changes, the
    prompt stays accurate automatically.
    """
    try:
        df = data_service.get_dataframe()
        total       = len(df)
        survived    = int(df["Survived"].sum())
        not_survived = total - survived
        survival_pct = round(df["Survived"].mean() * 100, 2)
    except Exception as e:
        # Fallback if dataset unavailable at import time
        logger.warning(f"Could not load dataset for system prompt: {e}")
        total, survived, not_survived, survival_pct = "unknown", "unknown", "unknown", "unknown"

    return (
        "You are a smart, friendly data analyst specialized in the Titanic passenger dataset. "
        "You have tools that query the dataset and generate charts. "
        "Always use tools to answer data questions — never guess the numbers. "
        "When a user asks for a chart or histogram, call the appropriate chart tool. "
        "After a chart tool is called, briefly describe what the chart shows. "
        "Keep answers concise and easy to understand. "
        "Always maintain the full context of the conversation. If the user says 'their' or "
        "'those' or uses any pronoun, refer back to what was discussed earlier in the conversation."
        "\n\n"
        "CRITICAL — DATASET vs HISTORICAL FACTS:\n"
        f"The dataset contains {total} passenger records — this is a well-known ML training "
        "sample, NOT the complete Titanic manifest. The real Titanic carried approximately "
        "2,224 people and around 1,500 perished.\n"
        f"Key dataset figures for your reference: {total} total records, {survived} survived, "
        f"{not_survived} did not survive, {survival_pct}% survival rate.\n"
        "NEVER use dataset numbers to make claims about the real historical event. "
        f"When answering from the dataset, always say 'in this dataset' or 'among the {total} records'. "
        "When the user asks about historical totals (how many died, how many were on board, etc.), "
        "answer from your historical knowledge and clearly note it differs from the dataset sample. "
        f"Example: if asked 'how many didn't survive', say: 'Historically, around 1,500 of the "
        f"~2,224 aboard perished. In this {total}-record dataset, {not_survived} passengers did "
        "not survive.'"
    )

SYSTEM_PROMPT = _build_system_prompt()

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@tool
def get_male_percentage() -> str:
    """Returns the percentage of male passengers on the Titanic."""
    return data_service.get_male_percentage()

@tool
def get_female_percentage() -> str:
    """Returns the percentage of female passengers on the Titanic."""
    return data_service.get_female_percentage()

@tool
def get_average_fare() -> str:
    """Returns the average ticket fare paid by Titanic passengers."""
    return data_service.get_average_fare()

@tool
def get_survival_rate() -> str:
    """Returns the overall survival rate of Titanic passengers as a percentage."""
    return data_service.get_survival_rate()

@tool
def get_embarkation_counts() -> str:
    """Returns the number of passengers per embarkation port: Southampton, Cherbourg, Queenstown."""
    return data_service.get_embarkation_counts()

@tool
def get_age_stats() -> str:
    """Returns the average, minimum, and maximum passenger age."""
    return data_service.get_age_stats()

@tool
def get_total_passengers() -> str:
    """Returns the number of records in the dataset sample.
    IMPORTANT: This is a training sample, NOT the full Titanic manifest.
    The real ship carried approximately 2,224 people. Always clarify this distinction."""
    return data_service.get_total_passengers()

@tool
def get_dataset_summary() -> str:
    """Returns a full computed summary of the dataset: total records, survival counts,
    sex breakdown, average fare and age. Use when the user asks for an overview or
    general statistics. All values are computed live from the data — never hardcoded."""
    return data_service.get_dataset_summary()

@tool
def get_class_distribution() -> str:
    """Returns the number of passengers in each travel class (1st, 2nd, 3rd)."""
    return data_service.get_class_distribution()

@tool
def get_survival_by_sex() -> str:
    """Returns survival counts and rates broken down by sex (male vs female)."""
    return data_service.get_survival_by_sex()

@tool
def age_histogram() -> str:
    """Generates a histogram of passenger age distribution. Use when user asks for an age chart or age histogram."""
    b64 = chart_service.age_histogram()
    _chart_registry["base64"] = b64
    _chart_registry["type"] = "age_histogram"
    return "Age distribution histogram generated and will be displayed to the user."

@tool
def embarkation_bar_chart() -> str:
    """Generates a bar chart of passengers per embarkation port. Use when user asks for an embarkation chart."""
    b64 = chart_service.embarkation_bar_chart()
    _chart_registry["base64"] = b64
    _chart_registry["type"] = "embarkation_bar_chart"
    return "Embarkation port bar chart generated and will be displayed to the user."

@tool
def survival_pie_chart() -> str:
    """Generates a pie chart of survived vs did-not-survive passengers. Use when user asks for a survival chart."""
    b64 = chart_service.survival_pie_chart()
    _chart_registry["base64"] = b64
    _chart_registry["type"] = "survival_pie_chart"
    return "Survival pie chart generated and will be displayed to the user."

@tool
def sex_distribution_pie_chart() -> str:
    """Generates a pie chart showing the distribution of male and female passengers. Use when the user asks for a chart of males and females, or sex distribution."""
    b64 = chart_service.sex_distribution_pie_chart()
    _chart_registry["base64"] = b64
    _chart_registry["type"] = "sex_distribution_pie_chart"
    return "Sex distribution pie chart generated and will be displayed to the user."

@tool
def survival_by_class_bar_chart() -> str:
    """Generates a bar chart of survival by passenger class (1st, 2nd, 3rd). Use when asked about class survival."""
    b64 = chart_service.survival_by_class_bar_chart()
    _chart_registry["base64"] = b64
    _chart_registry["type"] = "survival_by_class_bar_chart"
    return "Survival by class bar chart generated and will be displayed to the user."

@tool
def top_wealthiest_bar_chart() -> str:
    """Generates a horizontal bar chart of the top 50 wealthiest passengers by ticket fare. Use when user asks for a chart of the wealthiest, richest, or top passengers."""
    b64 = chart_service.top_wealthiest_bar_chart()
    _chart_registry["base64"] = b64
    _chart_registry["type"] = "top_wealthiest_bar_chart"
    return "Top 50 wealthiest passengers chart generated and will be displayed to the user."

ALL_TOOLS = [
    get_male_percentage,
    get_female_percentage,
    get_average_fare,
    get_survival_rate,
    get_embarkation_counts,
    get_age_stats,
    get_total_passengers,
    get_dataset_summary,
    get_class_distribution,
    get_survival_by_sex,
    age_histogram,
    embarkation_bar_chart,
    survival_pie_chart,
    sex_distribution_pie_chart,
    survival_by_class_bar_chart,
    top_wealthiest_bar_chart,
]


def build_agent():
    """Build and return the LangGraph react agent. Called once at startup."""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set. Please add it to your .env file.")

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.1,
    )

    graph = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
    )

    tool_names = [t.name for t in ALL_TOOLS]
    logger.info(f"Agent built — model={GROQ_MODEL}, tools={tool_names}")
    return graph


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
try:
    agent_graph = build_agent()
    logger.info("Agent graph ready.")
except Exception as e:
    agent_graph = None
    logger.error(f"FAILED to build agent: {e}", exc_info=True)


def _build_messages(history: list, question: str) -> list:
    """
    Convert Streamlit session_state history (list of dicts with 'role' and 'content')
    into LangChain message objects for the agent.

    Handles both dict-style messages {"role": ..., "content": ...}
    and object-style messages with .role / .content attributes.
    """
    msgs = []

    if history:
        for msg in history:
            # Safely extract role and content regardless of dict vs object
            if isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")
            else:
                role = getattr(msg, "role", "")
                content = getattr(msg, "content", "")

            # Skip empty messages — they confuse the agent
            if not content or not content.strip():
                continue

            if role == "user":
                msgs.append(HumanMessage(content=content))
            elif role == "assistant":
                # Only include assistant messages that have real text content.
                # Skip messages that were just chart notifications with no text.
                if content and content.strip():
                    msgs.append(AIMessage(content=content))

    # Always append the current user question last
    msgs.append(HumanMessage(content=question))
    return msgs


def _extract_answer(result: dict) -> str:
    """
    Extract the final text answer from the LangGraph agent result.

    LangGraph returns a list of messages. The last AIMessage with non-empty
    content is the final answer. We must skip:
      - ToolMessages (tool call results)
      - AIMessages with empty content (these are tool-call invocation messages,
        where the LLM decided to call a tool but hasn't produced text yet)
    """
    messages = result.get("messages", [])
    logger.info(f"Agent returned {len(messages)} message(s)")

    for msg in reversed(messages):
        msg_type = getattr(msg, "type", "") or getattr(msg, "role", "")

        # Skip tool result messages entirely
        if msg_type == "tool":
            continue

        # Only consider AI/assistant messages
        if msg_type in ("ai", "assistant"):
            content = getattr(msg, "content", "")
            # IMPORTANT: skip empty-content AI messages — these are tool-call
            # invocation messages, not final answers
            if content and content.strip():
                logger.info(f"Found final answer: {content[:100]!r}...")
                return content

    return ""


def run_agent(question: str, history: list = None) -> dict:
    """
    Invoke the agent with a user question and chat history.

    Args:
        question: The current user question.
        history:  List of previous messages as dicts {"role": "user"/"assistant", "content": str}.
                  Pass the full st.session_state.messages list from Streamlit.

    Returns:
        dict with keys: answer (str), chart_base64 (str|None), chart_type (str|None)
    """
    if agent_graph is None:
        return {
            "answer": "⚠️ Agent is unavailable. Check your GROQ_API_KEY in the .env file and restart.",
            "chart_base64": None,
            "chart_type": None,
        }

    # Reset chart registry before each call
    _chart_registry["base64"] = None
    _chart_registry["type"] = None

    try:
        logger.info(f"Running agent | question={question!r} | history_len={len(history) if history else 0}")

        messages = _build_messages(history or [], question)
        logger.info(f"Sending {len(messages)} message(s) to agent")

        result = agent_graph.invoke({"messages": messages})

        answer = _extract_answer(result)

        if not answer:
            answer = "I processed your request but couldn't generate a text response. Please try rephrasing."

        logger.info(f"Final answer: {answer[:120]!r}")

        return {
            "answer": answer,
            "chart_base64": _chart_registry.get("base64"),
            "chart_type": _chart_registry.get("type"),
        }

    except Exception as e:
        logger.exception(f"Agent error for {question!r}: {e}")
        return {
            "answer": f"⚠️ Error: {str(e)}",
            "chart_base64": None,
            "chart_type": None,
        }