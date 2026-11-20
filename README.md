# Fetch-Decode-Execute & Interrupt Cycle (Manim Animation)
---

## Installation & Requirements

Ensure you have Python 3.10+ installed along with `ffmpeg` and `pango`:

### macOS (Homebrew)
```bash
brew install ffmpeg pango
```

### Install Manim
```bash
# In your virtual environment:
pip install manim
```

---

## How to Render

Run the commands below from the project folder:

### Quick Preview (Low Quality, 480p 15fps)
```bash
manim -pql FDE.py FDE
```

### Final Render (High Quality, 1080p 60fps)
```bash
manim -pqh FDE.py FDE
```

Rendered videos are automatically saved in `media/videos/FDE/`.