import io
from typing import BinaryIO, List


def parse_codes_txt(file_like: BinaryIO) -> List[int]:
    """
    Parses a text file containing a list of CNPs (one per line).
    
    Discards headers, blank lines, and non-numeric lines silently.
    Decodes using UTF-8 with 'replace' for invalid characters.
    
    Args:
        file_like: A binary file-like object (e.g., UploadedFile from Streamlit).
        
    Returns:
        A list of integers representing the extracted CNPs.
    """
    try:
        content = file_like.read().decode("utf-8", errors="replace")
        if content.startswith('\ufeff'):
            content = content[1:]
    except Exception:
        # Fallback if read fails for some reason
        return []

    codes = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.isdigit():
            codes.append(int(stripped))
            
    return codes
