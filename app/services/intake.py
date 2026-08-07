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

        if session.status == "completed":
            raise ValueError("Intake session is already completed")

        # 1. Append user message to history
        new_messages = list(session.messages)
        new_messages.append({"role": "user", "content": message})
        session.messages = new_messages
        flag_modified(session, "messages")
        await self.db.commit()

        # 2. Compile messages for LLM review
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
            os.makedirs(self.artifacts_dir, exist_ok=True)
            file_path = os.path.join(self.artifacts_dir, f"{session.id}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(spec_markdown)

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
