import unicodedata

def normalize_text(s: str) -> str:
    # Replace smart quotes, dashes, etc.
    replacements = {
        "’": "'", "‘": "'", "‛": "'", "‚": "'",
        "“": '"', "”": '"', "„": '"', "‟": '"',
        "–": "-", "—": "-", "―": "-",
        "…": "...",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)

    # Normalize and reduce to ASCII
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return s.strip().lower()
