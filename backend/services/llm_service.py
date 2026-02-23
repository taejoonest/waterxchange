"""
LLM Service for SGMA Chat Assistant
Integrates with OpenAI or Anthropic APIs
"""

from typing import List, Optional, Dict, Any
import os

from core.config import settings

class LLMService:
    """
    LLM integration for generating natural language responses
    about SGMA compliance and water trading.
    """
    
    SYSTEM_PROMPT = """You are an expert assistant for California's Sustainable Groundwater Management Act (SGMA) 
and water trading regulations. You help farmers understand:

1. Whether their water transfers are compliant with SGMA
2. What permits or notifications are required
3. Basin-specific rules and restrictions
4. Best practices for water trading

Always be helpful, accurate, and cite specific SGMA sections when possible.
If you're unsure about something, say so rather than guessing.

When answering about transfers:
- Intra-basin (same basin) transfers are generally allowed without permits
- Inter-basin transfers to adjacent basins under 100 AF require GSA notification only
- Inter-basin transfers over 100 AF require permits from both GSAs
- Critically overdrafted basins may have additional restrictions

Keep responses concise and actionable for farmers."""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self._init_clients()
    
    def _init_clients(self):
        """Initialize LLM API clients"""
        
        if settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except ImportError:
                pass
        
        if settings.ANTHROPIC_API_KEY:
            try:
                from anthropic import Anthropic
                self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            except ImportError:
                pass
    
    async def generate_response(
        self,
        user_message: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
        compliance_info: Optional[Dict] = None
    ) -> str:
        """
        Generate a response using LLM with retrieved context.
        Falls back to rule-based response if no LLM available.
        """
        
        # Build the augmented prompt
        augmented_prompt = self._build_prompt(user_message, context, compliance_info)
        
        # Try OpenAI first
        if self.openai_client:
            return await self._call_openai(augmented_prompt, conversation_history)
        
        # Try Anthropic
        if self.anthropic_client:
            return await self._call_anthropic(augmented_prompt, conversation_history)
        
        # Fallback to rule-based response
        return self._generate_fallback_response(user_message, context, compliance_info)
    
    def _build_prompt(
        self, 
        user_message: str, 
        context: str, 
        compliance_info: Optional[Dict]
    ) -> str:
        """Build the augmented prompt with retrieved context"""
        
        prompt_parts = [
            f"User Question: {user_message}",
            "",
            f"Retrieved SGMA Context:\n{context}"
        ]
        
        if compliance_info:
            prompt_parts.extend([
                "",
                "Compliance Check Result:",
                f"- Allowed: {compliance_info.get('allowed', 'Unknown')}",
                f"- Reason: {compliance_info.get('reason', 'N/A')}",
                f"- Requires Permit: {compliance_info.get('requires_permit', False)}",
                f"- Relevant Rules: {', '.join(compliance_info.get('rules', []))}"
            ])
        
        prompt_parts.extend([
            "",
            "Please provide a helpful, accurate response based on this information."
        ])
        
        return "\n".join(prompt_parts)
    
    async def _call_openai(
        self, 
        prompt: str, 
        conversation_history: Optional[List[Dict]]
    ) -> str:
        """Call OpenAI API"""
        
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return self._generate_fallback_response(prompt, "", None)
    
    async def _call_anthropic(
        self, 
        prompt: str, 
        conversation_history: Optional[List[Dict]]
    ) -> str:
        """Call Anthropic API"""
        
        messages = []
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-6:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                system=self.SYSTEM_PROMPT,
                messages=messages,
                max_tokens=500
            )
            return response.content[0].text
        except Exception as e:
            return self._generate_fallback_response(prompt, "", None)
    
    def _generate_fallback_response(
        self, 
        user_message: str, 
        context: str, 
        compliance_info: Optional[Dict]
    ) -> str:
        """Generate a rule-based response when LLM is not available"""
        
        user_lower = user_message.lower()
        
        # Check for compliance questions
        if compliance_info:
            allowed = compliance_info.get("allowed", True)
            reason = compliance_info.get("reason", "")
            requires_permit = compliance_info.get("requires_permit", False)
            rules = compliance_info.get("rules", [])
            
            if allowed:
                response = f"✅ **This transfer appears to be allowed.**\n\n{reason}"
                if requires_permit:
                    response += "\n\n⚠️ Note: A permit is required for this transfer."
                if rules:
                    response += f"\n\n📋 Relevant rules: {', '.join(rules)}"
            else:
                response = f"❌ **This transfer may not be allowed.**\n\n{reason}"
                if rules:
                    response += f"\n\n📋 Relevant rules: {', '.join(rules)}"
            
            return response
        
        # General questions
        if "permit" in user_lower:
            return """**SGMA Permit Requirements:**

• **Intra-basin transfers**: No permit needed
• **Inter-basin transfers < 100 AF**: GSA notification required
• **Inter-basin transfers ≥ 100 AF**: Permit required from both GSAs
• **Critically overdrafted basins**: Additional restrictions may apply

Contact your local GSA for specific requirements."""
        
        if "basin" in user_lower:
            return """**California Central Valley Basins:**

The Central Valley is divided into several groundwater basins, each managed by a Groundwater Sustainability Agency (GSA):

• Kern County - Critically Overdrafted
• San Joaquin Valley - High Priority
• Tulare Lake - Critically Overdrafted
• Kings County - Medium Priority
• Fresno County - High Priority
• Madera County - Critically Overdrafted

Transfers within the same basin are generally unrestricted. Inter-basin transfers have additional requirements."""
        
        # Default response
        return """I can help you with SGMA compliance questions about water transfers. 

Try asking:
• "Can I transfer water to [basin name]?"
• "Do I need a permit to sell 50 AF?"
• "What are the rules for my basin?"

For specific compliance checks, please provide:
- Source basin
- Destination basin  
- Quantity (in acre-feet)"""
