import re
from typing import Dict, Any
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)

class EmergencyGuard:
    """Emergency detection and response system."""
    
    def __init__(self):
        """Initialize emergency guard with emergency patterns."""
        self.emergency_patterns = {
            'severe': [
                (r'\b(chest pain|heart attack|heart pain|cardiac arrest)\b', 'chest_pain'),
                (r'\b(stroke|brain attack|paralysis|numbness|facial drooping)\b', 'stroke'),
                (r'\b(severe bleeding|uncontrolled bleeding|hemorrhage)\b', 'bleeding'),
                (r'\b(difficulty breathing|cannot breathe|choking|suffocating)\b', 'breathing'),
                (r'\b(unconscious|passed out|fainted|unresponsive)\b', 'unconscious'),
                (r'\b(suicidal|suicide|self-harm|kill myself)\b', 'suicide'),
                (r'\b(overdose|drug overdose|poisoning)\b', 'overdose'),
                (r'\b(severe allergic reaction|anaphylaxis|anaphylactic)\b', 'allergic'),
            ],
            'urgent': [
                (r'\b(severe pain|excruciating pain|agonizing pain)\b', 'severe_pain'),
                (r'\b(high fever|very high temperature|fever over 104)\b', 'high_fever'),
                (r'\b(severe headache|migraine|worst headache)\b', 'severe_headache'),
                (r'\b(vomiting blood|blood in vomit|hematemesis)\b', 'vomiting_blood'),
                (r'\b(blood in stool|rectal bleeding)\b', 'blood_stool'),
                (r'\b(confusion|disorientation|delirium)\b', 'confusion'),
                (r'\b(seizure|convulsion|fit|epileptic)\b', 'seizure'),
            ],
            'psychiatric': [
                (r'\b(panic attack|anxiety attack|severe anxiety)\b', 'panic_attack'),
                (r'\b(hallucination|seeing things|hearing voices)\b', 'hallucination'),
                (r'\b(psychotic|psychosis|paranoid|delusional)\b', 'psychosis'),
                (r'\b(depression|severe depression|suicidal thoughts)\b', 'depression'),
                (r'\b(manic|mania|bipolar episode)\b', 'mania'),
            ]
        }
        
        self.emergency_responses = {
            'chest_pain': "⚠️ EMERGENCY: Chest pain or heart attack symptoms detected. Please call emergency services (911) immediately.",
            'stroke': "⚠️ EMERGENCY: Stroke symptoms detected. Please call emergency services (911) immediately.",
            'bleeding': "⚠️ EMERGENCY: Severe bleeding detected. Please call emergency services (911) immediately.",
            'breathing': "⚠️ EMERGENCY: Breathing difficulty detected. Please call emergency services (911) immediately.",
            'unconscious': "⚠️ EMERGENCY: Unconsciousness detected. Please call emergency services (911) immediately.",
            'suicide': "⚠️ CRISIS: Suicidal thoughts detected. Please call the Suicide Prevention Lifeline at 988 or emergency services (911) immediately.",
            'overdose': "⚠️ EMERGENCY: Overdose detected. Please call emergency services (911) or Poison Control (1-800-222-1222) immediately.",
            'allergic': "⚠️ EMERGENCY: Severe allergic reaction detected. Please call emergency services (911) immediately.",
            'severe_pain': "⚠️ URGENT: Severe pain detected. Please seek immediate medical attention or call emergency services.",
            'high_fever': "⚠️ URGENT: High fever detected. Please seek medical attention immediately.",
            'severe_headache': "⚠️ URGENT: Severe headache detected. Please seek medical attention immediately.",
            'vomiting_blood': "⚠️ URGENT: Blood in vomit detected. Please seek immediate medical attention.",
            'blood_stool': "⚠️ URGENT: Blood in stool detected. Please seek immediate medical attention.",
            'confusion': "⚠️ URGENT: Confusion or disorientation detected. Please seek immediate medical attention.",
            'seizure': "⚠️ URGENT: Seizure detected. Please seek immediate medical attention.",
            'panic_attack': "⚠️ URGENT: Panic attack detected. Please stay calm and seek medical attention if needed.",
            'hallucination': "⚠️ URGENT: Hallucination detected. Please seek immediate medical attention.",
            'psychosis': "⚠️ URGENT: Psychotic symptoms detected. Please seek immediate psychiatric attention.",
            'depression': "⚠️ URGENT: Severe depression detected. Please reach out to a mental health professional or call the Suicide Prevention Lifeline at 988.",
            'mania': "⚠️ URGENT: Manic episode detected. Please seek immediate psychiatric attention."
        }
        
        self.resources = {
            'emergency': "Emergency Services: 911",
            'suicide': "Suicide Prevention Lifeline: 988",
            'poison': "Poison Control: 1-800-222-1222",
            'crisis': "Crisis Text Line: Text HOME to 741741",
            'mental_health': "SAMHSA National Helpline: 1-800-662-4357"
        }
    
    def check_emergency(self, query: str) -> Dict[str, Any]:
        """
        Check if a query contains emergency-related content.
        
        Args:
            query: User query text
        
        Returns:
            Dictionary with emergency detection results
        """
        query_lower = query.lower()
        
        detected_emergencies = []
        urgency_level = 'none'
        
        # Check each category
        for category, patterns in self.emergency_patterns.items():
            for pattern, emergency_type in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    detected_emergencies.append({
                        'type': emergency_type,
                        'category': category,
                        'pattern': pattern
                    })
        
        # Determine urgency level
        if detected_emergencies:
            categories = set([e['category'] for e in detected_emergencies])
            if 'severe' in categories:
                urgency_level = 'severe'
            elif 'urgent' in categories:
                urgency_level = 'urgent'
            elif 'psychiatric' in categories:
                urgency_level = 'psychiatric'
        
        # Generate response
        if urgency_level != 'none':
            # Get primary emergency
            primary_emergency = detected_emergencies[0]
            response = self.emergency_responses.get(
                primary_emergency['type'],
                "⚠️ URGENT: Emergency situation detected. Please seek immediate medical attention or call emergency services."
            )
            
            # Add resources
            resources = []
            if 'suicide' in query_lower or 'suicidal' in query_lower:
                resources.append(self.resources['suicide'])
            if any(term in query_lower for term in ['overdose', 'poison']):
                resources.append(self.resources['poison'])
            
            if 'severe' in urgency_level or 'emergency' in query_lower:
                resources.append(self.resources['emergency'])
            
            if resources:
                response += f"\n\n📞 Resources: {', '.join(resources)}"
            
            # Add mental health resources for psychiatric emergencies
            if urgency_level == 'psychiatric':
                response += "\n\n🧠 Mental Health Resources:"
                response += f"\n- {self.resources['suicide']}"
                response += f"\n- {self.resources['crisis']}"
                response += f"\n- {self.resources['mental_health']}"
            
            return {
                "is_emergency": True,
                "type": urgency_level,
                "detected": detected_emergencies,
                "response": response,
                "resources": resources,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "is_emergency": False,
            "type": "none",
            "detected": [],
            "response": None,
            "resources": [],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_emergency_response(self, query: str) -> str:
        """Return the emergency response text for a query."""
        return self.check_emergency(query)["response"] or ""