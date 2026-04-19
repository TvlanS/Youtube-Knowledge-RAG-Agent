from youtube_transcript_api import YouTubeTranscriptApi


class subtitle_extract():
    def __init__(self, video_url: str):
        self.video_url = video_url

    def subtitle(self):
        video_id = self.video_url.split("=")[1].split("&")[0]
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=['en', 'hi'])
        return transcript
    
