import re
from pathlib import Path

def read_version_from_version_txt(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"StringStruct\('FileVersion', '([^']+)'\)", text)
    if m:
        return m.group(1)
    # Fallback to semantic version in RELEASE_NOTES if available
    notes = Path("RELEASE_NOTES_v1.0.0.md")
    if notes.exists():
        m2 = re.search(r"v(\d+\.\d+\.\d+)", notes.read_text(encoding="utf-8", errors="ignore"))
        if m2:
            return m2.group(1)
    return "1.0.0"

if __name__ == "__main__":
    version_file = Path("version.txt")
    print(read_version_from_version_txt(version_file))