"""
Customer Support routes.
POST   /api/support/tickets                     — create a new support ticket
GET    /api/support/tickets/{ticket_id}         — get ticket with messages
GET    /api/support/tickets/family/{family_id}  — list all tickets for a family
POST   /api/support/tickets/{ticket_id}/message — send a message and get response
GET    /api/support/tickets/{ticket_id}/stream  — stream a response (SSE)
PUT    /api/support/tickets/{ticket_id}/status  — update ticket status
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import database as db
import support_agent as agent
from models import APIResponse
from observability import get_tracer

logger = logging.getLogger(__name__)
router = APIRouter()
_tracer = get_tracer("route.support")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CreateTicketRequest(BaseModel):
    family_id: Optional[str] = None
    client_number: Optional[str] = None
    subject: str
    initial_message: str
    category: Optional[str] = None  # auto-detected if not provided
    priority: str = "normal"


class SendMessageRequest(BaseModel):
    message: str
    family_id: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Support ticket endpoints
# ---------------------------------------------------------------------------


@router.post("/support/tickets", response_model=APIResponse, status_code=201)
async def create_ticket(body: CreateTicketRequest):
    """
    Create a new support ticket.
    If category is not provided, it is auto-detected from the initial message.
    An initial AI response is generated immediately.
    """
    with _tracer.start_as_current_span("route.support.create_ticket"):
        # Auto-detect category if not provided
        category = body.category
        if not category:
            category = await agent.detect_category(body.initial_message)

        # Resolve family context if available
        family = None
        family_context = None
        if body.family_id:
            family = await db.get_family(body.family_id)
        elif body.client_number:
            family = await db.get_family_by_client_number(body.client_number)

        if family:
            members = await db.get_family_members(str(family["id"]))
            subscription = await db.get_family_subscription(str(family["id"]))
            family_context = {
                "name": family["name"],
                "client_number": family["client_number"],
                "subscription": subscription.get("subscription_plans", {}).get("display_name", "Unknown plan") if subscription else "No active subscription",
                "member_count": len(members),
            }

        # Create ticket in database
        ticket = await db.create_support_ticket({
            "family_id": str(family["id"]) if family else None,
            "client_number": body.client_number or (family["client_number"] if family else None),
            "category": category,
            "subject": body.subject,
            "priority": body.priority,
        })

        if not ticket:
            raise HTTPException(status_code=500, detail="Failed to create support ticket.")

        ticket_id = str(ticket["id"])

        # Save the user's initial message
        await db.add_support_message(ticket_id, "user", body.initial_message)

        # Generate initial AI response
        conversation_history = [{"role": "user", "content": body.initial_message}]
        response_text = await agent.generate_support_response(
            category=category,
            conversation_history=conversation_history,
            family_context=family_context,
        )

        # Save the AI response
        await db.add_support_message(ticket_id, "assistant", response_text)

        # Log to audit trail
        await db.log_action(
            action="support_ticket_created",
            family_id=str(family["id"]) if family else None,
            entity_type="support_ticket",
            entity_id=ticket_id,
            details={"category": category, "subject": body.subject},
        )

        agent_name = agent._get_agent_name(category)

        return APIResponse(
            data={
                "ticket_id": ticket_id,
                "category": category,
                "agent_name": agent_name,
                "subject": body.subject,
                "status": "open",
                "initial_response": response_text,
                "family_context": family_context,
            },
            message=f"Support ticket created. {agent_name} is handling your request.",
        )


@router.get("/support/tickets/{ticket_id}", response_model=APIResponse)
async def get_ticket(ticket_id: str):
    """Return a ticket with its full message history."""
    with _tracer.start_as_current_span("route.support.get_ticket"):
        ticket = await db.get_support_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found.")

        messages = await db.get_ticket_messages(ticket_id)

        return APIResponse(data={
            **ticket,
            "messages": messages,
            "agent_name": agent._get_agent_name(ticket["category"]),
        })


@router.get("/support/tickets/family/{family_id}", response_model=APIResponse)
async def get_family_tickets(family_id: str):
    """Return all support tickets for a family."""
    with _tracer.start_as_current_span("route.support.family_tickets"):
        tickets = await db.get_family_tickets(family_id)
        return APIResponse(data=tickets)


@router.post("/support/tickets/{ticket_id}/message", response_model=APIResponse)
async def send_message(ticket_id: str, body: SendMessageRequest):
    """
    Send a message in an existing ticket and get an AI response.
    Maintains full conversation context.
    """
    with _tracer.start_as_current_span("route.support.send_message"):
        ticket = await db.get_support_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found.")

        if ticket["status"] in ("resolved", "closed"):
            raise HTTPException(
                status_code=409,
                detail="This ticket is closed. Please open a new ticket."
            )

        # Get full conversation history
        existing_messages = await db.get_ticket_messages(ticket_id)
        conversation_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in existing_messages
            if msg["role"] in ("user", "assistant")
        ]

        # Add the new user message
        conversation_history.append({"role": "user", "content": body.message})
        await db.add_support_message(ticket_id, "user", body.message)

        # Get family context if available
        family_context = None
        family_id = body.family_id or ticket.get("family_id")
        if family_id:
            family = await db.get_family(str(family_id))
            if family:
                members = await db.get_family_members(str(family["id"]))
                subscription = await db.get_family_subscription(str(family["id"]))
                family_context = {
                    "name": family["name"],
                    "client_number": family["client_number"],
                    "subscription": subscription["display_name"] if subscription else "No active subscription",
                    "member_count": len(members),
                }

        # Generate response
        response_text = await agent.generate_support_response(
            category=ticket["category"],
            conversation_history=conversation_history,
            family_context=family_context,
        )

        await db.add_support_message(ticket_id, "assistant", response_text)

        return APIResponse(
            data={
                "ticket_id": ticket_id,
                "category": ticket["category"],
                "agent_name": agent._get_agent_name(ticket["category"]),
                "response": response_text,
            },
            message="Response generated.",
        )


@router.get("/support/tickets/{ticket_id}/stream")
async def stream_message(ticket_id: str, message: str, family_id: str = None):
    """
    Stream an AI support response via Server-Sent Events.
    Used by the frontend chat interface for real-time response display.
    """
    ticket = await db.get_support_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    existing_messages = await db.get_ticket_messages(ticket_id)
    conversation_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in existing_messages
        if msg["role"] in ("user", "assistant")
    ]
    conversation_history.append({"role": "user", "content": message})

    await db.add_support_message(ticket_id, "user", message)

    family_context = None
    fid = family_id or ticket.get("family_id")
    if fid:
        family = await db.get_family(str(fid))
        if family:
            members = await db.get_family_members(str(family["id"]))
            family_context = {
                "name": family["name"],
                "client_number": family["client_number"],
                "subscription": "Family",
                "member_count": len(members),
            }

    full_response = []

    async def event_stream():
        async for chunk in agent.stream_support_response(
            category=ticket["category"],
            conversation_history=conversation_history,
            family_context=family_context,
        ):
            full_response.append(chunk)
            yield f"data: {json.dumps({'text': chunk})}\n\n"

        # Save complete response after streaming
        complete_response = "".join(full_response)
        await db.add_support_message(ticket_id, "assistant", complete_response)
        yield f"data: {json.dumps({'done': True, 'agent': agent._get_agent_name(ticket['category'])})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.put("/support/tickets/{ticket_id}/status", response_model=APIResponse)
async def update_ticket_status(ticket_id: str, body: UpdateStatusRequest):
    """Update the status of a support ticket."""
    with _tracer.start_as_current_span("route.support.update_status"):
        valid_statuses = ("open", "in_progress", "resolved", "closed")
        if body.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        ticket = await db.get_support_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found.")

        updated = await db.update_ticket_status(ticket_id, body.status)

        await db.log_action(
            action="support_ticket_status_updated",
            family_id=str(ticket.get("family_id")) if ticket.get("family_id") else None,
            entity_type="support_ticket",
            entity_id=ticket_id,
            details={"old_status": ticket["status"], "new_status": body.status},
        )

        return APIResponse(
            data=updated,
            message=f"Ticket status updated to {body.status}.",
        )
