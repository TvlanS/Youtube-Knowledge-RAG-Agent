#!/usr/bin/env python
import sys
from pyprojroot import here
sys.path.insert(0, str(here("my_toolbox")))
sys.path.insert(0, str(here("my_toolbox/utils")))
sys.path.insert(0, str(here("src")))
import warnings

from datetime import datetime

from agent_youtube_knowledge_rag.crew import AgentYoutubeKnowledgeRag

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    crew = AgentYoutubeKnowledgeRag().crew()
    print("YouTube Knowledge Agent ready. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye.")
            break

        try:
            result = crew.kickoff(inputs={"question": user_input})
            print(f"\nAgent: {result}\n")
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    run()


