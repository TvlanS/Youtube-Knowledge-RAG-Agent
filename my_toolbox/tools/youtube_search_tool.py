import json
import os
import re
import time
import yaml
import pyprojroot
from datetime import datetime

from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

root = pyprojroot.here()


class YouTubeSearchTool:
    def __init__(self, search_query: str, max_videos: int = 10):
        self.search_query = search_query
        self.max_videos = max_videos
        self._load_config()

    def _load_config(self):
        config_path = os.path.join(root, "my_toolbox", "config", "llm_config.yml")
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.api_key = config["deepseek"]["api_key"]
        self.website_url = config["deepseek"]["website_url"]
        self.summariser_prompt = config["prompt"]["summariser_prompt"]
        self.filter_prompt = config["prompt"]["filter_prompt"]

    def run(self) -> str:
        videos = self._scrape_youtube()
        if not videos:
            return "No videos found."

        topic_slug = re.sub(r"[^\w\s-]", "", self.search_query).strip()
        topic_slug = re.sub(r"\s+", "_", topic_slug).lower()

        description = self._get_llm_description(videos)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{topic_slug}_{timestamp}.json"
        catalog_id = os.path.splitext(filename)[0]

        # Save original results
        original_dir = os.path.join(root, "data", "original_search_results")
        os.makedirs(original_dir, exist_ok=True)
        original_path = os.path.join(original_dir, filename)

        original_data = {
            "id": catalog_id,
            "description": description,
            "topic": self.search_query,
            "topic_slug": topic_slug,
            "searched_at": datetime.now().isoformat(),
            "total": len(videos),
            "videos": [
                {
                    "title": v["title"],
                    "url": v["url"],
                    "transcribed": False,
                    "transcript_path": None,
                    "embedded": False,
                }
                for v in videos
            ],
        }

        with open(original_path, "w", encoding="utf-8") as f:
            json.dump(original_data, f, ensure_ascii=False, indent=2)
        print(f"Original saved ({len(videos)} videos): {original_path}")

        # Filter irrelevant videos
        irrelevant_titles = self._get_irrelevant_titles(videos)
        filtered_videos = [v for v in videos if v["title"] not in irrelevant_titles]
        print(f"Filtered out {len(irrelevant_titles)} irrelevant videos, {len(filtered_videos)} remaining.")

        # Save filtered results
        filtered_dir = os.path.join(root, "data", "filtered_search_results")
        os.makedirs(filtered_dir, exist_ok=True)
        filtered_path = os.path.join(filtered_dir, filename)

        filtered_data = {
            "id": catalog_id,
            "description": description,
            "topic": self.search_query,
            "topic_slug": topic_slug,
            "searched_at": datetime.now().isoformat(),
            "total": len(filtered_videos),
            "videos": [
                {
                    "title": v["title"],
                    "url": v["url"],
                    "transcribed": False,
                    "transcript_path": None,
                    "embedded": False,
                }
                for v in filtered_videos
            ],
        }

        with open(filtered_path, "w", encoding="utf-8") as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
        print(f"Filtered saved ({len(filtered_videos)} videos): {filtered_path}")

        self._update_catalog(catalog_id, description)

        return filtered_path

    def _update_catalog(self, catalog_id: str, description: str) -> None:
        catalog_path = os.path.join(root, "data", "video_catalog.json")
        if os.path.exists(catalog_path):
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        else:
            catalog = []

        catalog = [entry for entry in catalog if entry.get("id") != catalog_id]
        catalog.append({"id": catalog_id, "description": description})

        with open(catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        print(f"Catalog updated: {catalog_path}")

    def _scrape_youtube(self) -> list:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--lang=en")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        driver = webdriver.Chrome(options=chrome_options)
        results = []

        try:
            url = f"https://www.youtube.com/results?search_query={self.search_query.replace(' ', '+')}"
            print(f"Searching: {url}")
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-video-renderer"))
            )

            last_count = 0
            while len(results) < self.max_videos:
                elements = driver.find_elements(
                    By.CSS_SELECTOR, "ytd-video-renderer a#video-title"
                )
                for el in elements:
                    title = el.get_attribute("title")
                    href = el.get_attribute("href")
                    if title and href and {"title": title, "url": href} not in results:
                        results.append({"title": title, "url": href})
                    if len(results) >= self.max_videos:
                        break

                if len(results) >= self.max_videos:
                    break
                if len(results) == last_count:
                    print("No new videos after scroll, stopping.")
                    break
                last_count = len(results)
                driver.execute_script("window.scrollBy(0, 1500);")
                time.sleep(2)
        finally:
            driver.quit()

        return results[:self.max_videos]

    def _get_llm_description(self, videos: list) -> str:
        titles_text = "\n".join(f"- {v['title']}" for v in videos)
        user_message = f"Search topic: {self.search_query}\n\nVideo titles:\n{titles_text}"

        client = OpenAI(api_key=self.api_key, base_url=self.website_url)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": self.summariser_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content

    def _get_irrelevant_titles(self, videos: list) -> list:
        titles_text = "\n".join(f"- {v['title']}" for v in videos)
        user_message = f"Search keyword: {self.search_query}\n\nVideo titles:\n{titles_text}"

        client = OpenAI(api_key=self.api_key, base_url=self.website_url)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": self.filter_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        raw = response.choices[0].message.content

        # Extract the JSON array from the response robustly
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if not match:
            print("Filter LLM returned no parseable list, skipping filter.")
            return []
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            print(f"Failed to parse filter response: {raw}")
            return []


if __name__ == "__main__":
    tool = YouTubeSearchTool(search_query="Crew AI Tutorial", max_videos=10)
    path = tool.run()
    print(f"Filtered result saved to: {path}")
