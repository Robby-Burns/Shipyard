import re
from typing import List, Dict, Any

def extract_tags(content: str, tag_name: str) -> List[Dict[str, Any]]:
    """
    Extracts content and attributes for all matching HTML/XML style tags.
    Handles:
    - Single quotes, double quotes, or no quotes for attributes
    - Whitespaces inside tags (e.g., <tag  attr = "val" >)
    - Unclosed tags (reads until the next opening tag or end of document)
    - Stripping of markdown code blocks enclosing the content (e.g. ```xml ... ```)
    """
    results = []
    # Find all starts of the tag (case-insensitive)
    tag_pattern = re.compile(rf"<{tag_name}\b", re.IGNORECASE)
    opening_matches = list(tag_pattern.finditer(content))
    
    for i, start_match in enumerate(opening_matches):
        start_idx = start_match.start()
        
        # Find the closing bracket of this opening tag
        bracket_end = content.find(">", start_idx)
        if bracket_end == -1:
            continue
            
        tag_header = content[start_idx:bracket_end]
        
        # Extract attributes
        attributes = {}
        attr_pattern = re.compile(r"(\w+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))")
        for attr_match in attr_pattern.finditer(tag_header):
            name = attr_match.group(1).lower()
            val = attr_match.group(2) or attr_match.group(3) or attr_match.group(4)
            attributes[name] = val
            
        # Determine where the body of the tag ends
        # Look for the closing tag </tag_name>
        close_tag = f"</{tag_name}>"
        close_idx = content.lower().find(close_tag.lower(), bracket_end + 1)
        
        if close_idx != -1:
            # Found standard closing tag
            body = content[bracket_end + 1:close_idx]
        else:
            # Unclosed tag fallback: read until the next opening tag of the same name, or end of doc
            next_opening_idx = opening_matches[i+1].start() if i + 1 < len(opening_matches) else len(content)
            body = content[bracket_end + 1:next_opening_idx]
            
        # Clean body of markdown blocks if they wrap the entire content
        body_clean = body.strip()
        if body_clean.startswith("```"):
            # Remove the opening code fence and language identifier line
            lines = body_clean.splitlines()
            if lines:
                # e.g., ```mermaid -> remove first line
                lines_clean = lines[1:]
                # remove closing ``` if it exists at the end
                if lines_clean and lines_clean[-1].strip() == "```":
                    lines_clean = lines_clean[:-1]
                body_clean = "\n".join(lines_clean).strip()
                
        results.append({
            "content": body_clean,
            "attributes": attributes
        })
        
    return results

def parse_agent_decision(
    content: str,
    tag_name: str,
    status_keys: List[str] = ["status", "qa_status", "challenge_status"],
    reason_keys: List[str] = ["reason", "challenge_reason"]
) -> Dict[str, Any]:
    """
    Parses agent decisions, supporting both structured JSON outputs and fallback XML tags.
    """
    import json
    cleaned = content.strip()
    
    # Try parsing as JSON first
    # Strip markdown code fences if LLM wrapped JSON in ```json ... ```
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            lines_clean = lines[1:]
            if lines_clean and lines_clean[-1].strip() == "```":
                lines_clean = lines_clean[:-1]
            cleaned = "\n".join(lines_clean).strip()
            
    try:
        # If it looks like a JSON object
        if (cleaned.startswith("{") and cleaned.endswith("}")) or (cleaned.startswith("[") and cleaned.endswith("]")):
            data = json.loads(cleaned)
            if isinstance(data, dict):
                # Resolve status
                status = None
                for k in status_keys:
                    if k in data:
                        status = str(data[k]).strip()
                        break
                # Resolve reason
                reason = None
                for k in reason_keys:
                    if k in data:
                        reason = str(data[k]).strip()
                        break
                if status is not None:
                    return {"status": status, "reason": reason, "format": "json"}
    except Exception:
        pass

    # Fallback to XML tag extraction
    tags = extract_tags(content, tag_name)
    if tags:
        # Check attributes first
        status = tags[0]["attributes"].get("status")
        reason = tags[0]["attributes"].get("reason")
        
        # If not in attributes, check content (e.g. <qa_status>PASSED</qa_status>)
        if not status:
            status = tags[0]["content"].strip()
            
        return {"status": status, "reason": reason, "format": "xml"}
        
    return {"status": None, "reason": None, "format": "unknown"}
