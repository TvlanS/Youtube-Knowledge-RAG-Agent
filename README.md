# Youtube Knowledge RAG

A multi-agent AI system that searches YouTube for videos on any topic, transcribes them into chapter-aware documents, embeds them into a hybrid vector database, and answers questions using retrieval-augmented generation (RAG).

Built with **CrewAI** for agent orchestration, **DeepSeek** as the LLM, **ChromaDB + BM25** for hybrid retrieval, and **Selenium + yt-dlp** for YouTube data collection.

---

## Agent Summary

| Agent | Role | Tools / Functions Used |
|---|---|---|
| **Manager** | Routes the user's request to the correct specialist agent | CrewAI hierarchical process — no direct tools |
| **Ingestion Agent** | Searches YouTube, downloads transcripts, embeds into vector DB | `IngestionTool` → `YouTubeSearchTool`, `YouTubeTranscriberTool`, `RAGEmbedTool` |
| **QA Agent** | Retrieves context from the knowledge base and answers questions | `CatalogListTool`, `CatalogTool`, `RAGQueryTool` |

### Tool / Function Details

| Tool | File | What It Does |
|---|---|---|
| `IngestionTool` | `tools/custom_tool.py` | Orchestrates the full ingestion pipeline for a given topic |
| `YouTubeSearchTool` | `my_toolbox/tools/youtube_search_tool.py` | Selenium scrape of YouTube search → LLM filtering → saves metadata |
| `YouTubeTranscriberTool` | `my_toolbox/tools/youtube_transcriber_tool.py` | Downloads subtitles via `youtube-transcript-api`, aligns to chapters, exports JSON + PDF |
| `RAGEmbedTool` | `my_toolbox/tools/rag_embed_tool.py` | Splits PDFs into parent/child chunks, embeds with `all-MiniLM-L6-v2`, stores in Chroma |
| `CatalogListTool` | `tools/custom_tool.py` | Returns list of all ingested topics from `data/video_catalog.json` |
| `CatalogTool` | `tools/custom_tool.py` | LLM semantic matching to find the right topic slug for a user query |
| `RAGQueryTool` | `my_toolbox/tools/rag_query_tool.py` | Ensemble retrieval (Chroma + BM25) with LLM-generated alt-query and parent-chunk re-ranking |

---

## Architecture Overview

```
User Input (CLI)
    │
    ▼
CrewAI Manager Agent
    ├── Ingestion Agent  (search / collect / get)
    │       ├── YouTubeSearchTool    → scrape & filter YouTube results
    │       ├── YouTubeTranscriberTool → subtitles + chapters → PDF/JSON
    │       └── RAGEmbedTool         → Chroma + BM25 vector store
    │
    └── QA Agent  (question / ask / explain)
            ├── CatalogListTool  → list available topics
            ├── CatalogTool      → match query to topic slug
            └── RAGQueryTool     → hybrid retrieve + re-rank → answer
```

---

## Project Structure

```
agent_youtube_knowledge_rag_2.0/
├── src/
│   └── agent_youtube_knowledge_rag/
│       ├── main.py               # CLI entry point
│       ├── crew.py               # CrewAI agent & task definitions
│       ├── config/
│       │   ├── agents.yaml       # Agent role/goal/backstory config
│       │   └── tasks.yaml        # Task descriptions
│       └── tools/
│           └── custom_tool.py    # CrewAI-wrapped tool classes
├── my_toolbox/
│   ├── config/
│   │   └── llm_config.yml        # API keys, base URL, prompts
│   ├── tools/
│   │   ├── Ingestion_pipeline.py
│   │   ├── youtube_search_tool.py
│   │   ├── youtube_transcriber_tool.py
│   │   ├── rag_embed_tool.py
│   │   ├── rag_query_tool.py
│   │   ├── rag_state.py
│   │   └── catalog_lookup_tool.py
│   └── utils/
│       ├── config_setup.py
│       ├── LLM_load.py
│       ├── metadata_extract.py
│       ├── subtitle_extract.py
│       ├── sub_sorter.py
│       └── rankingV2.py
├── data/                         # Runtime data (auto-created)
│   ├── original_search_results/
│   ├── filtered_search_results/
│   ├── transcripts/
│   ├── rag/                      # Chroma vector stores per topic
│   ├── video_catalog.json
│   └── recent_topics.json
├── knowledge/
│   └── user_preference.txt
├── requirements.txt
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.10+
- Google Chrome installed (for Selenium)
- A [DeepSeek API key](https://platform.deepseek.com/)

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd agent_youtube_knowledge_rag_2.0
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Open `my_toolbox/config/llm_config.yml` and fill in your credentials:

```yaml
api_key: "your-deepseek-api-key"
website_url: "https://api.deepseek.com"
```

> **Note:** It is recommended to move secrets to a `.env` file and load them with `python-dotenv` rather than storing them in the YAML file directly.

### 5. Install ChromeDriver

The YouTube search tool uses Selenium with Chrome. Install a matching ChromeDriver:

```bash
pip install webdriver-manager
```

Or download manually from [chromedriver.chromium.org](https://chromedriver.chromium.org/) and place it on your `PATH`.

### 6. Run the application

```bash
cd src
python -m agent_youtube_knowledge_rag.main
```

You will be dropped into an interactive CLI. Type a topic to collect videos, or ask a question about previously ingested content.

---

## Usage Examples

```
> collect videos about transformer architecture
  # Ingestion Agent searches YouTube, transcribes, and embeds videos

> what is multi-head attention?
  # QA Agent retrieves relevant chunks and answers from the knowledge base

> what topics have been ingested?
  # Lists all available topics in the catalog
```

---

## Data Flow

1. **Search** — Selenium scrapes YouTube, DeepSeek LLM filters irrelevant results
2. **Transcribe** — `yt-dlp` extracts chapters, `youtube-transcript-api` downloads subtitles, `reportlab` generates PDFs
3. **Embed** — PDFs are split into parent/child chunks, embedded with `all-MiniLM-L6-v2`, stored in Chroma
4. **Query** — Ensemble retriever (Chroma vector search + BM25 keyword search) returns top chunks, re-ranked by parent relevance
5. **Answer** — QA Agent synthesizes a response with citations

---

## Dependencies

See `requirements.txt` for pinned versions. Key packages:

| Package | Purpose |
|---|---|
| `crewai` | Multi-agent orchestration |
| `openai` | DeepSeek API client |
| `selenium` | YouTube search scraping |
| `yt-dlp` | Video metadata & chapter extraction |
| `youtube-transcript-api` | Subtitle download |
| `langchain-chroma` | Vector store |
| `langchain-huggingface` | Sentence-transformer embeddings |
| `langchain-community` | BM25 retriever, PDF loader |
| `langchain-text-splitters` | Document chunking |
| `reportlab` | PDF generation |
| `pyprojroot` | Project root resolution |
| `pydantic` | Data validation |
| `pyyaml` | Config file parsing |

---

## License

MIT License. For personal and educational use. Respect YouTube's Terms of Service when extracting content.
