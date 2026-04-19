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


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        AgentYoutubeKnowledgeRag().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        AgentYoutubeKnowledgeRag().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        AgentYoutubeKnowledgeRag().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = AgentYoutubeKnowledgeRag().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
    
if __name__ == "__main__":
    run()


