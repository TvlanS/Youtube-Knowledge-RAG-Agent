import json
import os
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from pyprojroot import here
from tools.Ingestion_pipeline import ingestion
from tools.catalog_lookup_tool import CatalogLookupTool
from tools.rag_query_tool import RAGQueryTool as _RAGQueryTool


class IngestionInput(BaseModel):
    input: str = Field(description="The topic or keyword to search for on YouTube")
    max_videos: int = Field(default=10, description="Maximum number of videos to retrieve")


class CatalogInput(BaseModel):
    input: str = Field(description="The user's question to find a matching topic in the catalog")


class RAGQueryInput(BaseModel):
    query: str = Field(description="The user's question to answer from the RAG store")
    topic_slug: str = Field(description="The catalog id returned by the catalog lookup tool")
    k: int = Field(default=10, description="Number of context chunks to retrieve")
    use_alt_query: bool = Field(default=True, description="Whether to generate an alternative query for better recall")


class IngestionTool(BaseTool):
    name: str = "Youtube video collector"
    description: str = (
        "Webscrapes, transcribes and embeds YouTube videos into a RAG knowledge base. "
        "Use this when the user wants to gather or collect information from YouTube."
    )
    args_schema: Type[BaseModel] = IngestionInput

    def _run(self, input: str, max_videos: int = 10) -> str:
        results = ingestion(input, max_videos).run()
        return str(results)


class CatalogTool(BaseTool):
    name: str = "Video Catalog reviewer"
    description: str = (
        "Searches the video catalog to find the correct topic id matching the user's question. "
        "Always call this BEFORE the RAG query tool — never guess the topic id."
    )
    args_schema: Type[BaseModel] = CatalogInput

    def _run(self, input: str) -> str:
        results = CatalogLookupTool().run(input)
        return str(results)


class CatalogListInput(BaseModel):
    pass


class CatalogListTool(BaseTool):
    name: str = "catalog_list"
    description: str = (
        "Returns the full list of topics that have been ingested into the knowledge base. "
        "Use this when the user asks what topics are available, what has been collected, "
        "or what is in the knowledge base."
    )
    args_schema: Type[BaseModel] = CatalogListInput

    def _run(self, **kwargs) -> str:
        catalog_path = os.path.join(here(), "data", "video_catalog.json")
        if not os.path.exists(catalog_path):
            return "No topics have been ingested yet."
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        if not catalog:
            return "No topics have been ingested yet."
        lines = [f"- {entry['id']}: {entry['description']}" for entry in catalog]
        return "Available topics:\n" + "\n".join(lines)


class RAGQueryTool(BaseTool):
    name: str = "RAG query tool"
    description: str = (
        "Queries the RAG vector store for a given topic and returns relevant context "
        "from transcribed YouTube videos. Requires the catalog id from the catalog lookup tool. "
        "Always call the catalog lookup tool first to get the correct topic_slug."
    )
    args_schema: Type[BaseModel] = RAGQueryInput

    def _run(self, query: str, topic_slug: str, k: int = 10, use_alt_query: bool = True) -> str:
        result = _RAGQueryTool().run(query=query, topic_slug=topic_slug, k=k, use_alt_query=use_alt_query)
        if result["status"] == "success":
            return result["context"]
        return f"ERROR: rag_query failed — {result['message']}"
