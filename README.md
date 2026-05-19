# VentureMind AI

Autonomous Venture Intelligence Platform

## Description

VentureMind AI is an AI-native startup intelligence operating system designed to help transform raw market domains into venture-backed startup opportunities. It uses FastAPI for async APIs, LangGraph for orchestration, LangChain for agent abstractions, and the Groq API for fast LLM-powered reasoning across discovery, validation, critique, roadmap generation, and memory-aware workflow execution.

## Tech Stack

- Python 3.11
- FastAPI
- LangGraph
- LangChain
- Groq API
- Pydantic v2

## Project Structure

```text
backend/
├── agents/
│   ├── base_agent.py
│   ├── competitor_agent.py
│   ├── memory_agent.py
│   ├── problem_discovery_agent.py
│   ├── redteam_agent.py
│   ├── roadmap_agent.py
│   ├── solution_generator_agent.py
│   └── validation_agent.py
├── api/
│   └── routes.py
├── chains/
│   ├── memory_chain.py
│   └── validation_chain.py
├── prompts/
│   └── system_prompts.py
├── schemas/
│   └── base_schema.py
├── utils/
│   ├── json_validator.py
│   ├── llm_client.py
│   └── retry_handler.py
├── workflows/
│   └── orchestration_graph.py
├── config.py
└── main.py
```

## Setup Instructions

1. Clone the repository:

```powershell
git clone https://github.com/Kaus360/venturemind-ai.git
cd "venturemind-ai"
```

2. Create a Python 3.11 virtual environment:

```powershell
py -3.11 -m venv .venv
```

3. Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

5. Create your environment file from the example:

```powershell
Copy-Item .env.example .env
```

6. Open `.env` and add your `GROQ_API_KEY`.

7. Run the server:

```powershell
uvicorn backend.main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/v1/generate-problems` | Generate startup problems for a target domain |
| POST | `/api/v1/generate-solution` | Generate a startup solution from a problem statement |
| POST | `/api/v1/validate-startup` | Validate startup feasibility and score the concept |
| POST | `/api/v1/analyze-competitors` | Analyze competitors, gaps, and opportunity areas |
| POST | `/api/v1/redteam-critique` | Run an adversarial critique against the startup idea |
| POST | `/api/v1/generate-roadmap` | Generate a phased startup execution roadmap |
| POST | `/api/v1/execute-workflow` | Run the full VentureMind AI orchestration workflow |
| GET | `/api/v1/memory-context` | Retrieve stored workflow memory context |
| GET | `/health` | Basic health check endpoint |

## Workflow Architecture

```text
START → Problem Discovery → Solution Generator → Validation → Competitor Analysis → RedTeam Critic → Roadmap Generator → Memory Agent → END
```

## Team

Team Member 1 — AI Orchestration + Agent Engineer

## License

MIT
