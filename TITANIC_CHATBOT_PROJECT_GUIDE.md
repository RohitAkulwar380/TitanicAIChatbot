# 🚢 Titanic Dataset Chat Agent — Project Guide

> A comprehensive guide covering project architecture, best practices, design principles, and pitfalls to avoid when building the Titanic chatbot assignment.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack & Why](#2-tech-stack--why)
3. [Project Structure](#3-project-structure)
4. [Architecture & Data Flow](#4-architecture--data-flow)
5. [Module Breakdown](#5-module-breakdown)
6. [Design Principles](#6-design-principles)
   - [SOLID](#solid-principles)
   - [DRY](#dry-dont-repeat-yourself)
   - [KISS](#kiss-keep-it-simple-stupid)
   - [YAGNI](#yagni-you-arent-gonna-need-it)
   - [Separation of Concerns](#separation-of-concerns)
7. [Best Practices](#7-best-practices)
8. [What TO Do](#8-what-to-do-)
9. [What NOT To Do](#9-what-not-to-do-)
10. [Environment & Secrets Management](#10-environment--secrets-management)
11. [Deployment Guide (Streamlit Cloud)](#11-deployment-guide-streamlit-cloud)
12. [Testing Checklist](#12-testing-checklist)

---

## 1. Project Overview

Build a conversational chatbot that allows users to ask natural language questions about the Titanic passenger dataset and receive both **text answers** and **visualizations** in response.

**Core user stories:**
- "What percentage of passengers were male?" → Text answer with percentage
- "Show me a histogram of passenger ages" → Rendered chart
- "What was the average ticket fare?" → Computed statistic
- "How many passengers embarked from each port?" → Bar chart or table

---

## 2. Tech Stack & Why

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | Streamlit | Pure Python UI, fast to build, easy to deploy |
| **Backend** | FastAPI | Async, fast, auto-generates API docs, Pythonic |
| **Agent** | LangChain | Manages LLM + tools + memory in a structured way |
| **LLM** | Groq (via OpenAI-compatible API) | Very fast inference, free tier, works with LangChain |
| **Data** | Pandas + Titanic CSV | Industry-standard data manipulation |
| **Charts** | Matplotlib / Plotly | Mature, Streamlit-native rendering |
| **Deployment** | Streamlit Cloud + GitHub | Free, one-click deploy, shareable URL |

---

## 3. Project Structure

```
titanic-chatbot/
│
├── app.py                   # Streamlit frontend — UI only, no business logic
│
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI app — routes only, delegates to services
│   ├── models.py            # Pydantic request/response schemas
│   └── services/
│       ├── __init__.py
│       ├── agent_service.py # LangChain agent setup and invocation
│       ├── data_service.py  # All Titanic dataset loading and querying
│       └── chart_service.py # All chart/visualization generation
│
├── config.py                # Centralized config (env vars, constants)
├── titanic.csv              # Dataset (committed to repo)
├── requirements.txt         # All dependencies pinned to versions
├── .env.example             # Template for env vars (never commit .env)
├── .gitignore               # Must include .env, __pycache__, *.pyc
└── README.md                # Setup instructions and usage examples
```

> **Why this structure?** Each file has one clear responsibility. Adding a new feature means touching one or two files — not hunting across the whole codebase.

---

## 4. Architecture & Data Flow

```
┌─────────────────────────────────────┐
│         Streamlit Frontend          │
│  - Chat input widget                │
│  - Chat history display             │
│  - Chart rendering (st.pyplot)      │
└──────────────┬──────────────────────┘
               │ HTTP POST /chat (JSON)
               ▼
┌─────────────────────────────────────┐
│         FastAPI Backend             │
│  - Receives question                │
│  - Validates with Pydantic          │
│  - Delegates to AgentService        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         LangChain Agent             │
│  - Receives user question           │
│  - Decides which tool(s) to call    │
│  - Formats final response           │
└──────┬───────────────┬──────────────┘
       │               │
       ▼               ▼
┌──────────────┐  ┌──────────────────┐
│ DataService  │  │  ChartService    │
│ (pandas ops) │  │ (matplotlib/     │
│              │  │  plotly charts)  │
└──────────────┘  └──────────────────┘
       │               │
       └───────┬───────┘
               ▼
      Response: { text, chart_base64 }
               │
               ▼
      Streamlit renders both
```

---

## 5. Module Breakdown

### `config.py`
Centralize all configuration. Never hardcode values anywhere else.

```python
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
TITANIC_CSV_PATH = os.getenv("TITANIC_CSV_PATH", "titanic.csv")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
```

---

### `backend/models.py`
Define clean Pydantic schemas for all API inputs and outputs.

```python
from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    chart_base64: Optional[str] = None  # Base64 PNG string if a chart was generated
    chart_type: Optional[str] = None    # e.g. "histogram", "bar"
```

---

### `backend/services/data_service.py`
Responsible for **one thing only**: loading and querying the Titanic dataset.

```python
import pandas as pd
from config import TITANIC_CSV_PATH
from functools import lru_cache

@lru_cache(maxsize=1)
def get_dataframe() -> pd.DataFrame:
    """Load Titanic CSV once and cache it. Never reload on every request."""
    return pd.read_csv(TITANIC_CSV_PATH)

def get_male_percentage() -> float:
    df = get_dataframe()
    return round((df['Sex'] == 'male').mean() * 100, 2)

def get_average_fare() -> float:
    df = get_dataframe()
    return round(df['Fare'].mean(), 2)

def get_embarkation_counts() -> dict:
    df = get_dataframe()
    return df['Embarked'].value_counts().to_dict()

def get_age_data() -> list:
    df = get_dataframe()
    return df['Age'].dropna().tolist()
```

---

### `backend/services/chart_service.py`
Responsible for **one thing only**: generating charts and returning base64 strings.

```python
import matplotlib.pyplot as plt
import io
import base64
from data_service import get_dataframe, get_age_data, get_embarkation_counts

def fig_to_base64(fig) -> str:
    """Convert any matplotlib figure to a base64 string for JSON transport."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded

def age_histogram() -> str:
    ages = get_age_data()
    fig, ax = plt.subplots()
    ax.hist(ages, bins=20, color="steelblue", edgecolor="white")
    ax.set_title("Distribution of Passenger Ages")
    ax.set_xlabel("Age")
    ax.set_ylabel("Count")
    return fig_to_base64(fig)

def embarkation_bar_chart() -> str:
    counts = get_embarkation_counts()
    port_labels = {"S": "Southampton", "C": "Cherbourg", "Q": "Queenstown"}
    labels = [port_labels.get(k, k) for k in counts.keys()]
    fig, ax = plt.subplots()
    ax.bar(labels, counts.values(), color="coral", edgecolor="white")
    ax.set_title("Passengers by Embarkation Port")
    ax.set_ylabel("Count")
    return fig_to_base64(fig)
```

---

### `backend/services/agent_service.py`
LangChain agent wiring — connects LLM to tools.

```python
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import StructuredTool
from langchain import hub
from config import GROQ_API_KEY, GROQ_MODEL
from . import data_service, chart_service

def build_agent() -> AgentExecutor:
    llm = ChatOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
    )

    tools = [
        StructuredTool.from_function(
            func=data_service.get_male_percentage,
            name="get_male_percentage",
            description="Returns the percentage of male passengers on the Titanic."
        ),
        StructuredTool.from_function(
            func=data_service.get_average_fare,
            name="get_average_fare",
            description="Returns the average ticket fare paid by passengers."
        ),
        StructuredTool.from_function(
            func=chart_service.age_histogram,
            name="age_histogram",
            description="Generates a histogram of passenger ages. Returns base64 PNG."
        ),
        StructuredTool.from_function(
            func=chart_service.embarkation_bar_chart,
            name="embarkation_bar_chart",
            description="Generates a bar chart of passengers per embarkation port."
        ),
    ]

    prompt = hub.pull("hwchase17/openai-functions-agent")
    agent = create_openai_functions_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
```

---

### `backend/main.py`
FastAPI entry point — thin routing layer only.

```python
from fastapi import FastAPI
from backend.models import ChatRequest, ChatResponse
from backend.services.agent_service import build_agent

app = FastAPI(title="Titanic Chat API")
agent_executor = build_agent()  # Build once at startup

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    result = agent_executor.invoke({"input": request.question})
    # Parse result for text and any chart output
    return ChatResponse(answer=result["output"])
```

---

### `app.py` (Streamlit)
UI only — no data logic, no chart generation here.

```python
import streamlit as st
import requests
import base64
from PIL import Image
import io
from config import BACKEND_URL

st.title("🚢 Titanic Dataset Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("chart"):
            img_bytes = base64.b64decode(msg["chart"])
            st.image(Image.open(io.BytesIO(img_bytes)))

if prompt := st.chat_input("Ask me anything about the Titanic passengers..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = requests.post(f"{BACKEND_URL}/chat", json={"question": prompt})
            data = response.json()
            st.write(data["answer"])
            if data.get("chart_base64"):
                img_bytes = base64.b64decode(data["chart_base64"])
                st.image(Image.open(io.BytesIO(img_bytes)))

    st.session_state.messages.append({
        "role": "assistant",
        "content": data["answer"],
        "chart": data.get("chart_base64")
    })
```

---

## 6. Design Principles

### SOLID Principles

#### S — Single Responsibility Principle
> Every module, class, or function should have **one reason to change**.

✅ `data_service.py` only queries data. If the dataset changes, you edit one file.
✅ `chart_service.py` only makes charts. If you switch from matplotlib to Plotly, you edit one file.
✅ `agent_service.py` only handles agent logic. If you swap LangChain for another framework, you edit one file.

❌ **Violation example:** Putting pandas queries, chart generation, AND API routing all in `main.py`.

---

#### O — Open/Closed Principle
> Your code should be **open for extension, closed for modification**.

✅ To add a new chart (e.g. survival rate pie chart), just add a new function to `chart_service.py` and register it as a new tool in `agent_service.py`. Nothing else changes.
✅ To add a new data query, add a function to `data_service.py` and register a tool. Done.

❌ **Violation example:** Writing a giant `if "histogram" in question: ... elif "bar chart" in question: ...` block that requires editing the core function every time you add a chart type.

---

#### L — Liskov Substitution Principle
> Subclasses/implementations should be **substitutable** for their base types.

✅ If you switch from Groq to OpenRouter, you only change the `base_url` and `api_key` in `config.py`. The rest of the agent code works identically because both use the OpenAI-compatible interface.

---

#### I — Interface Segregation Principle
> Don't force modules to depend on interfaces they don't use.

✅ `app.py` (Streamlit) only knows about `BACKEND_URL`. It doesn't import pandas, LangChain, or matplotlib — those are backend concerns.
✅ `data_service.py` doesn't know or care about charts or FastAPI.

---

#### D — Dependency Inversion Principle
> Depend on **abstractions**, not concrete implementations.

✅ The agent depends on LangChain's `BaseTool` interface, not specific tool implementations. Swap tools freely.
✅ Use `config.py` as the single source of truth for environment-dependent values. Modules import from config, not directly from `os.environ`.

---

### DRY (Don't Repeat Yourself)

> Every piece of knowledge should have a **single, unambiguous representation** in the system.

**Practical applications in this project:**

- `get_dataframe()` uses `@lru_cache` — the CSV is read **once**, not once per request. Never call `pd.read_csv()` in multiple places.
- `fig_to_base64()` is a shared utility in `chart_service.py` — every chart function calls it. Never copy-paste the base64 conversion logic.
- All config values live in `config.py` — never hardcode `"titanic.csv"` or `"http://localhost:8000"` in multiple files.
- Pydantic models in `models.py` define the API contract once — both the FastAPI route and the Streamlit client rely on the same schema.

---

### KISS (Keep It Simple, Stupid)

> Prefer the simplest solution that works. Complexity is a liability.

✅ Use `@lru_cache` for dataset caching instead of implementing Redis or a database.
✅ Use base64 PNG strings to transport charts over HTTP instead of a file system or S3.
✅ Use Streamlit's built-in `st.chat_input` and `st.chat_message` instead of building a custom chat UI.
✅ Start with a small, explicit set of LangChain tools before adding complexity.

❌ Don't add a database, authentication system, or message queue for this assignment. It's not needed.

---

### YAGNI (You Aren't Gonna Need It)

> Don't build features **until they are actually needed**.

For this assignment scope:
- ❌ Don't add user authentication
- ❌ Don't add a database for chat history persistence
- ❌ Don't build a streaming response system
- ❌ Don't add multiple LLM provider switching UI
- ✅ Do focus on making the 4 example questions work perfectly first

---

### Separation of Concerns

The project is cleanly divided into exactly three layers:

| Layer | Responsible For | Should NOT Touch |
|---|---|---|
| **Streamlit (app.py)** | UI rendering, user input, HTTP calls to backend | pandas, LangChain, matplotlib |
| **FastAPI (backend/)** | Routing, validation, orchestration | Streamlit widgets, UI state |
| **Services** | Business logic, data, charts | HTTP requests, Streamlit, route definitions |

---

## 7. Best Practices

### Python
- Pin all dependency versions in `requirements.txt` (e.g. `fastapi==0.111.0`, not `fastapi`)
- Use type hints on all function signatures
- Use `dataclasses` or Pydantic models for structured data — no raw dicts flying between functions
- Handle exceptions explicitly — never catch bare `except:` without logging

### FastAPI
- Always use async route handlers (`async def`) for better concurrency
- Use Pydantic for all request/response validation — never access `request.body` directly
- Build the agent once at startup, not on every request — it's expensive to initialize

### LangChain
- Write clear, specific tool descriptions — the LLM uses these to decide which tool to call
- Keep tool functions **pure and side-effect-free** where possible
- Log agent reasoning with `verbose=True` during development, disable in production
- Always handle `AgentExecutor` exceptions gracefully — LLMs can time out or return unexpected output

### Streamlit
- Use `st.session_state` for all stateful data (chat history, etc.)
- Never put expensive computation directly in `app.py` — always delegate to the backend
- Use `st.spinner()` to show loading state during API calls
- Use `st.cache_data` or `st.cache_resource` if any data loading happens in the Streamlit layer

### Charts
- Always call `plt.close(fig)` after converting to base64 to prevent memory leaks
- Use `bbox_inches="tight"` when saving figures to avoid clipping
- Label all axes and add titles to every chart
- Use consistent color schemes across charts

---

## 8. What TO Do ✅

- **Start with the data layer first.** Get `data_service.py` working with real queries before touching LangChain or Streamlit.
- **Test your tools in isolation** before wiring them into the agent. Call `data_service.get_male_percentage()` directly in a Python REPL first.
- **Use `.env` for secrets locally.** Never type your API key directly in code.
- **Commit `titanic.csv` to your GitHub repo.** Streamlit Cloud needs it to be in the repo.
- **Add a `.gitignore`** that excludes `.env`, `__pycache__`, `*.pyc`, and `.DS_Store`.
- **Write a clear `README.md`** explaining how to run the project locally — even the assignment reviewers will appreciate it.
- **Handle the `NaN` values** in the Titanic dataset. Columns like `Age`, `Cabin`, and `Embarked` have missing values. Always use `.dropna()` or fill them before computing statistics.
- **Provide fallback responses** when the agent can't determine which tool to use.
- **Use Streamlit secrets** (not `.env`) when deploying to Streamlit Cloud — add your `GROQ_API_KEY` in the Streamlit Cloud dashboard under Settings → Secrets.

---

## 9. What NOT To Do ❌

- **Never commit your `.env` file or API keys** to GitHub. This is a critical security mistake.
- **Never call `pd.read_csv()` inside a tool function** that gets called per request — cache it.
- **Never put business logic in `app.py`** (Streamlit). It's a UI file only.
- **Never hardcode the backend URL** as `"http://localhost:8000"` without making it configurable — this will break on Streamlit Cloud.
- **Never ignore pandas warnings** about chained indexing (`.loc` vs direct indexing).
- **Don't use `print()` for logging** — use Python's `logging` module so you can control log levels.
- **Don't return raw exceptions to the user** — catch them in the FastAPI route and return a friendly error message with the appropriate HTTP status code.
- **Don't forget to handle the case where the LLM generates a chart tool call but the user asked a text-only question** — your response model needs `Optional` fields.
- **Don't skip input validation** — if someone sends an empty string to your `/chat` endpoint, it should return a 422 error, not crash.
- **Don't use global mutable state** — the only global state allowed is the cached dataframe and the agent executor instance.

---

## 10. Environment & Secrets Management

### Local Development
Create a `.env` file (never commit this):
```
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=llama-3.3-70b-versatile
BACKEND_URL=http://localhost:8000
TITANIC_CSV_PATH=titanic.csv
```

Load it in `config.py` using `python-dotenv`:
```python
from dotenv import load_dotenv
load_dotenv()
```

Create a `.env.example` (safe to commit) as a template:
```
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
BACKEND_URL=http://localhost:8000
```

### Streamlit Cloud Deployment
In Streamlit Cloud dashboard → your app → Settings → Secrets, add:
```toml
GROQ_API_KEY = "your_groq_key_here"
GROQ_MODEL = "llama-3.3-70b-versatile"
BACKEND_URL = "http://localhost:8000"
```

Access in code via `st.secrets["GROQ_API_KEY"]` or via the environment (since Streamlit Cloud injects secrets as env vars).

---

## 11. Deployment Guide (Streamlit Cloud)

### One-time Setup
1. Push your project to a **public GitHub repository**
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select your repo → set main file to `app.py`
4. Add your secrets in Settings → Secrets (see above)
5. Click **Deploy** — your app gets a public URL like `https://yourname-titanic-chatbot.streamlit.app`

### Important Note on FastAPI + Streamlit Cloud
Streamlit Cloud **only runs a single process** — it runs `app.py` via Streamlit. It cannot simultaneously run a FastAPI server on a different port.

**Solution options (pick one):**

**Option A (Recommended for simplicity):** Run FastAPI inside the Streamlit process using a background thread:
```python
# In app.py, start FastAPI in a thread on startup
import threading
import uvicorn
from backend.main import app as fastapi_app

def run_backend():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

threading.Thread(target=run_backend, daemon=True).start()
```

**Option B:** Deploy FastAPI separately on [Render.com](https://render.com) (free tier) and point `BACKEND_URL` to the Render URL.

**Option C (Simplest):** Skip FastAPI entirely for the Streamlit Cloud version and call the agent service directly from `app.py`. Add a comment in the code explaining that FastAPI is available for the API-only version.

---

## 12. Testing Checklist

Before submitting your Streamlit URL, verify:

- [ ] "What percentage of passengers were male?" returns a number close to **64.76%**
- [ ] "Show me a histogram of passenger ages" renders a visible chart
- [ ] "What was the average ticket fare?" returns approximately **$32.20**
- [ ] "How many passengers embarked from each port?" returns S: 644, C: 168, Q: 77 (approximately)
- [ ] The chat history persists across multiple questions in the same session
- [ ] A loading spinner appears while the agent is thinking
- [ ] Empty or nonsense input doesn't crash the app
- [ ] The app loads fresh in an incognito browser window (confirms deployment works for others)
- [ ] Your API key is NOT visible anywhere in the GitHub repo

---

## Quick Reference: Titanic Dataset Columns

| Column | Type | Notes |
|---|---|---|
| `PassengerId` | int | Unique ID |
| `Survived` | int | 0 = No, 1 = Yes |
| `Pclass` | int | 1 = First, 2 = Second, 3 = Third |
| `Name` | str | Full name |
| `Sex` | str | "male" / "female" |
| `Age` | float | **Has NaN values** — always dropna() |
| `SibSp` | int | Siblings/spouses aboard |
| `Parch` | int | Parents/children aboard |
| `Ticket` | str | Ticket number |
| `Fare` | float | Ticket price in British pounds |
| `Cabin` | str | **Mostly NaN** |
| `Embarked` | str | S = Southampton, C = Cherbourg, Q = Queenstown. **Has NaN** |

---

*Built for the TailorTalk assignment. Good luck! 🚢*
