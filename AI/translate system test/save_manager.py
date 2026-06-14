from datetime import datetime
from pathlib import Path

SAVE_DIR = Path("documents")

SAVE_DIR.mkdir(exist_ok=True)

def save_documents(korean, english):

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    ko_file = SAVE_DIR / f"{timestamp}_ko.md"
    en_file = SAVE_DIR / f"{timestamp}_en.md"

    ko_file.write_text(
        korean,
        encoding="utf-8"
    )

    en_file.write_text(
        english,
        encoding="utf-8"
    )

    return ko_file, en_file
