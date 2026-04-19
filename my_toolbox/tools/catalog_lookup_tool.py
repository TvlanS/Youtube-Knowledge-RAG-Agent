import json
import os
import re
import yaml
from openai import OpenAI
from pyprojroot import here

root = here()

_RECENT_PATH  = os.path.join(root, "data", "recent_topics.json")
_CATALOG_PATH = os.path.join(root, "data", "video_catalog.json")


class CatalogLookupTool:

    def __init__(self):
        self._load_config()

    def _load_config(self):
        config_path = os.path.join(root, "my_toolbox", "config", "llm_config.yml")
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.api_key      = config["deepseek"]["api_key"]
        self.website_url  = config["deepseek"]["website_url"]
        self.lookup_prompt = config["prompt"]["catalog_lookup_prompt"]

    def run(self, query: str) -> dict:
        # Step 1: check recent topics (fast path)
        recent = self._load_json(_RECENT_PATH)
        if recent:
            match_id = self._llm_match(query, recent)
            if match_id:
                return {"status": "success", "id": match_id, "source": "recent"}

        # Step 2: full catalog scan
        catalog = self._load_json(_CATALOG_PATH)
        if not catalog:
            return {"status": "error", "message": "No catalog found. Run a search first."}

        match_id = self._llm_match(query, catalog)
        if match_id:
            return {"status": "success", "id": match_id, "source": "catalog"}

        return {"status": "error", "message": "No matching topic found in catalog for this query."}

    def _llm_match(self, query: str, entries: list) -> str | None:
        entries_text = "\n".join(
            f"- id: {e['id']}\n  description: {e['description']}" for e in entries
        )
        user_message = f"Query: {query}\n\nAvailable topics:\n{entries_text}"

        client = OpenAI(api_key=self.api_key, base_url=self.website_url)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": self.lookup_prompt},
                {"role": "user",   "content": user_message},
            ],
        )
        raw = response.choices[0].message.content

        match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
            matched = data.get("matched_id")
            return matched if isinstance(matched, str) else None
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _load_json(path: str) -> list:
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


if __name__ == "__main__":
    tool = CatalogLookupTool()
    result = tool.run("Sadhguru Videos")
    print(result)
