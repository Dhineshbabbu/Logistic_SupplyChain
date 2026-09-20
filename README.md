# 🚚 Supply Chain Dispatch Console

An AI-powered logistics assistant that lets users ask questions about supply-chain data using natural language.

## Features

- ChatGPT-style dark UI
- Multiple chat threads
- LangGraph-based agent workflow
- PostgreSQL data retrieval
- LLM tool calling
- Logistics insights and summaries

## Tech Stack

- Python
- Streamlit
- LangChain
- LangGraph
- Groq LLM
- PostgreSQL
- SQLAlchemy


The agent can retrieve information such as:

- Shipping costs
- ETA variation
- Traffic congestion
- Inventory levels
- Supplier reliability
- Delay probability
- Disruption likelihood
- Route risk

## Example Questions

```text
Give me a summary of the logistics data.
```

```text
What is the average shipping cost?
```

```text
Identify potential delivery risks.
```

```text
Show the order fulfillment status distribution.
```

## Security Notes

- Keep API keys in `.env`.
- Do not commit `.env` to Git.
- Use a read-only database user.
- Validate LLM-generated SQL before execution.
- Restrict database access to approved tables and queries.

## Future Improvements

- Persistent chat history
- Data visualizations
- Real-time alerts
- Predictive delay analysis
- Weather and traffic integration
- Export reports to Excel and PDF

## Author

Dhinesh Babbu A
