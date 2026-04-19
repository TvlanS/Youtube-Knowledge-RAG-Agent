import json
from tools.youtube_search_tool import YouTubeSearchTool
from tools.youtube_transcriber_tool import YouTubeTranscriberTool
from tools.rag_embed_tool import RAGEmbedTool


class ingestion():
    def __init__(self, topic: str,max_videos: int = 10
    ):
        self.topic = topic
        self.max_videos = max_videos

    def run(self):
        search = YouTubeSearchTool(self.topic, self.max_videos)
        search_output = search.run()

        with open(search_output, "r", encoding="utf-8") as f:
            catalog_id = json.load(f)["id"]

        transcribe = YouTubeTranscriberTool(search_output)
        path = transcribe.run()
        tool = RAGEmbedTool()
        tool.run(path[1], catalog_id=catalog_id)
        return f"Ingestion complete. Topic: '{self.topic}', catalog_id: '{catalog_id}', folder: {path[1]}"




