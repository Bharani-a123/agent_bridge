"""Agent state definition shared across all graph nodes."""

from __future__ import annotations

import operator
from typing import Annotated, Any

from langgraph.graph.message import MessagesState


class AgentState(MessagesState):
    """Extends MessagesState with a risk_log accumulator.

    - messages  : full conversation history (add_messages reducer inherited)
    - risk_log  : every gateway decision recorded during this session
                  (operator.add reducer → each node's entries are appended)
    """

    risk_log: Annotated[list[dict[str, Any]], operator.add]
