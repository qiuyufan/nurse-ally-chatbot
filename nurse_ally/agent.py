import os
import openai
import json
from typing import Dict, List, Any, Optional, Tuple

# Base Agent class
class Agent:
    """Base agent class that defines the interface for all specialized agents"""
    
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
    
    def process(self, user_message: str, context: Dict[str, Any]) -> str:
        """Process a user message and return a response"""
        raise NotImplementedError("Subclasses must implement this method")

    def _prepare_messages(self, context: Dict[str, Any], user_message: str) -> List[Dict[str, str]]:
        """Prepare messages for the OpenAI API"""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history if available
        if 'conversation_history' in context and context['conversation_history']:
            for msg in context['conversation_history']:
                messages.append(msg)
        
        # Add current user message if not already in history
        if user_message and (not context.get('conversation_history') or 
                            context['conversation_history'][-1]['role'] != 'user' or 
                            context['conversation_history'][-1]['content'] != user_message):
            messages.append({"role": "user", "content": user_message})
        
        return messages

    def _call_openai_api(self, messages: List[Dict[str, str]]) -> str:
        """Call the OpenAI API with the prepared messages"""
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Can be configured based on needs
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content


class NurseAlly(Agent):
    """Main Nurse Ally agent that uses tools to provide healthcare navigation assistance"""
    
    def __init__(self):
        super().__init__(
            """You are Nurse Ally, a compassionate and professional AI health assistant helping users access 
            the right level of healthcare while traveling, studying abroad, or living as digital nomads.
            
            Your mission is to:
            - Understand the user's symptoms
            - Estimate the urgency of their situation (triage)
            - Recommend what kind of care they should seek
            - Inform them whether their insurance likely covers it
            - Show nearby clinics or care providers if needed
            
            You do not give medical diagnoses or prescriptions.
            
            You already have access to the user's profile, which includes:
            - Nationality
            - Insurance type (e.g., Travel, EHIC, Private, None)
            - Insurance provider
            - Current country and city
            - Preferred language
            - Optional: chronic conditions, allergies, care preferences
            
            Do not ask the user for this information. Instead, retrieve it from context or passed parameters.
            
            If the user reports symptoms like chest pain, fainting, difficulty breathing, bleeding, or confusion, 
            always respond with: "This may be an emergency. Please go to the nearest hospital or call the local 
            emergency number immediately."
            
            Never provide medical diagnosis. Emphasize your role is to help users decide where to go and what's 
            covered — not what illness they have.
            
            Always use simple, clear, and reassuring language. Use bullet points when listing options or steps.
            Include links to maps or helpful resources using Markdown if supported. Refer to yourself as "Nurse Ally."
            Never say you are an AI model. Stay in character as a trusted assistant."""
        )
        self.tools = {
            "triage_symptoms": self._triage_symptoms,
            "check_insurance_coverage": self._check_insurance_coverage,
            "map_search": self._map_search,
            "get_claim_checklist": self._get_claim_checklist
        }
    
    def process(self, user_message: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Process a user message using appropriate tools and return a response"""
        # Check for emergency keywords first
        emergency_keywords = ["chest pain", "fainting", "difficulty breathing", "bleeding", "confusion"]
        if any(keyword in user_message.lower() for keyword in emergency_keywords):
            emergency_response = "This may be an emergency. Please go to the nearest hospital or call the local emergency number immediately."
            return emergency_response, context
        
        # Prepare messages for the OpenAI API
        messages = self._prepare_messages(context, user_message)
        
        # Determine which tool to use based on the conversation state
        if not context.get('symptoms_assessed') and not context.get('urgency_level'):
            # If symptoms haven't been assessed yet, use the triage tool
            if any(symptom in user_message.lower() for symptom in ["pain", "hurt", "sick", "fever", "cough", "headache"]):
                symptoms_result = self._triage_symptoms({"symptoms": user_message})
                context['urgency_level'] = symptoms_result['urgency']
                context['symptoms_assessed'] = True
                context['symptoms'] = user_message
        
        # If we have symptoms and urgency but no insurance check yet
        elif context.get('symptoms_assessed') and not context.get('insurance_checked'):
            # Check insurance coverage
            insurance_type = context.get('user_profile', {}).get('insurance_type', 'Unknown')
            country = context.get('user_profile', {}).get('country', 'Unknown')
            care_level = self._map_urgency_to_care_level(context.get('urgency_level', 'mild'))
            
            coverage_result = self._check_insurance_coverage({
                "insurance_type": insurance_type,
                "country": country,
                "care_level": care_level
            })
            
            context['insurance_checked'] = True
            context['insurance_covers'] = coverage_result['covered']
            context['coverage_note'] = coverage_result['note']
        
        # If we have symptoms, urgency, and insurance check but no facility recommendations
        elif context.get('symptoms_assessed') and context.get('insurance_checked') and not context.get('facilities_recommended'):
            # Search for nearby facilities
            city = context.get('user_profile', {}).get('city', 'Unknown')
            care_level = self._map_urgency_to_care_level(context.get('urgency_level', 'mild'))
            
            if city != 'Unknown':
                map_result = self._map_search({
                    "city": city,
                    "care_level": care_level
                })
                
                context['facilities_recommended'] = True
                context['map_link'] = map_result['map_link']
        
        # Call OpenAI API to generate a response based on the updated context
        response = self._call_openai_api(messages)
        
        # If we've completed all steps, provide a claim checklist
        if context.get('symptoms_assessed') and context.get('insurance_checked') and context.get('facilities_recommended'):
            insurance_type = context.get('user_profile', {}).get('insurance_type', 'Unknown')
            care_level = self._map_urgency_to_care_level(context.get('urgency_level', 'mild'))
            
            checklist_result = self._get_claim_checklist({
                "insurance_type": insurance_type,
                "care_level": care_level
            })
            
            # Add checklist to the response
            checklist_items = "\n".join([f"- {item}" for item in checklist_result['checklist']])
            response += f"\n\nHere's a checklist of what you'll need for insurance claims:\n{checklist_items}"
        
        return response, context
    
    def _map_urgency_to_care_level(self, urgency: str) -> str:
        """Map urgency level to care level"""
        urgency_map = {
            "severe": "hospital",
            "moderate": "walk-in clinic",
            "mild": "pharmacy"
        }
        return urgency_map.get(urgency, "walk-in clinic")
    
    # Tool implementations
    def _triage_symptoms(self, input_data: Dict[str, str]) -> Dict[str, str]:
        """Triage symptoms to determine urgency level"""
        symptoms = input_data.get("symptoms", "")
        
        # Emergency keywords that indicate severe urgency
        emergency_keywords = ["chest pain", "heart", "breathing", "unconscious", "severe bleeding", 
                             "head injury", "stroke", "seizure", "anaphylaxis", "allergic reaction"]
        
        # Urgent keywords that indicate moderate urgency
        urgent_keywords = ["fever", "infection", "broken", "fracture", "sprain", "cut", "wound", 
                          "vomiting", "dehydration", "migraine", "severe pain"]
        
        # Determine urgency based on keywords
        if any(keyword in symptoms.lower() for keyword in emergency_keywords):
            return {"urgency": "severe"}
        elif any(keyword in symptoms.lower() for keyword in urgent_keywords):
            return {"urgency": "moderate"}
        else:
            return {"urgency": "mild"}
    
    def _check_insurance_coverage(self, input_data: Dict[str, str]) -> Dict[str, Any]:
        """Check if insurance covers the care level in the specified country"""
        insurance_type = input_data.get("insurance_type", "Unknown")
        country = input_data.get("country", "Unknown")
        care_level = input_data.get("care_level", "walk-in clinic")
        
        # Simple coverage rules (would be more complex in a real system)
        coverage_rules = {
            "Travel": {
                "hospital": True,
                "walk-in clinic": True,
                "pharmacy": False,
                "note": "Most travel insurance covers emergency and urgent care, but not routine pharmacy visits."
            },
            "EHIC": {
                "hospital": True,
                "walk-in clinic": True,
                "pharmacy": True,
                "note": "EHIC covers public healthcare services in EU countries at the same cost as locals."
            },
            "Private": {
                "hospital": True,
                "walk-in clinic": True,
                "pharmacy": True,
                "note": "Your private insurance likely covers all levels of care, but may require pre-authorization for hospital visits."
            },
            "None": {
                "hospital": False,
                "walk-in clinic": False,
                "pharmacy": False,
                "note": "Without insurance, you'll need to pay out-of-pocket for healthcare services."
            }
        }
        
        # Get coverage for the specified insurance type and care level
        if insurance_type in coverage_rules:
            covered = coverage_rules[insurance_type].get(care_level, False)
            note = coverage_rules[insurance_type].get("note", "")
        else:
            covered = False
            note = "I don't have specific information about your insurance type. Please check with your provider."
        
        return {
            "covered": covered,
            "note": note
        }
    
    def _map_search(self, input_data: Dict[str, str]) -> Dict[str, str]:
        """Search for healthcare facilities based on city and care level"""
        city = input_data.get("city", "")
        care_level = input_data.get("care_level", "walk-in clinic")
        
        # Map care level to search term
        search_terms = {
            "hospital": "emergency hospital",
            "walk-in clinic": "urgent care clinic",
            "pharmacy": "pharmacy"
        }
        
        search_term = search_terms.get(care_level, care_level)
        
        # Create Google Maps search URL
        map_link = f"https://www.google.com/maps/search/{search_term}+in+{city}".replace(" ", "+")
        
        return {
            "map_link": map_link
        }
    
    def _get_claim_checklist(self, input_data: Dict[str, str]) -> Dict[str, List[str]]:
        """Get a checklist of documents needed for insurance claims"""
        insurance_type = input_data.get("insurance_type", "Unknown")
        care_level = input_data.get("care_level", "walk-in clinic")
        
        # Base checklist items needed for all claims
        base_checklist = [
            "Receipt from healthcare provider",
            "Copy of passport/ID",
            "Insurance policy number"
        ]
        
        # Additional items based on insurance type and care level
        additional_items = {
            "Travel": {
                "hospital": ["Hospital discharge summary", "Medical report", "Proof of travel (e.g., flight tickets)"],
                "walk-in clinic": ["Medical report", "Proof of travel (e.g., flight tickets)"],
                "pharmacy": ["Prescription from doctor", "Proof of travel (e.g., flight tickets)"]
            },
            "EHIC": {
                "hospital": ["EHIC card details", "Hospital discharge summary"],
                "walk-in clinic": ["EHIC card details", "Medical report"],
                "pharmacy": ["EHIC card details", "Prescription from doctor"]
            },
            "Private": {
                "hospital": ["Pre-authorization form (if required)", "Hospital discharge summary", "Itemized bill"],
                "walk-in clinic": ["Medical report", "Itemized bill"],
                "pharmacy": ["Prescription from doctor"]
            }
        }
        
        # Combine base checklist with additional items
        checklist = base_checklist.copy()
        
        if insurance_type in additional_items and care_level in additional_items[insurance_type]:
            checklist.extend(additional_items[insurance_type][care_level])
        
        return {
            "checklist": checklist
        }