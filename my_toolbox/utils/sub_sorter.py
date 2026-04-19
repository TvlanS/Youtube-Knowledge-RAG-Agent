import pickle 
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

class Sub_Sorter():
        def __init__(self,folder,meta,sub):
            self.folder = folder
            self.meta = meta
            self.sub = sub
            pass
        # txt_file , pdf_file , folder
        
        @staticmethod
        def json_to_pdf(json_path, pdf_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(name="Title", fontSize=18, leading=22, spaceAfter=12, alignment=1)
            heading_style = ParagraphStyle(name="Heading", fontSize=14, leading=18, spaceAfter=8, textColor="blue")
            normal_style = styles["Normal"]

            story = []
            story.append(Paragraph(data["title_name"], title_style))
            story.append(Spacer(1, 12))

            if "chapters" in data :
                for chap in data["chapters"]:
                    story.append(Paragraph(f"<b>Chapter {chap['chapter_number']}: {chap['chapter_title']}</b>", heading_style))
                    story.append(Paragraph(f"<b>Timeline:</b> {chap['timeline']} minute", normal_style))
                    story.append(Spacer(1, 6))
                    story.append(Paragraph(chap["chapter_text"], normal_style))
                    story.append(Spacer(1, 12))
            else:
                    story.append(Paragraph(f"<b>Title : {data['title_name']}</b>", heading_style))
                    story.append(Spacer(1, 6))
                    story.append(Paragraph(data["Transcript"], normal_style))

            doc.build(story)

        def skipped_sorter(self):

            json_path = os.path.join(self.folder, f"sortedjson_{self.meta['title']}.json")
            pdf_path = os.path.join(self.folder, f"sortedpdf_{self.meta['title']}.pdf")

            text = " ".join(item.text for item in self.sub)
            data = {"title_name": self.meta["title"],
                    "Transcript" : str(text)}
            
            with open(json_path, "w", encoding="utf-8") as f: # Paste to text file
                json.dump(data,f,indent=4)
                
                print("Json file created")

            self.json_to_pdf(json_path,pdf_path)

            print("PDF file created")

            return print("Files Generated Have Fun")


        def sorter(self):
            # Load metadata

            if "chapters" not in self.meta or not self.meta["chapters"] or len(self.meta["chapters"]) == 0:
                return self.skipped_sorter()

            if self.meta:
                chapters = self.meta["chapters"]
                print(f"Loaded metadata!")
            else:
                print("No metadata file found!")

            # Load subtitles
            if self.sub:
                print(f"Loaded subtitles")
            else:
                print("No subtitle file found!")

            cc ={}

            for snippet in self.sub:
                cc[snippet.start] = snippet.text # Create a dictionary of time and text


            keys_chap = list(chapters.keys())  # Extract the chapter timeline only
            keys_video = list(cc.keys()) # Extract the video timeline only


            # Convert keys
            chapters_in_seconds = {k: v for k, v in chapters.items()} #Remap the chapter to seconds this time

            keys_chap = list(chapters_in_seconds.keys())  # Extract the chapter timeline only from new dictionary

            pos = [] # New list for the positions of chapter in the transcript , start with 0 as beginning of video for intro
            rem = [0]

            for index,chaps in enumerate(chapters_in_seconds.keys()): # Finds the position in transcription for each chapter
                for indexs , vidlen in enumerate(keys_video):
                    try : 
                        previouslen = keys_video[index-1] if index > 0 else 0
                    except :
                        pass

                    if previouslen <= chaps and vidlen >= chaps:
                        pos.append(indexs) ## change to +1 or -1
                        rem.append(round(vidlen-chaps,1))
                        break


            pos.append(len(keys_video)-1) # Add the end of the video since last chapter has no closer
            chapter_data_list =[]


            json_path = os.path.join(self.folder, f"sortedjson_{self.meta['title']}.json")
            pdf_path = os.path.join(self.folder, f"sortedpdf_{self.meta['title']}.pdf")

            with open(json_path, "w", encoding="utf-8") as f: # Paste to text file
                for index, chap_time in enumerate(keys_chap):
                    start_chap = pos[index]

                    try:
                        end_chap = pos[index + 1]
                    except IndexError:
                        end_chap = len(self.sub)  # If at the last chapter, set end_chap to end of transcript

                    chap_transcript = " ".join(item.text for item in self.sub[start_chap:end_chap])

                    chapter_entry = {
                    "chapter_number": index + 1,
                    "chapter_title": chapters_in_seconds[chap_time],
                    "timeline": rf"{chap_time/60} minute",
                    "chapter_text": chap_transcript,
                    }
                    chapter_data_list.append(chapter_entry)

                data = {
                "title_name": self.meta["title"],
                "chapters": chapter_data_list,
                }
                
                json.dump(data,f,indent=4)
                
                print("Json file created")

            self.json_to_pdf(json_path,pdf_path)

            print("PDF file created")

            return print("Files Generated Have Fun")
        
        