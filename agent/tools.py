"""Tool definitions exposed to the LangGraph agent.

Each tool simulates a real business operation. The risk gateway intercepts
calls to these tools before they are actually executed.
"""

from __future__ import annotations

from langchain_core.tools import tool


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient address.

    Args:
        to:      Recipient email address (e.g. alice@company.com).
        subject: Email subject line.
        body:    Plain-text email body.
    """
    return f"Email sent to '{to}' | Subject: '{subject}'"


@tool
def issue_refund(customer_id: str, amount: float) -> str:
    """Issue a monetary refund to a customer.

    Args:
        customer_id: Unique customer identifier (e.g. CUST-001).
        amount:      Refund amount in USD (must be positive).
    """
    return f"Refund of ${amount:.2f} issued to customer '{customer_id}'."


@tool
def lookup_account(customer_id: str) -> str:
    """Look up a customer's account details by their ID.

    Args:
        customer_id: Unique customer identifier (e.g. CUST-001).
    """
    # Simulated in-memory account data
    accounts = {
        "CUST-001": "Status=Active  | Balance=$1,250.00 | Plan=Premium  | Joined=2023-01",
        "CUST-002": "Status=Active  | Balance=$320.50   | Plan=Basic    | Joined=2024-03",
        "CUST-003": "Status=Pending | Balance=$0.00     | Plan=Trial    | Joined=2025-01",
    }
    info = accounts.get(customer_id, f"No account found for '{customer_id}'.")
    return f"Account {customer_id}: {info}"
