"""
Vita Roots Customer Support Agent
A multi-persona support agent that routes conversations to the appropriate
specialist based on category: general, account, or billing.

Each category has its own system prompt and response style.
All conversations are persisted to Supabase via support_tickets and support_messages.
All LLM calls are traced via Phoenix Arize.
"""

from __future__ import annotations

import logging
import os
from typing import AsyncIterator

import anthropic
from dotenv import load_dotenv

from observability import get_tracer

load_dotenv()
logger = logging.getLogger(__name__)
_tracer = get_tracer("support.agent")

MODEL = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# System prompts per support category
# ---------------------------------------------------------------------------

GENERAL_SYSTEM = """You are Sage, the Vita Roots general support specialist. 
Vita Roots is a family wellness platform that provides personalized meal planning, 
grocery list generation, and supplement guidance powered by AI.

Your role is to help families with general questions about how the platform works, 
what features are available, and how to get the most out of their wellness plans.

Guidelines:
- Be warm, encouraging, and knowledgeable about nutrition and wellness
- Explain features clearly without technical jargon
- If a question involves account changes or billing, let the client know you will 
  connect them with the right specialist
- Never make up features or capabilities that don't exist
- Always address the client by their family name if known
- Keep responses concise and actionable

Vita Roots features include: AI-generated meal plans, personalized grocery lists, 
supplement guides, signal alerts for new research affecting their plan, and 
human-in-the-loop plan approval before any changes take effect."""

ACCOUNT_SYSTEM = """You are Alex, the Vita Roots account specialist.
Vita Roots is a family wellness platform that provides personalized meal planning,
grocery list generation, and supplement guidance powered by AI.

Your role is to help families with account-related questions including:
- Adding or updating family member profiles
- Changing dietary preferences, health goals, or wellness philosophy
- Managing notification preferences
- Understanding their client number and member numbers
- Accessing their meal plan and grocery list history
- Profile and account settings

Guidelines:
- Be professional, precise, and solution-focused
- Ask clarifying questions when needed to resolve issues accurately
- If you need information you cannot access (like resetting passwords), 
  direct the client to the appropriate self-service option
- Always reference the client by their client number (e.g. VR-001001) when relevant
- If a question involves billing or payments, let the client know you will 
  connect them with the billing specialist
- Never share or confirm sensitive personal information beyond what the client provides"""

BILLING_SYSTEM = """You are Morgan, the Vita Roots billing specialist.
Vita Roots is a family wellness platform that provides personalized meal planning,
grocery list generation, and supplement guidance powered by AI.

Your role is to help families with billing and subscription questions including:
- Explaining subscription plans (Starter $9.99/mo, Family $19.99/mo, Premium $34.99/mo)
- Reviewing billing history and invoice questions
- Explaining charges and subscription cycles
- Upgrade and downgrade requests
- Cancellation policy (cancel anytime, no long-term contracts)
- Trial period questions (14-day free trial on all plans)

Guidelines:
- Be empathetic and transparent — billing questions can be stressful
- Never process actual payments or access payment card details
- For refund requests, acknowledge the request and escalate to a human agent
- Always confirm the client number before discussing account-specific billing details
- Be clear about what each plan includes and what the differences are
- If the client is considering cancellation, acknowledge their concern and 
  offer to explain what they would lose access to

Subscription plans:
- Starter ($9.99/mo, $99.99/yr): Up to 2 family members, meal planning, basic grocery list, email support
- Family ($19.99/mo, $199.99/yr): Up to 6 members, all features including supplement guides and signal alerts
- Premium ($34.99/mo, $349.99/yr): Unlimited members, all features, dedicated support, early access"""


def _get_system_prompt(category: str) -> str:
    mapping = {
        "general": GENERAL_SYSTEM,
        "account": ACCOUNT_SYSTEM,
        "billing": BILLING_SYSTEM,
    }
    return mapping.get(category, GENERAL_SYSTEM)


def _get_agent_name(category: str) -> str:
    mapping = {
        "general": "Sage",
        "account": "Alex",
        "billing": "Morgan",
    }
    return mapping.get(category, "Sage")


# ---------------------------------------------------------------------------
# Category detection
# ---------------------------------------------------------------------------

CATEGORY_DETECTION_PROMPT = """You are a customer support router for Vita Roots, a family wellness platform.

Classify the following customer message into exactly one of these categories:
- general: questions about how the platform works, features, wellness plans, meal planning, supplements
- account: questions about profile settings, family members, preferences, account access, history
- billing: questions about payments, subscriptions, invoices, pricing, cancellation, refunds

Respond with ONLY one word: general, account, or billing.

Customer message: {message}"""


async def detect_category(message: str) -> str:
    """
    Use Claude to detect the support category from the first message.
    Returns 'general', 'account', or 'billing'.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    with _tracer.start_as_current_span("support.detect_category"):
        response = client.messages.create(
            model=MODEL,
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": CATEGORY_DETECTION_PROMPT.format(message=message),
            }],
        )
        category = response.content[0].text.strip().lower()
        if category not in ("general", "account", "billing"):
            category = "general"
        logger.info(f"[support.detect_category] Detected: {category}")
        return category


# ---------------------------------------------------------------------------
# Support response generation
# ---------------------------------------------------------------------------

async def generate_support_response(
    category: str,
    conversation_history: list[dict],
    family_context: dict | None = None,
) -> str:
    """
    Generate a support response for the given category and conversation history.
    Optionally includes family context (name, client number, subscription) 
    for more personalized responses.

    conversation_history format:
      [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    system_prompt = _get_system_prompt(category)

    # Inject family context if available
    if family_context:
        context_block = f"""
Current client context:
- Family name: {family_context.get('name', 'Unknown')}
- Client number: {family_context.get('client_number', 'Unknown')}
- Subscription: {family_context.get('subscription', 'Unknown')}
- Member count: {family_context.get('member_count', 'Unknown')}
"""
        system_prompt = system_prompt + "\n\n" + context_block

    with _tracer.start_as_current_span("support.generate_response") as span:
        span.set_attribute("support.category", category)
        span.set_attribute("support.agent", _get_agent_name(category))
        span.set_attribute("support.message_count", len(conversation_history))

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=conversation_history,
        )

        reply = response.content[0].text
        logger.info(f"[support.generate_response] Category: {category}, tokens: {response.usage.output_tokens}")
        return reply


async def stream_support_response(
    category: str,
    conversation_history: list[dict],
    family_context: dict | None = None,
) -> AsyncIterator[str]:
    """
    Stream a support response for real-time chat display.
    Yields text chunks as they arrive from the API.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    system_prompt = _get_system_prompt(category)

    if family_context:
        context_block = f"""
Current client context:
- Family name: {family_context.get('name', 'Unknown')}
- Client number: {family_context.get('client_number', 'Unknown')}
- Subscription: {family_context.get('subscription', 'Unknown')}
- Member count: {family_context.get('member_count', 'Unknown')}
"""
        system_prompt = system_prompt + "\n\n" + context_block

    with _tracer.start_as_current_span("support.stream_response") as span:
        span.set_attribute("support.category", category)
        span.set_attribute("support.agent", _get_agent_name(category))

        with client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=conversation_history,
        ) as stream:
            for text in stream.text_stream:
                yield text
