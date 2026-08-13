import re
from typing import List


# ============================================================================
# Engineering Specification Contract
# ============================================================================

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

BUILD_PLAN_REQUIRED_PHASE_SUBSECTIONS = [
    "Objectives",
    "Tasks",
    "Timeline",
    "Resources",
    "Deliverables",
]


# ============================================================================
# Canonical Engineering Specification Template
#
# IntakeService imports this constant directly.
# Do not remove or rename it without updating IntakeService.
# ============================================================================

ENGINEERING_SPEC_TEMPLATE = """# Live Engineering Specification: {project_title}

## Request Summary

## Objectives

## Scope

## Non-Goals

## Requirements

## Constraints

## Assumptions

## Agent Responsibilities

### Coordinator

### Architect

### Builder

### Reviewer

### QA

### Platform

## Phase Plan

### Phase 1: Foundation

#### Objectives

#### Tasks

#### Timeline

#### Resources

#### Deliverables

## Missing Inputs & Upload Requests

## Validation Checklist

## Risks and Blockers

## Acceptance Criteria
"""


# ============================================================================
# Approved heading aliases
#
# The LLM may use slightly different but semantically equivalent headings.
# Validation should not reject a specification simply because it says
# "Product Constraints" instead of "Constraints", for example.
# ============================================================================

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


# ============================================================================
# Public validation functions
# ============================================================================

def missing_engineering_spec_sections(markdown: str) -> List[str]:
    """
    Return required Engineering Specification sections that are missing.

    Validation accepts approved heading aliases so equivalent terminology
    does not create false failures.
    """

    missing: List[str] = []

    # ------------------------------------------------------------------------
    # Shared engineering specification sections
    # ------------------------------------------------------------------------

    for section in REQUIRED_ENGINEERING_SPEC_SECTIONS:
        aliases = SECTION_ALIASES.get(section, [section])

        if not _has_any_heading(markdown, aliases):
            missing.append(section)

    # ------------------------------------------------------------------------
    # Agent Responsibilities
    # ------------------------------------------------------------------------

    agent_body = _section_body(
        markdown,
        SECTION_ALIASES.get(
            "Agent Responsibilities",
            ["Agent Responsibilities"],
        ),
    )

    for agent in REQUIRED_AGENT_SECTIONS:
        if not _has_heading(agent_body, agent):
            missing.append(
                f"Agent Responsibilities > {agent}"
            )

    # ------------------------------------------------------------------------
    # Phase Plan
    # ------------------------------------------------------------------------

    phase_body = _section_body(
        markdown,
        SECTION_ALIASES.get(
            "Phase Plan",
            ["Phase Plan"],
        ),
    )

    phases = _numbered_phase_sections(phase_body)

    if not phases:
        missing.append(
            "Phase Plan > one or more numbered phase sections"
        )

    for phase_title, phase_content in phases:
        for subsection in REQUIRED_PHASE_SUBSECTIONS:
            if not _has_heading(
                phase_content,
                subsection,
            ):
                missing.append(
                    f"Phase Plan > {phase_title} > {subsection}"
                )

    return missing


def missing_build_plan_sections(markdown: str) -> List[str]:
    """
    Validate a build plan containing numbered phases.
    """

    missing: List[str] = []

    phases = _numbered_phase_sections(markdown)

    if not phases:
        missing.append(
            "one or more numbered phase sections"
        )

    for phase_title, phase_content in phases:
        for subsection in BUILD_PLAN_REQUIRED_PHASE_SUBSECTIONS:
            if not _has_heading(
                phase_content,
                subsection,
            ):
                missing.append(
                    f"{phase_title} > {subsection}"
                )

    return missing


# ============================================================================
# Heading helpers
# ============================================================================

def _has_any_heading(
    markdown: str,
    headings: List[str],
) -> bool:
    """
    Return True when any approved heading exists.
    """

    for heading in headings:
        if _has_heading(markdown, heading):
            return True

    return False


def _has_heading(
    markdown: str,
    heading: str,
) -> bool:
    """
    Check for a Markdown heading from ## through ######.

    Matching is case-insensitive and requires the entire heading line
    to match the expected heading text.
    """

    escaped = re.escape(heading)

    return bool(
        re.search(
            rf"(?im)^#{{2,6}}\s+{escaped}\s*$",
            markdown,
        )
    )


# ============================================================================
# Section extraction
# ============================================================================

def _section_body(
    markdown: str,
    headings: List[str],
) -> str:
    """
    Return the content belonging to the first matching ## section.

    The section ends at the next ## heading.
    """

    matches = []

    for heading in headings:
        escaped = re.escape(heading)

        match = re.search(
            rf"(?im)^##\s+{escaped}\s*$",
            markdown,
        )

        if match:
            matches.append(match)

    if not matches:
        return ""

    match = min(
        matches,
        key=lambda item: item.start(),
    )

    start = match.end()

    next_heading = re.search(
        r"(?m)^##\s+",
        markdown[start:],
    )

    if next_heading:
        end = start + next_heading.start()
    else:
        end = len(markdown)

    return markdown[start:end]


# ============================================================================
# Phase parsing
# ============================================================================

def _numbered_phase_sections(
    markdown: str,
) -> List[tuple[str, str]]:
    """
    Extract numbered Phase sections such as:

        ## Phase 1: Foundation
        ## Phase 2: Implementation

    or:

        ### Phase 1: Foundation
    """

    matches = list(
        re.finditer(
            r"(?im)^(##|###)\s+(Phase\s+\d+[:\s-].*)$",
            markdown,
        )
    )

    phases: List[tuple[str, str]] = []

    for index, match in enumerate(matches):
        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(markdown)

        phase_title = match.group(2).strip()
        phase_content = markdown[start:end]

        phases.append(
            (
                phase_title,
                phase_content,
            )
        )

    return phases