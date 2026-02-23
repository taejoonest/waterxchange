"""
SGMA Chat API - Knowledge Graph + LLM powered assistant
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from core.security import get_current_user
from services.knowledge_graph import SGMAKnowledgeGraph
from services.llm_service import LLMService

router = APIRouter()

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    sources: List[str]
    compliance_check: Optional[dict] = None

# Initialize services
kg = SGMAKnowledgeGraph()
kg.load_regulations()
llm = LLMService()

@router.post("/", response_model=ChatResponse)
async def chat_with_sgma_assistant(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat with the SGMA AI assistant.
    Uses knowledge graph retrieval + LLM for accurate regulatory guidance.
    """
    
    user_message = request.message
    
    # Step 1: Query knowledge graph for relevant SGMA context
    kg_results = kg.query(user_message)
    
    # Step 2: Check if this is a transfer compliance question
    compliance_check = None
    if any(word in user_message.lower() for word in ["transfer", "sell", "buy", "trade"]):
        # Extract basin names if mentioned
        compliance_check = kg.check_transfer_compliance(user_message)
    
    # Step 3: Build context from knowledge graph
    context = kg.format_context(kg_results)
    
    # Step 4: Generate response using LLM with retrieved context
    response = await llm.generate_response(
        user_message=user_message,
        context=context,
        conversation_history=request.conversation_history,
        compliance_info=compliance_check
    )
    
    # Extract source citations
    sources = [r.get("source", "SGMA Regulations") for r in kg_results[:3]]
    
    return ChatResponse(
        response=response,
        sources=list(set(sources)),
        compliance_check=compliance_check
    )

@router.post("/quick-check")
async def quick_compliance_check(
    from_basin: str,
    to_basin: str,
    quantity_af: float,
    current_user: dict = Depends(get_current_user)
):
    """
    Quick check if a transfer is allowed between two basins.
    Returns compliance status without full chat response.
    """
    
    result = kg.check_transfer_between_basins(from_basin, to_basin, quantity_af)
    
    return {
        "from_basin": from_basin,
        "to_basin": to_basin,
        "quantity_af": quantity_af,
        "is_allowed": result["allowed"],
        "reason": result["reason"],
        "requires_permit": result.get("requires_permit", False),
        "relevant_rules": result.get("rules", [])
    }
