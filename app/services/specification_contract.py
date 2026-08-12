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


BUILD_PLAN_REQUIRED_PHASE_SUBSECTIONS = [
    "Objectives",
    "Tasks",
    "Timeline",
    "Resources",
    "Deliverables",
]


def missing_engineering_spec_sections(markdown: str) -> List[str]:
    missing = [
        section
        for section in REQUIRED_ENGINEERING_SPEC_SECTIONS
        if not _has_heading(markdown, section)
    ]
    agent_body = _section_body(markdown, "Agent Responsibilities")
    missing.extend(
        f"Agent Responsibilities > {section}"
        for section in REQUIRED_AGENT_SECTIONS
        if not _has_heading(agent_body, section)
    )
    phase_body = _section_body(markdown, "Phase Plan")
    phases = _numbered_phase_sections(phase_body)
    if not phases:
        missing.append("Phase Plan > one or more numbered phase sections")
    for phase_title, phase_content in phases:
        missing.extend(
            f"Phase Plan > {phase_title} > {section}"
            for section in REQUIRED_PHASE_SUBSECTIONS
            if not _has_heading(phase_content, section)
        )
    return missing


def missing_build_plan_sections(markdown: str) -> List[str]:
    missing = []
    phases = _numbered_phase_sections(markdown)
    if not phases:
        missing.append("one or more numbered phase sections")
    for phase_title, phase_content in phases:
        missing.extend(
            f"{phase_title} > {section}"
            for section in BUILD_PLAN_REQUIRED_PHASE_SUBSECTIONS
            if not _has_heading(phase_content, section)
        )
    return missing


def _has_heading(markdown: str, heading: str) -> bool:
    escaped = re.escape(heading)
    return bool(re.search(rf"(?im)^#{{2,6}}\s+{escaped}\s*$", markdown))


def _section_body(markdown: str, heading: str) -> str:
    escaped = re.escape(heading)
    match = re.search(rf"(?im)^(##)\s+{escaped}\s*$", markdown)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"(?m)^##\s+", markdown[start:])
    end = start + next_heading.start() if next_heading else len(markdown)
    return markdown[start:end]


def _numbered_phase_sections(markdown: str) -> List[tuple[str, str]]:
    matches = list(re.finditer(r"(?im)^(##|###)\s+(Phase\s+\d+[:\s-].*)$", markdown))
    phases: List[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        phases.append((match.group(2).strip(), markdown[start:end]))
    return phases
