import re
from typing import List


REQUIRED_ENGINEERING_SPEC_SECTIONS = [
    "Request Summary",
    "Objectives",
    "Scope",
    "Non-Goals",
    "Requirements",
    "Constraints",
    "Assumptions",
    "Agent Responsibilities",
    "Phase Plan",
    "Missing Inputs & Upload Requests",
    "Validation Checklist",
    "Risks and Blockers",
    "Acceptance Criteria",
]

REQUIRED_AGENT_SECTIONS = [
    "Coordinator",
    "Architect",
    "Builder",
    "Reviewer",
    "QA",
    "Platform",
]

REQUIRED_PHASE_SUBSECTIONS = [
    "Objectives",
    "Tasks",
    "Timeline",
    "Resources",
    "Deliverables",
]

# Approved heading aliases.
#
# These allow the specification writer to use reasonable equivalent
# terminology without causing a false validation failure.
SECTION_ALIASES = {
    "Request Summary": [
        "Request Summary",
        "Summary",
    ],
    "Objectives": [
        "Objectives",
        "Goals",
    ],
    "Scope": [
        "Scope",
        "Project Scope",
    ],
    "Non-Goals": [
        "Non-Goals",
        "Non Goals",
        "Out of Scope",
        "Out of Scope (Non-Goals)",
        "Out of Scope / Non-Goals",
    ],
    "Requirements": [
        "Requirements",
        "Functional Requirements",
        "Product Requirements",
        "Functional and Non-Functional Requirements",
    ],
    "Constraints": [
        "Constraints",
        "Product Constraints",
        "Engineering Constraints",
        "Technical Constraints",
    ],
    "Assumptions": [
        "Assumptions",
        "Product Assumptions",
        "Engineering Assumptions",
    ],
    "Agent Responsibilities": [
        "Agent Responsibilities",
        "Engineering Agent Responsibilities",
    ],
    "Phase Plan": [
        "Phase Plan",
        "Engineering Phase Plan",
        "Implementation Phase Plan",
    ],
    "Missing Inputs & Upload Requests": [
        "Missing Inputs & Upload Requests",
        "Missing Inputs",
        "Inputs & Upload Requests",
    ],
    "Validation Checklist": [
        "Validation Checklist",
        "QA Validation Checklist",
        "Build Validation Checklist",
    ],
    "Risks and Blockers": [
        "Risks and Blockers",
        "Risks & Blockers",
        "Risks",
        "Engineering Risks",
        "Engineering Risks and Blockers",
    ],
    "Acceptance Criteria": [
        "Acceptance Criteria",
        "Acceptance Criteria & Definition of Done",
    ],
}


def missing_engineering_spec_sections(markdown: str) -> List[str]:
    missing = []

    for section in REQUIRED_ENGINEERING_SPEC_SECTIONS:
        if not _has_any_heading(
            markdown,
            SECTION_ALIASES.get(section, [section]),
        ):
            missing.append(section)

    agent_body = _section_body(
        markdown,
        SECTION_ALIASES.get(
            "Agent Responsibilities",
            ["Agent Responsibilities"],
        ),
    )

    for section in REQUIRED_AGENT_SECTIONS:
        if not _has_any_heading(agent_body, [section]):
            missing.append(
                f"Agent Responsibilities > {section}"
            )

    phase_body = _section_body(
        markdown,
        SECTION_ALIASES.get("Phase Plan", ["Phase Plan"]),
    )

    phases = _numbered_phase_sections(phase_body)

    if not phases:
        missing.append(
            "Phase Plan > one or more numbered phase sections"
        )

    for phase_title, phase_content in phases:
        for section in REQUIRED_PHASE_SUBSECTIONS:
            if not _has_any_heading(
                phase_content,
                [section],
            ):
                missing.append(
                    f"Phase Plan > {phase_title} > {section}"
                )

    return missing


def missing_build_plan_sections(markdown: str) -> List[str]:
    missing = []

    phases = _numbered_phase_sections(markdown)

    if not phases:
        missing.append(
            "one or more numbered phase sections"
        )

    for phase_title, phase_content in phases:
        for section in BUILD_PLAN_REQUIRED_PHASE_SUBSECTIONS:
            if not _has_any_heading(
                phase_content,
                [section],
            ):
                missing.append(
                    f"{phase_title} > {section}"
                )

    return missing


def _has_any_heading(
    markdown: str,
    headings: List[str],
) -> bool:
    for heading in headings:
        if _has_heading(markdown, heading):
            return True

    return False


def _has_heading(
    markdown: str,
    heading: str,
) -> bool:
    escaped = re.escape(heading)

    return bool(
        re.search(
            rf"(?im)^#{{2,6}}\s+{escaped}\s*$",
            markdown,
        )
    )


def _section_body(
    markdown: str,
    headings: List[str],
) -> str:
    matches = []

    for heading in headings:
        escaped = re.escape(heading)

        match = re.search(
            rf"(?im)^(##)\s+{escaped}\s*$",
            markdown,
        )

        if match:
            matches.append(match)

    if not matches:
        return ""

    match = min(matches, key=lambda item: item.start())

    start = match.end()

    next_heading = re.search(
        r"(?m)^##\s+",
        markdown[start:],
    )

    end = (
        start + next_heading.start()
        if next_heading
        else len(markdown)
    )

    return markdown[start:end]


def _numbered_phase_sections(
    markdown: str,
) -> List[tuple[str, str]]:
    matches = list(
        re.finditer(
            r"(?im)^(##|###)\s+(Phase\s+\d+[:\s-].*)$",
            markdown,
        )
    )

    phases: List[tuple[str, str]] = []

    for index, match in enumerate(matches):
        start = match.end()

        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(markdown)
        )

        phases.append(
            (
                match.group(2).strip(),
                markdown[start:end],
            )
        )

    return phases


BUILD_PLAN_REQUIRED_PHASE_SUBSECTIONS = [
    "Objectives",
    "Tasks",
    "Timeline",
    "Resources",
    "Deliverables",
]