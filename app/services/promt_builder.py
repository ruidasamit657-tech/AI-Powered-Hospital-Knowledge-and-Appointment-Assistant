from typing import List, Dict, Any

from app.core.logging import get_logger

logger = get_logger(__name__)

class PromptBuilder:
    """Builds prompts for the LLM with context and instructions."""
    
    def __init__(self):
        """Initialize the prompt builder with system prompts."""
        self.system_prompt = """You are a helpful medical assistant chatbot for a hospital. Your responses should be:
1. Accurate and based on the provided context
2. Clear and easy to understand for patients
3. Professional and empathetic
4. Safe and responsible

Important guidelines:
- Only provide information that is in the context
- If the information is not in the context, say so clearly
- Never provide medical diagnoses or treatment recommendations
- Always recommend consulting healthcare professionals for personal medical advice
- For emergencies, direct users to call emergency services
- Be helpful but cautious with medical information"""
    
    def build_rag_prompt(
        self,
        query: str,
        context: List[Dict[str, Any]],
    ) -> str:
        """Build a grounded prompt from the query and retrieved context."""
        context_text = "\n\n".join(
            f"[{index}] {item.get('content', '')}"
            for index, item in enumerate(context, start=1)
            if item.get("content")
        )
        if not context_text:
            context_text = "No relevant context was found."

        return (
            f"{self.system_prompt}\n\n"
            f"Context:\n{context_text}\n\n"
            f"User question: {query}\n\n"
            "Answer using only the context above."
        )

    def build_llm_prompt(self, query: str) -> str:
        """Build a prompt for answering without retrieved context."""
        return (
            f"{self.system_prompt}\n\n"
            f"User question: {query}\n\n"
            "No supporting context was retrieved. Say so clearly and do not invent information."
        )
