import json
import os
import re
import sys
import time
import random
import pyprojroot
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

root = pyprojroot.here()
sys.path.insert(0, str(os.path.join(root, "utils")))

from metadata_extract import Metadata_Extracter
from subtitle_extract import subtitle_extract


class YouTubeTranscriberTool:
    def __init__(self, search_results_path: str):
        self.search_results_path = search_results_path

    def run(self) -> str:
        with open(self.search_results_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        topic_slug = data["topic_slug"]
        run_dt = datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_folder = os.path.join(root, "data", "transcripts", f"{topic_slug}_{run_dt}")
        transcribed_count = 0
        failed = []

        for i, video in enumerate(data["videos"]):
            if video["transcribed"]:
                continue

            url = video["url"]
            title = video["title"]
            print(f"Transcribing: {title}")

            try:
                meta = Metadata_Extracter(url).extract_chapters_yt_dlp()
                time.sleep(10)
                if i > 0 and i % 5 == 0:
                    print(f"Cooldown: waiting 15 seconds...")
                    time.sleep(15)
                sub = subtitle_extract(url).subtitle()

                safe_title = re.sub(r'[<>:"/\\|?*]', "", title.replace(" ", "_"))[:50]
                transcript_dir = os.path.join(topic_folder, safe_title)
                os.makedirs(transcript_dir, exist_ok=True)

                json_path = os.path.join(transcript_dir, "transcript.json")
                pdf_path = os.path.join(transcript_dir, "transcript.pdf")

                transcript_data = self._build_transcript(meta, sub, topic_slug, url, safe_title)

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(transcript_data, f, ensure_ascii=False, indent=4)

                self._write_pdf(transcript_data, pdf_path)

                video["transcribed"] = True
                video["transcript_path"] = json_path
                transcribed_count += 1
                print(f"Done: {safe_title}")

            except Exception as e:
                failed.append(f"{title}: {e}")
                print(f"Failed: {title} — {e}")

        with open(self.search_results_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        summary = f"Transcribed {transcribed_count}/{len(data['videos'])} videos."
        if failed:
            summary += f" Failed: {failed}"
        summary += f" | Folder: {topic_folder}"
        return summary, topic_folder

    def _build_transcript(self, meta: dict, sub, topic_slug: str, source_url: str, title: str) -> dict:
        base = {
            "title_name": title,
            "topic_slug": topic_slug,
            "source_url": source_url,
            "transcribed_at": datetime.now().isoformat(),
        }

        chapters = meta.get("chapters", {})

        if not chapters:
            base["has_chapters"] = False
            base["chapters"] = [
                {
                    "chapter_number": 1,
                    "chapter_title": title,
                    "timeline": None,
                    "chapter_text": " ".join(item.text for item in sub),
                }
            ]
            return base

        cc = {snippet.start: snippet.text for snippet in sub}
        keys_video = list(cc.keys())
        keys_chap = list(chapters.keys())

        positions = []
        for index, chap_start in enumerate(keys_chap):
            prev = keys_chap[index - 1] if index > 0 else 0
            for i, vid_time in enumerate(keys_video):
                if prev <= chap_start <= vid_time:
                    positions.append(i)
                    break
        positions.append(len(keys_video) - 1)

        chapter_list = []
        for index, chap_time in enumerate(keys_chap):
            start = positions[index]
            end = positions[index + 1] if index + 1 < len(positions) else len(sub)
            chapter_list.append(
                {
                    "chapter_number": index + 1,
                    "chapter_title": chapters[chap_time],
                    "timeline": f"{chap_time / 60:.2f}",
                    "chapter_text": " ".join(item.text for item in sub[start:end]),
                }
            )

        base["has_chapters"] = True
        base["chapters"] = chapter_list
        return base

    def _write_pdf(self, data: dict, pdf_path: str) -> None:
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            name="TitleStyle", fontSize=18, leading=22, spaceAfter=12, alignment=1
        )
        heading_style = ParagraphStyle(
            name="HeadingStyle", fontSize=14, leading=18, spaceAfter=8, textColor="blue"
        )
        normal_style = styles["Normal"]

        story = [Paragraph(data["title_name"], title_style), Spacer(1, 12)]

        for chap in data["chapters"]:
            story.append(
                Paragraph(
                    f"<b>Chapter {chap['chapter_number']}: {chap['chapter_title']}</b>",
                    heading_style,
                )
            )
            timeline_display = chap["timeline"] if chap["timeline"] else "N/A"
            story.append(Paragraph(f"<b>Timeline:</b> {timeline_display} min", normal_style))
            story.append(Spacer(1, 6))
            story.append(Paragraph(chap["chapter_text"], normal_style))
            story.append(Spacer(1, 12))

        doc.build(story)


if __name__ == "__main__":
    path = r"data/filtered_search_results/crew_ai_tutorial_20260417_083126.json"
    tool = YouTubeTranscriberTool(search_results_path=path)
    print(tool.run())
