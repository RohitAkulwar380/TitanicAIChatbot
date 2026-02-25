# 🚢 Titanic Dataset Chatbot

A conversational AI chatbot that answers natural language questions about the Titanic passenger dataset, with text answers and data visualizations.

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI (runs as background thread inside Streamlit)
- **Agent**: LangChain + Groq LLM
- **Data**: Pandas + Titanic CSV
- **Charts**: Matplotlib

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create your `.env` file
```bash
copy .env.example .env
```
Then open `.env` and paste your Groq API key:
```
GROQ_API_KEY=your_key_here
```
Get a free key at: https://console.groq.com

### 3. Run the app
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. The FastAPI backend starts automatically on port 8000.

## Example Questions

| Question | Expected Answer |
|---|---|
| What percentage of passengers were male? | ~64.76% |
| Show me a histogram of passenger ages | Chart rendered |
| What was the average ticket fare? | ~$32.20 |
| How many passengers embarked from each port? | S: 644, C: 168, Q: 77 |
| What was the survival rate? | ~38.38% |
| Show survival by passenger class | Chart rendered |

## Project Structure

```
TitanicAIChatbot/
├── app.py                   # Streamlit frontend
├── config.py                # Centralized configuration
├── titanic.csv              # Dataset
├── requirements.txt
├── .env.example             # Template (safe to commit)
├── .env                     # Your secrets (DO NOT COMMIT)
└── backend/
    ├── main.py              # FastAPI app
    ├── models.py            # Pydantic schemas
    └── services/
        ├── data_service.py  # Pandas data queries
        ├── chart_service.py # Matplotlib visualizations
        └── agent_service.py # LangChain agent
```
