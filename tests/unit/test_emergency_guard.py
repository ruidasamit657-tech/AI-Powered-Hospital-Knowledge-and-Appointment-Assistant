"""
Unit tests for emergency guard service
"""

import pytest
from app.services.emergency_guard import EmergencyGuard

class TestEmergencyGuard:
    """Test emergency detection functionality"""
    
    @pytest.fixture
    def emergency_guard(self):
        """Create emergency guard instance"""
        return EmergencyGuard()
    
    def test_detect_heart_attack(self, emergency_guard):
        """Test heart attack detection"""
        is_emergency, keywords = emergency_guard.detect_emergency(
            "I think I'm having a heart attack!"
        )
        assert is_emergency == True
        assert "heart attack" in " ".join(keywords).lower()

    def test_detect_chest_pain(self, emergency_guard):
        """Test chest pain detection"""
        is_emergency, keywords = emergency_guard.detect_emergency(
            "I have severe chest pain"
        )
        assert is_emergency == True
        assert "chest pain" in " ".join(keywords).lower()

    def test_detect_stroke(self, emergency_guard):
        """Test stroke detection"""
        is_emergency, _ = emergency_guard.detect_emergency(
            "I can't move my arm and my speech is slurred"
        )
        assert is_emergency == True

    def test_detect_bleeding(self, emergency_guard):
        """Test severe bleeding detection"""
        is_emergency, _ = emergency_guard.detect_emergency(
            "I have severe bleeding and can't stop it"
        )
        assert is_emergency == True

    def test_detect_breathing_difficulty(self, emergency_guard):
        """Test breathing difficulty detection"""
        is_emergency, _ = emergency_guard.detect_emergency(
            "I can't breathe properly"
        )
        assert is_emergency == True

    def test_no_false_emergency(self, emergency_guard):
        """Test that non-emergency queries don't trigger"""
        is_emergency, keywords = emergency_guard.detect_emergency(
            "What are the hospital visiting hours?"
        )
        assert is_emergency == False
        assert len(keywords) == 0

    def test_emergency_911(self, emergency_guard):
        """Test 911 emergency detection"""
        is_emergency, _ = emergency_guard.detect_emergency(
            "Call 911 immediately!"
        )
        assert is_emergency == True

    def test_ambulance_detection(self, emergency_guard):
        """Test ambulance detection"""
        is_emergency, _ = emergency_guard.detect_emergency(
            "I need an ambulance"
        )
        assert is_emergency == True

    def test_emergency_response_format(self, emergency_guard):
        """Test emergency response format"""
        response = emergency_guard.get_emergency_response("test query")
        assert "⚠️ MEDICAL EMERGENCY DETECTED ⚠️" in response
        assert "CALL EMERGENCY SERVICES IMMEDIATELY" in response
        assert "911" in response
        assert "emergency code" in response