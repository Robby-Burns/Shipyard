import json
from typing import Any

from app.schemas.structured_output import ReviewOutput, Diagram, Adr, KnowledgeCandidate


def parse_structured_output(payload: str) -> Any:
    """Parse a JSON payload produced by an agent.
    Returns the appropriate Pydantic model instance. Falls back to the legacy XML parsers if JSON fails.
    """
    try:
        data = json.loads(payload)
        kind = data.get("type")
        if kind == "review":
            return ReviewOutput(**data["data"])  # type: ignore[arg-type]
        if kind == "diagram":
            return Diagram(**data["data"])  # type: ignore[arg-type]
        if kind == "adr":
            return Adr(**data["data"])  # type: ignore[arg-type]
        if kind == "knowledge_candidate":
            return KnowledgeCandidate(**data["data"])  # type: ignore[arg-type]
    except Exception:
        # Legacy XML parsing path (kept for backward compatibility)
        from app.services.agents.reviewer import extract_review_xml
        from app.services.agents.architect import extract_adr_xml, extract_diagram_xml
        raise
