"""
Chat route — streaming SSE endpoint for the AI wellness assistant.
POST /api/chat
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from deps import get_current_family
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from agent import WellnessAgent
from database import get_family
from models import ChatRequest, Family, FamilyMember
from observability import get_tracer, add_wellness_attributes

logger = logging.getLogger(__name__)
router = APIRouter()
_agent = WellnessAgent()
_tracer = get_tracer("route.chat")


def _family_from_record(record: dict) -> Family:
    """Reconstruct Family model from database record data field."""
    data = record.get("data", record)
    return Family.model_validate(data)


@router.post("/chat")
async def chat_endpoint(request: ChatRequest, current_family: dict = Depends(get_current_family)):
    """
    Stream a wellness assistant response via Server-Sent Events.
    Each SSE event data field contains a JSON string: {"chunk": "...", "done": false}
    Final event: {"chunk": "", "done": true}
    """
    family_id = str(current_family["id"])
    with _tracer.start_as_current_span("route.chat.post") as span:
        add_wellness_attributes(
            span,
            family_id=family_id,
            member_id=request.member_id,
            request_type="chat",
        )

        db_record = await get_family(family_id)
        if db_record is None:
            # If DB unavailable, return a minimal response rather than erroring
            logger.warning(f"Family {request.family_id} not found; using stub context.")
            raise HTTPException(
                status_code=404,
                detail=f"Family {request.family_id} not found.",
            )

        family = _family_from_record(dict(db_record))

        async def event_generator() -> AsyncGenerator[dict, None]:
            try:
                async for chunk in _agent.chat(
                    family=family,
                    message=request.message,
                    conversation_history=request.conversation_history,
                    member_id=request.member_id,
                ):
                    payload = json.dumps({"chunk": chunk, "done": False})
                    yield {"data": payload}

                # Signal completion
                yield {"data": json.dumps({"chunk": "", "done": True})}

            except Exception as exc:
                logger.exception("Chat stream error")
                error_payload = json.dumps({"error": str(exc), "done": True})
                yield {"data": error_payload}

        return EventSourceResponse(event_generator())
