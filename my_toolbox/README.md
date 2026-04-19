# YouTube Text Transcription & Chapter Extraction Tool

A Python tool that extracts subtitles, metadata, and chapter information from YouTube videos, then merges them into structured JSON and PDF outputs. Perfect for creating readable transcripts organized by video chapters. Tool was intended for LLM analytics.

## ✨ Features

- **Metadata Extraction**: Fetches video title, keywords, and chapter timestamps from YouTube descriptions using `yt-dlp`.
- **Subtitle Download**: Retrieves English or Hindi subtitles via `youtube-transcript-api`.
- **Chapter‑Aware Sorting**: Aligns subtitles with video chapters, producing a chapter‑by‑chapter transcript.
- **Multi‑Format Output**: Generates both JSON (for programmatic use) and PDF (for reading/printing) files.
- **Pipeline Architecture**: Simple, reusable `YT_Pipeline` class that orchestrates the whole process.

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/yt-text-transcription.git
   cd yt-text-transcription
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

### Quick Start

1. Open a Python interpreter or script in the project root.
2. Import the pipeline and run it with a YouTube URL:

```python
from utils.pipeline import YT_Pipeline

url = "https://www.youtube.com/watch?v=..."
pipeline = YT_Pipeline(url)
pipeline.run()
```

### Basic Python API

The `YT_Pipeline` class orchestrates the entire workflow:

The script will:
- Extract video metadata (title, chapters, keywords).
- Download available subtitles.
- Create a folder under `Video_Folder/` named after the video.
- Save a structured JSON file (`sortedjson_*.json`) and a formatted PDF (`sortedpdf_*.pdf`) inside that folder.

### Example Output Structure

```
Video_Folder/
└── Video_Title/
    ├── sortedjson_Video_Title.json
    └── sortedpdf_Video_Title.pdf
```

The JSON file contains:
```json
{
  "title_name": "Video Title",
  "chapters": [
    {
      "chapter_number": 1,
      "chapter_title": "Introduction",
      "timeline": "0.0 minute",
      "chapter_text": "Full transcript text for this chapter..."
    },
    ...
  ]
}
```

If no chapters are found, a flat transcript is produced.

## 📁 Project Structure

```
.
├── utils/                    # Core modules
│   ├── metadata_extract.py   # Extract video metadata & chapters
│   ├── subtitle_extract.py   # Fetch subtitles
│   ├── sub_sorter.py         # Merge metadata & subtitles, generate JSON/PDF
│   └── pipeline.py           # Orchestration class
├── Video_Folder/             # Output directory (auto‑created)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🔧 Dependencies

- [yt‑dlp](https://github.com/yt-dlp/yt-dlp) – YouTube metadata extraction.
- [youtube‑transcript‑api](https://pypi.org/project/youtube-transcript-api/) – Subtitle retrieval.
- [reportlab](https://www.reportlab.com/) – PDF generation.
- [pyprojroot](https://pypi.org/project/pyprojroot/) – Project‑root detection.

See `requirements.txt` for pinned versions.

## 🧪 Testing

Run the example in `pipeline.py`:

```bash
python utils/pipeline.py
```

This processes a sample YouTube video and writes outputs to `Video_Folder/`.

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request for:

- Bug fixes
- New features (CLI, Gradio UI, etc.)
- Documentation improvements
- Performance optimizations

## 📄 License

MIT License. See [LICENSE](LICENSE) file (if present) for details.

---

**Note**: This tool is intended for personal/educational use. Respect YouTube’s Terms of Service and copyright laws when using extracted content.