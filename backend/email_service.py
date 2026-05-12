"""
Email service — Resend API
Handles transactional email for plan and grocery approval notifications.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_URL = "https://api.resend.com/emails"
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")


async def send_plan_approval_email(
    to_email: str,
    family_name: str,
    client_number: str,
    token: str,
    week_start: str,
) -> bool:
    """
    Send a meal plan approval request email to the family.
    Includes approve and reject links containing the one-time token.
    """
    approve_url = f"{APP_URL}/api/approvals/plan/{token}/approve"
    reject_url = f"{APP_URL}/api/approvals/plan/{token}/reject"

    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px;">
      <img src="https://via.placeholder.com/120x40?text=Vita+Roots" alt="Vita Roots" style="margin-bottom: 24px;" />
      <h2 style="color: #2d6a4f;">Your Meal Plan is Ready for Review</h2>
      <p>Hello {family_name},</p>
      <p>Your personalized meal plan for the week of <strong>{week_start}</strong> has been generated and is ready for your approval.</p>
      <p style="color: #555;">Client Number: <strong>{client_number}</strong></p>
      <p>Please review and approve or reject your plan using the buttons below. If you take no action within 48 hours, your current plan will remain unchanged.</p>
      <div style="margin: 32px 0;">
        <a href="{approve_url}"
           style="background-color: #2d6a4f; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; margin-right: 16px; font-weight: bold;">
          ✓ Approve Plan
        </a>
        <a href="{reject_url}"
           style="background-color: #c0392b; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
          ✗ Reject Plan
        </a>
      </div>
      <p style="color: #888; font-size: 13px;">
        These links are single-use and will expire in 48 hours.
        If you have questions, contact us through the Vita Roots support portal.
      </p>
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
      <p style="color: #aaa; font-size: 12px;">Vita Roots Family Wellness · You are receiving this because you have an active plan.</p>
    </div>
    """

    return await _send_email(
        to=to_email,
        subject=f"Vita Roots — Your Meal Plan for {week_start} Needs Approval",
        html=html,
    )


async def send_grocery_approval_email(
    to_email: str,
    family_name: str,
    client_number: str,
    token: str,
    total_cost: float,
    item_count: int,
) -> bool:
    """
    Send a grocery list approval request email to the family.
    Includes approve and reject links containing the one-time token.
    """
    approve_url = f"{APP_URL}/api/approvals/grocery/{token}/approve"
    reject_url = f"{APP_URL}/api/approvals/grocery/{token}/reject"

    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px;">
      <img src="https://via.placeholder.com/120x40?text=Vita+Roots" alt="Vita Roots" style="margin-bottom: 24px;" />
      <h2 style="color: #2d6a4f;">Your Grocery List is Ready for Review</h2>
      <p>Hello {family_name},</p>
      <p>Your grocery list has been generated based on your approved meal plan.</p>
      <p style="color: #555;">Client Number: <strong>{client_number}</strong></p>
      <div style="background: #f8f9fa; border-radius: 8px; padding: 16px; margin: 16px 0;">
        <p style="margin: 0;"><strong>{item_count} items</strong> · Estimated total: <strong>${total_cost:.2f}</strong></p>
      </div>
      <p>Please review and confirm your grocery list. If you take no action within 48 hours, the list will remain pending.</p>
      <div style="margin: 32px 0;">
        <a href="{approve_url}"
           style="background-color: #2d6a4f; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; margin-right: 16px; font-weight: bold;">
          ✓ Approve List
        </a>
        <a href="{reject_url}"
           style="background-color: #c0392b; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
          ✗ Reject List
        </a>
      </div>
      <p style="color: #888; font-size: 13px;">
        These links are single-use and will expire in 48 hours.
      </p>
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
      <p style="color: #aaa; font-size: 12px;">Vita Roots Family Wellness · You are receiving this because you have an active plan.</p>
    </div>
    """

    return await _send_email(
        to=to_email,
        subject=f"Vita Roots — Your Grocery List ({item_count} items, ${total_cost:.2f}) Needs Approval",
        html=html,
    )


async def send_approval_confirmation_email(
    to_email: str,
    family_name: str,
    approval_type: str,
    decision: str,
) -> bool:
    """
    Send a confirmation email after a family makes an approval decision.
    """
    action = "approved" if decision == "approved" else "rejected"
    plan_label = "Meal Plan" if approval_type == "plan" else "Grocery List"
    color = "#2d6a4f" if decision == "approved" else "#c0392b"
    icon = "✓" if decision == "approved" else "✗"

    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px;">
      <h2 style="color: {color};">{icon} {plan_label} {action.capitalize()}</h2>
      <p>Hello {family_name},</p>
      <p>Your {plan_label.lower()} has been <strong>{action}</strong>. No further action is required.</p>
      {"<p>Your plan is now active and your wellness journey continues.</p>" if decision == "approved" else "<p>Your wellness agent will be notified and can generate a revised plan if needed.</p>"}
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
      <p style="color: #aaa; font-size: 12px;">Vita Roots Family Wellness</p>
    </div>
    """

    return await _send_email(
        to=to_email,
        subject=f"Vita Roots — {plan_label} {action.capitalize()}",
        html=html,
    )


async def _send_email(to: str, subject: str, html: str) -> bool:
    """
    Internal helper — sends email via Resend API.
    Returns True on success, False on failure.
    """
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — skipping email send.")
        return False

    payload = {
        "from": FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                RESEND_URL,
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if resp.status_code in (200, 201):
                logger.info(f"Email sent to {to}: {subject}")
                return True
            else:
                logger.error(f"Resend error {resp.status_code}: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False
