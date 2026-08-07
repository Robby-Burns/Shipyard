import re

def sanitize_path_component(component: str) -> str:
    """Return a safe filesystem component.
    Allows only alphanumeric characters, hyphens and underscores.
    Strips leading/trailing separators and rejects path traversal tokens.
    """
    component = component.lower()
    cleaned = re.sub(r"[^a-z0-9_-]", "_", component)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        raise ValueError("Path component is empty after sanitization")
    if ".." in cleaned:
        raise ValueError("Path component contains prohibited '..' sequence")
    return cleaned
