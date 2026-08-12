import os
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.database.models.intake import IntakeSession
from app.schemas.model_router import Capability, ChatMessage, ModelRouteRequest
from app.services.model_router import ModelRouterService
from app.services.activity_log import ActivityLogService


class IntakeService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_router = ModelRouterService(db)
        self.activity_log = ActivityLogService(db)
        self.artifacts_dir = "artifacts/specifications"

    async def create_session(
        self, title: str, owner_id: Optional[str] = None, request_id: Optional[str] = None
    ) -> IntakeSession:
        welcome_message = (
            "Welcome to Shipyard!\n\n"
            "What would you like to engineer?\n\n"
            "1. Describe an engineering problem or provide engineering documentation.\n"
            "2. Upload documentation (PRD, Jira export, existing Engineering Specification, etc.)."
        )
        session = IntakeSession(
            title=title,
            owner_id=owner_id,
            status="in_progress",
            messages=[
                {"role": "assistant", "content": welcome_message}
            ]
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        await self.activity_log.record(
            event_type="intake_session_created",
            source="intake_service",
            request_id=request_id,
            payload={"session_id": str(session.id), "title": session.title},
        )
        return session

    async def get_session(self, session_id: uuid.UUID) -> Optional[IntakeSession]:
        result = await self.db.execute(
            select(IntakeSession).where(IntakeSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def send_chat_message(
        self, session_id: uuid.UUID, message: str, request_id: Optional[str] = None
    ) -> IntakeSession:
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Intake session {session_id} not found")

        # 1. Append user message to history
        new_messages = list(session.messages)
        new_messages.append({"role": "user", "content": message})
        session.messages = new_messages
        flag_modified(session, "messages")
        await self.db.commit()

        # 2. Compile messages for LLM review
        # Transition to Spec Writer if user requests validation or turns exceed 8
        is_validating = False
        user_messages = [msg for msg in session.messages if msg["role"] == "user"]
        if user_messages:
            last_msg = user_messages[-1]["content"].lower()
            if any(kw in last_msg for kw in ["validate", "yes", "confirm", "proceed", "approve", "go ahead", "start", "write the spec", "write specification", "stop acting"]):
                is_validating = True
            elif len(user_messages) >= 8:
                is_validating = True

        if session.specification:
            system_prompt = (
                "You are the Engineering Intake Coordinator for the Shipyard AI Engineering Organization.\n"
                "The user has a generated Engineering Specification below, but has not approved it yet.\n"
                "Continue the conversation normally: answer questions, explain decisions, and incorporate requested changes.\n"
                "If the user requests a change to the specification, output 'VALIDATED' on the very first line, followed by the complete updated Engineering Specification in Markdown.\n"
                "If the user is only asking a question or discussing the design, respond conversationally without the VALIDATED marker.\n\n"
                "CURRENT ENGINEERING SPECIFICATION:\n"
                f"{session.specification}"
            )
        elif is_validating:
            system_prompt = (
                "You are the Engineering Specification Writer for the Shipyard AI Engineering Organization.\n"
                "Your job now is to write the complete, buildable Engineering Specification based on the user's input.\n"
                "Do not act as a coordinator or ask for decisions unless a choice materially changes the architecture, security, cost, or user experience.\n\n"
                "Use the following architectural decisions as the source of truth:\n"
                "- Backend: Python / FastAPI\n"
                "- Database: PostgreSQL using SQLAlchemy 2.x and Alembic migrations\n"
                "- Containerization: Docker deployed on Railway (provider-agnostic database/hosting)\n"
                "- LLM: Provider-agnostic via LLMProvider interface (V1: Anthropic)\n"
                "- Browser research: BrowserResearchProvider (V1: Playwright)\n"
                "- Orchestrator: Replaceable WorkflowOrchestrator (V1: SimpleWorkerProvider without Redis/Celery)\n"
                "- Execution Limits: 180s global boundary, 20s individual adapter timeouts\n"
                "- Gates: Gate 1 (outbound only) and Gate 2 (inbound + outbound)\n\n"
                "For anything genuinely unspecified, make a reasonable engineering default and label it clearly as an implementation choice or assumption.\n\n"
                "Output 'VALIDATED' on the very first line, followed by the complete Engineering Specification in Markdown.\n"
                "Write every section completely. Do not stop mid-list, mid-table, or mid-section."
            )
        else:
            system_prompt = (
                "You are the Engineering Intake Coordinator for the Shipyard AI Engineering Organization.\n"
                "Your task is to guide the user to provide sufficient information to generate a validated Engineering Specification.\n\n"
                "A complete Engineering Specification must contain the following five sections:\n"
                "1. Overview & Background: What is the goal, background, and target audience?\n"
                "2. Functional Requirements: What are the specific capabilities and behaviors of the system?\n"
                "3. Non-Functional Requirements: Performance, scale, security, or accessibility requirements.\n"
                "4. Technical Architecture Constraints: Programming language, framework, database, ORM, etc.\n"
                "5. Deployment & Infrastructure Constraints: Deployment environment, ports, environment variables.\n\n"
                "Analyze the chat history between the user and yourself. Determine if all 5 sections have enough details to write the specification.\n"
                "If any details are missing, your response must request the user for those specific details. Do NOT output the specification yet.\n"
                "If all 5 sections have sufficient details, output the word 'VALIDATED' on the very first line, followed by the complete Engineering Specification formatted in Markdown."
            )

        llm_messages = [ChatMessage(role="system", content=system_prompt)]
        for msg in session.messages:
            llm_messages.append(ChatMessage(role=msg["role"], content=msg["content"]))

        # 3. Route capability request to Model Router
        route_req = ModelRouteRequest(
            capability=Capability.GENERAL_REASONING,
            messages=llm_messages,
            temperature=0.2,
            # Specifications are substantially longer than ordinary chat
            # responses; the shared 2,000-token default truncates them.
            max_tokens=8000,
        )
        route_res = await self.model_router.route(route_req, request_id=request_id)
        llm_content = route_res.content.strip()

        # 4. Check if LLM response validates the spec
        if llm_content.startswith("VALIDATED"):
            # Extract specification content following VALIDATED keyword
            spec_markdown = llm_content[len("VALIDATED"):].strip()
            session.specification = spec_markdown
            session.status = "completed"
            new_messages.append({
                "role": "assistant",
                "content": "Engineering Specification has been validated and generated successfully!"
            })
            session.messages = new_messages
            flag_modified(session, "messages")
            await self.db.commit()

            # Persist specification to file system
            import anyio
            os.makedirs(self.artifacts_dir, exist_ok=True)
            file_path = os.path.join(self.artifacts_dir, f"{session.id}.md")
            spec_anyio = anyio.Path(file_path)
            await spec_anyio.write_text(spec_markdown, encoding="utf-8")

            await self.activity_log.record(
                event_type="intake_specification_generated",
                source="intake_service",
                request_id=request_id,
                payload={"session_id": str(session.id), "file_path": file_path},
            )
        else:
            new_messages.append({"role": "assistant", "content": llm_content})
            session.messages = new_messages
            flag_modified(session, "messages")
            await self.db.commit()

        await self.db.refresh(session)
        return session
