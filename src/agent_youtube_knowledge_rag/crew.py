from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from agent_youtube_knowledge_rag.tools.custom_tool import IngestionTool, CatalogTool, RAGQueryTool, CatalogListTool
from utils.config_setup import Config

config = Config()


@CrewBase
class AgentYoutubeKnowledgeRag():
    """AgentYoutubeKnowledgeRag crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    def _llm(self) -> LLM:
        return LLM(
            model="deepseek-chat",
            api_key=config.api_key,
            base_url="https://api.deepseek.com/v1"
        )

    @agent
    def manager(self) -> Agent:
        return Agent(
            config=self.agents_config['manager'],
            llm=self._llm(),
            allow_delegation=True,
            verbose=True,
        )

    @agent
    def ingestion(self) -> Agent:
        return Agent(
            config=self.agents_config['ingestion'],
            llm=self._llm(),
            tools=[IngestionTool()],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def qa(self) -> Agent:
        return Agent(
            config=self.agents_config['qa'],
            llm=self._llm(),
            tools=[CatalogListTool(), CatalogTool(), RAGQueryTool()],
            allow_delegation=False,
            verbose=True,
        )

    @task
    def ingestion_task(self) -> Task:
        return Task(config=self.tasks_config['ingestion_task'])

    @task
    def qa_task(self) -> Task:
        return Task(config=self.tasks_config['qa_task'])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.ingestion(), self.qa()],
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.manager(),
            memory=True,
            verbose=True,
        )
