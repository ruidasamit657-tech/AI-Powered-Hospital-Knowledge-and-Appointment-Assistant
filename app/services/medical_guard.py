import re
from typing import List, Dict, Any
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)

class MedicalGuard:
    """Safety guard for medical-related queries and responses."""
    
    def __init__(self):
        """Initialize medical guard with safety patterns and rules."""
        self.unsafe_patterns = [
            # Diagnosis requests
            (r'\b(diagnosis|diagnose|what do I have|what\'s wrong with me|am I sick)\b', 'diagnosis'),
            (r'\b(what disease|what condition|medical condition)\b', 'diagnosis'),
            
            # Treatment advice
            (r'\b(what should I take|what medication|what medicine|prescribe)\b', 'treatment'),
            (r'\b(should I take|can I take|is it safe to take)\b', 'treatment'),
            (r'\b(treatment for|cure for|how to treat)\b', 'treatment'),
            
            # Dosage questions
            (r'\b(how much|dosage|dose|how many mg|how many ml)\b', 'dosage'),
            (r'\b(take how many|how often should I take)\b', 'dosage'),
            
            # Emergency symptoms
            (r'\b(chest pain|heart attack|stroke|severe bleeding|unconscious)\b', 'emergency'),
            (r'\b(difficulty breathing|shortness of breath|choking)\b', 'emergency'),
            (r'\b(suicidal|self-harm|overdose)\b', 'emergency'),
            
            # Medical procedures
            (r'\b(surgery|operation|procedure|injection|biopsy)\b', 'procedure'),
            (r'\b(should I get|do I need|is it necessary)\b', 'procedure'),
            
            # Personal information
            (r'\b(blood pressure|blood sugar|heart rate|temperature)\b', 'vitals'),
            (r'\b(weight|height|BMI|body mass)\b', 'vitals')
        ]
        
        self.safety_responses = {
            'diagnosis': "I cannot provide medical diagnoses. Please consult a healthcare professional for proper diagnosis.",
            'treatment': "I cannot recommend treatments or medications. Please consult your doctor for medical advice.",
            'dosage': "I cannot provide dosage information. Always follow your doctor's prescription and instructions.",
            'emergency': "If you're experiencing a medical emergency, please call emergency services immediately.",
            'procedure': "I cannot provide medical procedure advice. Please consult your healthcare provider.",
            'vitals': "For medical vitals, please consult with your healthcare provider for accurate assessment."
        }
    
    def check_safety(self, query: str) -> Dict[str, Any]:
        """
        Check if a query is safe to process.
        
        Args:
            query: User query text
        
        Returns:
            Dictionary with safety check results
        """
        query_lower = query.lower()
        
        # Check for unsafe patterns
        warnings = []
        is_safe = True
        detected_categories = set()
        
        for pattern, category in self.unsafe_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                detected_categories.add(category)
        
        # Check for combination of medical terms
        medical_terms = ['symptom', 'pain', 'fever', 'cough', 'headache', 'nausea', 'dizziness']
        medical_term_count = sum(1 for term in medical_terms if term in query_lower)
        
        if medical_term_count >= 3:
            warnings.append("Multiple medical symptoms detected. Please consult a healthcare professional.")
            detected_categories.add('symptoms')
        
        # Generate response
        response = None
        if detected_categories:
            is_safe = False
            # Use the first detected category for response
            category = next(iter(detected_categories))
            response = self.safety_responses.get(category, 
                "I cannot provide medical advice. Please consult a healthcare professional.")
            
            # Add disclaimer for multiple categories
            if len(detected_categories) > 1:
                response += " For comprehensive medical advice, please consult your doctor."
        
        return {
            "is_safe": is_safe,
            "warnings": list(warnings),
            "detected_categories": list(detected_categories),
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def filter_response(self, response: str) -> str:
        """
        Filter and sanitize LLM response to ensure safety.
        
        Args:
            response: Generated response text
        
        Returns:
            Filtered response
        """
        # Remove any potentially dangerous advice
        dangerous_patterns = [
            (r'\b(take|use|consume|drink|eat)\s+\d+\s*(mg|ml|g|oz|pills?|tablets?|capsules?)\b', 
             '[dosage information removed - consult your doctor]'),
            (r'\b(prescribe|prescription|medication|drug|medicine)\s+\w+\s+\d+\s*(mg|ml|g)\b',
             '[medication information removed - consult your doctor]'),
            (r'\b(diagnosis|diagnose|diagnosed)\s+with\s+\w+\b',
             '[diagnosis information removed - consult your doctor]'),
            (r'\b(treatment|therapy|procedure|surgery)\s+for\s+\w+\b',
             '[treatment information removed - consult your doctor]')
        ]
        
        filtered = response
        for pattern, replacement in dangerous_patterns:
            filtered = re.sub(pattern, replacement, filtered, flags=re.IGNORECASE)
        
        # Add disclaimer if not already present
        if "consult" not in filtered.lower() and "doctor" not in filtered.lower():
            filtered += "\n\nPlease note: This information is for educational purposes only. Always consult your healthcare provider for medical advice."
        
        return filtered
    
    def validate_context(self, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and filter context documents for safety.
        
        Args:
            context: List of context documents
        
        Returns:
            Filtered context
        """
        safe_context = []
        
        for doc in context:
            content = doc.get("content", "")
            
            # Check if content is safe
            if self._is_content_safe(content):
                safe_context.append(doc)
            else:
                logger.warning(f"Filtered unsafe content: {content[:100]}...")
        
        return safe_context
    
    def _is_content_safe(self, content: str) -> bool:
        """Check if content is safe to use."""
        content_lower = content.lower()
        
        # Block content with dangerous medical advice
        dangerous_patterns = [
            r'\b(take|use|consume)\s+\d+\s*(mg|ml|g|pills)\s+of\s+\w+\b',
            r'\b(prescribe|recommend|suggest)\s+\w+\s+for\s+\w+\b',
            r'\b(should|must|need to)\s+take\s+\w+\s+for\s+\w+\b',
            r'\b(diagnosis|diagnose)\s+\w+\s+with\s+\w+\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return False
        
        return True
    
    def get_safety_disclaimer(self) -> str:
        """Get the standard medical disclaimer."""
        return """IMPORTANT: This chatbot provides informational responses only and does not constitute medical advice. 
        Always consult qualified healthcare professionals for medical concerns, diagnoses, or treatment decisions. 
        In case of emergency, call your local emergency services immediately."""