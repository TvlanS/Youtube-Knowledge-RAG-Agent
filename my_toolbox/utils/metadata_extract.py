import yt_dlp
import re
import os
import pickle


class Metadata_Extracter():

    def __init__(self,video_url: str):
        self.video_url = video_url
        self.metadata = {}
    
    @staticmethod
    def remove_emojis(text):  # Removes emojis and special pictographs
        emoji_pattern = re.compile(
            "[" 
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002700-\U000027BF"  # dingbats
            "\U000024C2-\U0001F251"  # enclosed characters
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001FA70-\U0001FAFF"  # more recent emojis
            "]+", flags=re.UNICODE
        )
        cleaned = emoji_pattern.sub('', text)
        # Also remove stray extra spaces left by emoji removal
        return re.sub(r'\s{2,}', ' ', cleaned).strip()
    
    @staticmethod
    def time_to_seconds(time_str: str) -> int: # Convert chapter time to sec to match the cc time format
    
        parts = time_str.split(':')
        parts = [int(p) for p in parts]
        
        # If format is MM:SS
        if len(parts) == 2:
            minutes, seconds = parts
            return minutes * 60 + seconds
        # If format is HH:MM:SS
        elif len(parts) == 3:
            hours, minutes, seconds = parts
            return hours * 3600 + minutes * 60 + seconds
        else:
            raise ValueError(f"Invalid time format: {time_str}")
    
    @staticmethod
    def sanitize_filename(name):  # Title Sanitization
        name = name.replace(" ","_") 
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        return name[:50]
    
    def extract_chapters_yt_dlp(self): # extrct chapters
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'forcejson': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.video_url, download=False)
            description = info.get('description', '') # getting description
            titles = info.get('title',"") # getting title
            keywords = info.get('tags', []) # extracting keywords


            pattern = r'(\d{1,2}:\d{2}(?::\d{2})?)\s+(.*)'
            description = self.remove_emojis(description)
            matches = re.findall(pattern, description) # etracting chapter raw

            try:
                chapter = {self.time_to_seconds(timestamp): desc for timestamp, desc in matches}
            except:
                pass
            

        
        title = self.sanitize_filename(titles) # sanitize title

        
        try : 
            self.metadata = {
                "title" : title,
                "keywords": keywords,
                "chapters": chapter
                }

        except:
        
            self.metadata = {
            "title" : title}

            print("No chapters found !")
        
        
        print("Meta Data Collection Completed !!!")
        print(self.metadata)
        return self.metadata
    

if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=BtKCXw24LRo"
    extract = Metadata_Extracter(url)
    meta = extract.extract_chapters_yt_dlp()
    print(meta)