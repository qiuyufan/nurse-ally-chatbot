import json
import re
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple
import openai

class Agent:
    """Base Agent class"""
    def __init__(self):
        pass
    
    def process(self, message: str, conversation_history: List[Dict], user_profile: Dict) -> Dict:
        """Process a message and return a response"""
        raise NotImplementedError("Subclasses must implement process()")

class NurseAlly(Agent):
    """NurseAlly agent implementation with specialized healthcare navigation tools"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        openai.api_key = api_key
        
        # Define the system prompt
        self.system_prompt = """
        You are Nurse Ally, a compassionate and professional AI health assistant helping users access the right level of healthcare while traveling, studying abroad, or living as digital nomads.
        
        Your mission is to:
        - Understand the user's symptoms
        - Estimate the urgency of their situation (triage)
        - Recommend what kind of care they should seek
        - Inform them whether their insurance likely covers it
        - Show nearby clinics or care providers if needed
        
        You do not give medical diagnoses or prescriptions.
        
        SAFETY BEHAVIOR:
        If the user reports symptoms like chest pain, fainting, difficulty breathing, bleeding, or confusion, always respond with:
        "This may be an emergency. Please go to the nearest hospital or call the local emergency number immediately."
        
        Never provide medical diagnosis. Emphasize your role is to help users decide where to go and what's covered — not what illness they have.
        
        STYLE GUIDE:
        - Always use simple, clear, and reassuring language.
        - Use bullet points when listing options or steps.
        - Include links to maps or helpful resources using Markdown if supported.
        - Refer to yourself as "Nurse Ally."
        - Never say you are an AI model. Stay in character as a trusted assistant.
        """
        
        # Initialize conversation state
        self.conversation_state = {
            "symptoms_assessed": False,
            "insurance_checked": False,
            "facility_recommended": False,
            "emergency_detected": False
        }
        
        # Emergency keywords that trigger immediate hospital recommendation
        self.emergency_keywords = [
            "chest pain", "heart attack", "stroke", "unconscious", "fainted", "fainting",
            "difficulty breathing", "can't breathe", "severe bleeding", "heavy bleeding",
            "head injury", "broken bone", "fracture", "seizure", "convulsion", "poisoning",
            "overdose", "suicide", "suicidal", "severe burn", "electric shock", "drowning",
            "choking", "anaphylaxis", "allergic reaction", "severe pain", "paralysis",
            "gunshot", "stab wound", "car accident", "traffic accident", "fall from height"
        ]
    
    def process(self, message: str, conversation_history: List[Dict], user_profile: Dict) -> Dict:
        """Process a message and return a response with appropriate healthcare guidance"""
        # Check for emergency keywords
        if self._check_for_emergency(message):
            self.conversation_state["emergency_detected"] = True
            return {
                "response": "This may be an emergency. Please go to the nearest hospital or call the local emergency number immediately.",
                "conversation_state": self.conversation_state
            }
        
        # Determine which tool to use based on conversation state
        if not self.conversation_state["symptoms_assessed"]:
            # First assess symptoms and urgency
            urgency = self._triage_symptoms(message)
            self.conversation_state["symptoms_assessed"] = True
            self.conversation_state["urgency"] = urgency
            
            # Determine appropriate care level based on urgency
            care_level = self._determine_care_level(urgency)
            self.conversation_state["care_level"] = care_level
            
            # Prepare next step to check insurance
            next_step = "Now, let me check if your insurance is likely to cover this type of care."
            
            response = self._generate_response(message, conversation_history, user_profile, {
                "tool_used": "triage_symptoms",
                "urgency": urgency,
                "care_level": care_level,
                "next_step": next_step
            })
            
        elif not self.conversation_state["insurance_checked"]:
            # Check insurance coverage
            insurance_type = user_profile.get("insurance_type", "None")
            country = user_profile.get("country", "Unknown")
            care_level = self.conversation_state.get("care_level", "walk-in clinic")
            
            coverage_info = self._check_insurance_coverage(insurance_type, country, care_level)
            self.conversation_state["insurance_checked"] = True
            self.conversation_state["coverage_info"] = coverage_info
            
            # Prepare next step to recommend facilities
            next_step = "Let me help you find a suitable healthcare facility nearby."
            
            response = self._generate_response(message, conversation_history, user_profile, {
                "tool_used": "check_insurance_coverage",
                "coverage_info": coverage_info,
                "next_step": next_step
            })
            
        elif not self.conversation_state["facility_recommended"]:
            # Recommend healthcare facilities
            city = user_profile.get("city", "")
            care_level = self.conversation_state.get("care_level", "walk-in clinic")
            
            map_link = None
            if city:
                map_info = self._map_search(city, care_level)
                map_link = map_info["map_link"]
            
            self.conversation_state["facility_recommended"] = True
            
            # Generate claim checklist if all steps are completed
            checklist = None
            if self.conversation_state["symptoms_assessed"] and self.conversation_state["insurance_checked"]:
                insurance_type = user_profile.get("insurance_type", "None")
                care_level = self.conversation_state.get("care_level", "walk-in clinic")
                checklist_info = self._get_claim_checklist(insurance_type, care_level)
                checklist = checklist_info["checklist"]
            
            response = self._generate_response(message, conversation_history, user_profile, {
                "tool_used": "map_search",
                "map_link": map_link,
                "checklist": checklist
            })
            
        else:
            # General conversation after all steps are completed
            response = self._generate_response(message, conversation_history, user_profile, {
                "tool_used": "general_conversation"
            })
        
        return response
    
    def _check_for_emergency(self, message: str) -> bool:
        """Check if the message contains emergency keywords"""
        message_lower = message.lower()
        for keyword in self.emergency_keywords:
            if keyword in message_lower:
                return True
        return False
    
    def _determine_care_level(self, urgency: str) -> str:
        """Determine appropriate care level based on urgency"""
        if urgency == "severe":
            return "hospital"
        elif urgency == "moderate":
            return "walk-in clinic"
        else:  # mild
            return "pharmacy"
    
    def _triage_symptoms(self, symptoms_description: str) -> str:
        """Tool 1: Triage symptoms to determine urgency level"""
        # Convert to lowercase for case-insensitive matching
        symptoms_lower = symptoms_description.lower()
        
        # Define keyword lists for different urgency levels
        severe_keywords = [
            "severe", "intense", "extreme", "unbearable", "excruciating",
            "chest pain", "difficulty breathing", "shortness of breath",
            "high fever", "fever above 103", "fever above 39.5",
            "coughing blood", "vomiting blood", "blood in stool", "blood in urine",
            "severe headache", "worst headache", "sudden headache",
            "confusion", "disorientation", "loss of consciousness",
            "unable to move", "paralysis", "stroke", "heart attack",
            "severe allergic reaction", "anaphylaxis", "swollen throat",
            "unable to swallow", "severe dehydration", "severe burn",
            "deep cut", "large wound", "heavy bleeding", "won't stop bleeding",
            "broken bone", "fracture", "dislocation", "head injury",
            "seizure", "convulsion", "poisoning", "overdose"
        ]
        
        moderate_keywords = [
            "moderate", "significant", "concerning", "persistent",
            "fever", "high temperature", "infection", "infected",
            "ear pain", "sinus pain", "toothache", "dental pain",
            "sprain", "strain", "twisted ankle", "joint pain",
            "migraine", "vomiting", "diarrhea", "dehydration",
            "rash", "skin infection", "eye infection", "pink eye",
            "urinary tract infection", "UTI", "kidney infection",
            "moderate pain", "unable to keep food down", "unable to keep liquids down",
            "asthma attack", "wheezing", "moderate allergic reaction",
            "cut requiring stitches", "minor burn", "insect bite with swelling",
            "flu symptoms", "covid symptoms", "strep throat", "bronchitis",
            "moderate bleeding", "minor injury", "sports injury"
        ]
        
        # Check for severe symptoms first (higher priority)
        for keyword in severe_keywords:
            if keyword in symptoms_lower:
                return "severe"
        
        # Then check for moderate symptoms
        for keyword in moderate_keywords:
            if keyword in symptoms_lower:
                return "moderate"
        
        # Default to mild if no severe or moderate keywords found
        return "mild"
    
    def _check_insurance_coverage(self, insurance_type: str, country: str, care_level: str) -> Dict:
        """Tool 2: Check if insurance likely covers the care level in the given country"""
        # Simplified coverage rules
        coverage_rules = {
            "Travel": {
                "hospital": {"covered": True, "note": "Most travel insurance covers emergency hospital visits, but you may need to pay upfront and claim later."},
                "walk-in clinic": {"covered": True, "note": "Travel insurance typically covers urgent care clinics, but check your policy limits."},
                "pharmacy": {"covered": False, "note": "Most travel insurance doesn't cover routine pharmacy visits unless prescribed by a doctor they approved."}
            },
            "EHIC": {
                "hospital": {"covered": True, "note": "EHIC covers emergency and necessary hospital treatment in EU countries at the same cost as locals."},
                "walk-in clinic": {"covered": "maybe", "note": "EHIC coverage for walk-in clinics varies by country. In some EU countries, you may need to visit public facilities only."},
                "pharmacy": {"covered": "maybe", "note": "EHIC may provide reduced-cost prescriptions in EU countries, but over-the-counter medications are typically not covered."}
            },
            "Private": {
                "hospital": {"covered": "maybe", "note": "Check if your private insurance has international coverage. You may need pre-authorization for hospital visits."},
                "walk-in clinic": {"covered": "maybe", "note": "Some private insurance plans cover international urgent care, but often with higher co-pays."},
                "pharmacy": {"covered": "maybe", "note": "Private insurance coverage for international pharmacy visits varies widely by provider."}
            },
            "None": {
                "hospital": {"covered": False, "note": "Without insurance, you'll be responsible for all hospital costs. Consider travel insurance for future trips."},
                "walk-in clinic": {"covered": False, "note": "You'll need to pay out-of-pocket for walk-in clinic services."},
                "pharmacy": {"covered": False, "note": "You'll need to pay the full price for medications and pharmacy services."}
            }
        }
        
        # Get coverage info based on insurance type and care level
        if insurance_type in coverage_rules and care_level in coverage_rules[insurance_type]:
            return coverage_rules[insurance_type][care_level]
        else:
            return {"covered": "maybe", "note": "I don't have specific information about your insurance coverage. Please check with your provider."}
    
    def _map_search(self, city: str, care_level: str) -> Dict:
        """Tool 3: Generate map search URL for healthcare facilities"""
        # Map care level to search query
        search_queries = {
            "hospital": "hospitals",
            "walk-in clinic": "urgent care clinics",
            "pharmacy": "pharmacies"
        }
        
        search_query = search_queries.get(care_level, "healthcare")
        
        # Create Google Maps search URL
        encoded_query = urllib.parse.quote(f"{search_query} in {city}")
        map_link = f"https://www.google.com/maps/search/{encoded_query}"
        
        return {"map_link": map_link}
    
    def _get_claim_checklist(self, insurance_type: str, care_level: str) -> Dict:
        """Tool 4: Generate checklist of documents needed for insurance claims"""
        # Base checklist items needed for all claims
        base_checklist = [
            "Receipt with itemized costs from the healthcare provider",
            "Medical report or treatment summary",
            "Copy of your passport/ID",
            "Copy of your insurance card/policy"
        ]
        
        # Additional items based on insurance type
        additional_items = {
            "Travel": [
                "Completed claim form from your travel insurance provider",
                "Proof of travel (e.g., flight tickets or boarding passes)"
            ],
            "EHIC": [
                "EHIC card details",
                "Any forms provided by the healthcare facility for EHIC patients"
            ],
            "Private": [
                "Pre-authorization documentation (if required by your insurance)",
                "Referral documentation (if you were referred by another doctor)"
            ],
            "None": [
                "Consider applying for emergency assistance from your embassy/consulate",
                "Ask the healthcare provider about payment plans or discounts for self-pay patients"
            ]
        }
        
        # Additional items based on care level
        care_level_items = {
            "hospital": [
                "Discharge summary",
                "Any lab or test results",
                "Prescription copies for medications"
            ],
            "walk-in clinic": [
                "Visit summary",
                "Follow-up instructions"
            ],
            "pharmacy": [
                "Prescription from doctor (if applicable)",
                "Packaging or information leaflets for medications purchased"
            ]
        }
        
        # Combine all relevant checklist items
        checklist = base_checklist.copy()
        
        if insurance_type in additional_items:
            checklist.extend(additional_items[insurance_type])
        
        if care_level in care_level_items:
            checklist.extend(care_level_items[care_level])
        
        return {"checklist": checklist}
    
    def _generate_response(self, message: str, conversation_history: List[Dict], user_profile: Dict, context: Dict) -> Dict:
        """Generate a response using OpenAI API based on the conversation context"""
        # Prepare messages for the API call
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add conversation history (limited to last 10 messages for context)
        for entry in conversation_history[-10:]:
            if entry["role"] == "user":
                messages.append({"role": "user", "content": entry["content"]})
            else:
                messages.append({"role": "assistant", "content": entry["content"]})
        
        # Add current message if not in history
        if not conversation_history or conversation_history[-1]["content"] != message:
            messages.append({"role": "user", "content": message})
        
        # Add user profile context
        profile_context = "User profile information:\n"
        for key, value in user_profile.items():
            if value:  # Only include non-empty values
                profile_context += f"- {key}: {value}\n"
        
        messages.append({"role": "system", "content": profile_context})
        
        # Add tool context
        tool_context = "Based on my analysis:\n"
        
        if context["tool_used"] == "triage_symptoms":
            tool_context += f"- Symptom urgency: {context['urgency']}\n"
            tool_context += f"- Recommended care level: {context['care_level']}\n"
            tool_context += f"- {context['next_step']}\n"
        
        elif context["tool_used"] == "check_insurance_coverage":
            coverage = "covered" if context['coverage_info']['covered'] == True else \
                      "not covered" if context['coverage_info']['covered'] == False else "possibly covered"
            
            tool_context += f"- Insurance coverage: {coverage}\n"
            tool_context += f"- Coverage note: {context['coverage_info']['note']}\n"
            tool_context += f"- {context['next_step']}\n"
        
        elif context["tool_used"] == "map_search":
            if context.get("map_link"):
                tool_context += f"- I can provide a map link to nearby healthcare facilities.\n"
            else:
                tool_context += f"- I don't have your location information to provide facility recommendations.\n"
            
            if context.get("checklist"):
                tool_context += f"- I can provide a checklist of documents needed for insurance claims.\n"
        
        messages.append({"role": "system", "content": tool_context})
        
        # Call OpenAI API
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",  # or another appropriate model
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content
            
            # Prepare the response object
            result = {
                "response": response_text,
                "conversation_state": self.conversation_state
            }
            
            # Add map link if available
            if context["tool_used"] == "map_search" and context.get("map_link"):
                result["map_link"] = context["map_link"]
            
            # Add checklist if available
            if context.get("checklist"):
                result["checklist"] = context["checklist"]
            
            return result
            
        except Exception as e:
            # Fallback response in case of API error
            return {
                "response": f"I'm having trouble processing your request right now. Please try again in a moment.",
                "conversation_state": self.conversation_state
            }
    
    def reset(self) -> None:
        """Reset the conversation state"""
        self.conversation_state = {
            "symptoms_assessed": False,
            "insurance_checked": False,
            "facility_recommended": False,
            "emergency_detected": False
        }