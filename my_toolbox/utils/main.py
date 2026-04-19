from metadata_extract import Metadata_Extracter
from sub_sorter import Sub_Sorter
from subtitle_extract import subtitle_extract
import pyprojroot
import os
import re
import random
import time


class YT_Pipeline:
    def __init__(self,url):
        self.url = url
    def run(self):
        meta = Metadata_Extracter(self.url)
        sub = subtitle_extract(self.url)

        meta = meta.extract_chapters_yt_dlp()
        time.sleep(random.randint(10,15))
        sub = sub.subtitle()
        
        root = pyprojroot.here()
        base_dir = os.path.join(root,"Video_Folder")
        folder_name = re.sub(r'[\\/*?:"<>|]',"_",meta["title"]).strip()
        folder_path  = os.path.join(base_dir,folder_name)

        os.makedirs(folder_path,exist_ok=True)
        base_dir = folder_path
        sorter = Sub_Sorter(folder_path,meta,sub)
        sorter.sorter()

# extract meta data
# extract subtitle
# merge both 
# create a folder for the subtitle

if __name__ == "__main__":
    url = rf"https://www.youtube.com/watch?v=OGIiGg8qKFg"
    pipeline = YT_Pipeline(url)
    pipeline.run()