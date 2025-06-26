import os
import openai
import json
import requests
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, session
from functools import wraps

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI API with key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "nurse-ally-secret-key")

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# ===== MODULAR AGENT SYSTEM =====
# Each agent is implemented as a separate class with a consistent interface

class Agent:
    """Base agent class that defines the interface for all specialized agents"""
    
    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
    
    def process(self, user_message, conversation_history):
        """Process a user message and return a response"""
        raise NotImplementedError("Subclasses must implement this method")


class CoordinatorAgent(Agent):
    """Manages conversation flow and delegates to specialized agents"""
    
    def __init__(self):
        super().__init__("You are Nurse Ally, a kind and professional AI nurse coordinator. "
                         "Your role is to manage the conversation flow, determine which specialized agent to call, "
                         "and synthesize their responses. You ask questions about symptoms, location, insurance "
                         "and make the final suggestions. You do NOT give medical advice, only logistics and "
                         "urgency-based recommendations.")
    
    def process(self, user_message, conversation_history):
        # Call OpenAI API with coordinator prompt
        messages = self._prepare_messages(conversation_history, user_message)
        response = self._call_openai_api(messages)
        return response, conversation_history
    
    def _prepare_messages(self, conversation_history, user_message):
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history
        for msg in conversation_history['messages']:
            messages.append(msg)
        
        # Add current user message if not in history
        if user_message and (not conversation_history['messages'] or 
                            conversation_history['messages'][-1]['role'] != 'user' or 
                            conversation_history['messages'][-1]['content'] != user_message):
            messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _call_openai_api(self, messages):
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content


class SymptomAssessmentAgent(Agent):
    """Assesses symptoms and determines urgency level"""
    
    def __init__(self):
        super().__init__("You are the Symptom Assessment Agent for Nurse Ally. "
                         "Your role is to ask detailed questions about the user's symptoms, assess their urgency level, "
                         "and determine if immediate medical attention is needed. You should classify urgency as: "
                         "'Emergency' (needs immediate medical attention), 'Urgent' (should be seen within 24 hours), "
                         "or 'Routine' (can wait for regular appointment). You do NOT provide medical advice or diagnoses, "
                         "only assess urgency based on reported symptoms.")
    
    def process(self, user_message, conversation_history):
        # Call OpenAI API with symptom assessment prompt
        messages = self._prepare_messages(conversation_history, user_message)
        response = self._call_openai_api(messages)
        
        # Extract symptom data and urgency level
        updated_history = self._extract_symptom_data(user_message, response, conversation_history)
        
        return response, updated_history
    
    def _prepare_messages(self, conversation_history, user_message):
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history
        for msg in conversation_history['messages']:
            messages.append(msg)
        
        # Add current user message if not in history
        if user_message and (not conversation_history['messages'] or 
                            conversation_history['messages'][-1]['role'] != 'user' or 
                            conversation_history['messages'][-1]['content'] != user_message):
            messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _call_openai_api(self, messages):
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    def _extract_symptom_data(self, user_message, assistant_message, conversation_history):
        # Initialize symptom data if not already present
        if 'symptom_data' not in conversation_history:
            conversation_history['symptom_data'] = {}
        
        # Extract symptoms from user message
        symptom_keywords = ['pain', 'hurt', 'sick', 'fever', 'cough', 'headache', 'injury', 'nausea', 'vomiting', 'dizziness']
        for keyword in symptom_keywords:
            if keyword in user_message.lower():
                conversation_history['symptom_data'][keyword] = True
        
        # Extract urgency level from assistant message
        urgency_indicators = {
            'emergency': ['emergency', 'immediate', 'severe', 'critical', '911', 'ambulance'],
            'urgent': ['urgent', 'soon', 'concerning', '24 hours', 'today'],
            'routine': ['routine', 'mild', 'regular', 'appointment']
        }
        
        for level, indicators in urgency_indicators.items():
            if any(indicator in assistant_message.lower() for indicator in indicators):
                conversation_history['urgency_level'] = level
                break
        
        return conversation_history


class InsuranceVerificationAgent(Agent):
    """Verifies insurance coverage and provides information about covered facilities"""
    
    def __init__(self):
        super().__init__("You are the Insurance Verification Agent for Nurse Ally. "
                         "Your role is to ask about the user's insurance provider, plan details, and verify coverage options. "
                         "You should help users understand what types of care facilities their insurance covers "
                         "(emergency rooms, urgent care, primary care, etc.) and any network restrictions. "
                         "You should be knowledgeable about major insurance providers and their typical coverage policies.")
    
    def process(self, user_message, conversation_history):
        # Call OpenAI API with insurance verification prompt
        messages = self._prepare_messages(conversation_history, user_message)
        response = self._call_openai_api(messages)
        
        # Extract insurance data
        updated_history = self._extract_insurance_data(user_message, response, conversation_history)
        
        return response, updated_history
    
    def _prepare_messages(self, conversation_history, user_message):
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history
        for msg in conversation_history['messages']:
            messages.append(msg)
        
        # Add current user message if not in history
        if user_message and (not conversation_history['messages'] or 
                            conversation_history['messages'][-1]['role'] != 'user' or 
                            conversation_history['messages'][-1]['content'] != user_message):
            messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _call_openai_api(self, messages):
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    def _extract_insurance_data(self, user_message, assistant_message, conversation_history):
        # Initialize insurance data if not already present
        if 'insurance_data' not in conversation_history:
            conversation_history['insurance_data'] = {}
        
        # Extract insurance provider from user message
        insurance_providers = ['aetna', 'blue cross', 'blue shield', 'cigna', 'humana', 'kaiser', 'medicare', 'medicaid', 'united healthcare', 'anthem']
        for provider in insurance_providers:
            if provider in user_message.lower():
                conversation_history['insurance_data']['provider'] = provider
        
        # Check if insurance file was uploaded
        if 'insurance_file' in conversation_history:
            conversation_history['insurance_data']['file_uploaded'] = True
        
        return conversation_history


class FacilityRecommendationAgent(Agent):
    """Recommends healthcare facilities based on location, symptoms, and insurance"""
    
    def __init__(self):
        super().__init__("You are the Facility Recommendation Agent for Nurse Ally. "
                         "Your role is to recommend appropriate healthcare facilities based on the user's location, "
                         "symptom urgency, and insurance coverage. You should consider factors like proximity, "
                         "wait times, facility type (ER, urgent care, primary care), and insurance network status. "
                         "When possible, provide specific facility names, addresses, and contact information.")
    
    def process(self, user_message, conversation_history):
        # Call OpenAI API with facility recommendation prompt
        messages = self._prepare_messages(conversation_history, user_message)
        response = self._call_openai_api(messages)
        
        # Search for nearby facilities based on conversation data
        facilities = self._search_nearby_facilities(conversation_history)
        
        return response, conversation_history, facilities
    
    def _prepare_messages(self, conversation_history, user_message):
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history
        for msg in conversation_history['messages']:
            messages.append(msg)
        
        # Add current user message if not in history
        if user_message and (not conversation_history['messages'] or 
                            conversation_history['messages'][-1]['role'] != 'user' or 
                            conversation_history['messages'][-1]['content'] != user_message):
            messages.append({"role": "user", "content": user_message})
        
        # Add location data if available
        if 'location_data' in conversation_history and conversation_history['location_data'].get('detected'):
            location_info = f"User's location: Latitude {conversation_history['location_data'].get('latitude')}, Longitude {conversation_history['location_data'].get('longitude')}"
            messages.append({"role": "system", "content": location_info})
        
        # Add symptom data if available
        if 'symptom_data' in conversation_history and conversation_history.get('urgency_level'):
            symptom_info = f"Symptom urgency level: {conversation_history.get('urgency_level')}"
            messages.append({"role": "system", "content": symptom_info})
        
        # Add insurance data if available
        if 'insurance_data' in conversation_history and 'provider' in conversation_history['insurance_data']:
            insurance_info = f"Insurance provider: {conversation_history['insurance_data']['provider']}"
            messages.append({"role": "system", "content": insurance_info})
        
        return messages
    
    def _call_openai_api(self, messages):
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    def _search_nearby_facilities(self, conversation_history):
        # This would typically call an external API to find nearby healthcare facilities
        # For now, we'll return mock data based on the conversation history
        facilities = []
        
        # Only proceed if we have location data
        if 'location_data' not in conversation_history or not conversation_history['location_data'].get('detected'):
            return facilities
        
        # Determine facility type based on urgency level
        urgency_level = conversation_history.get('urgency_level', 'routine')
        facility_types = []
        
        if urgency_level == 'emergency':
            facility_types = ['Emergency Room']
        elif urgency_level == 'urgent':
            facility_types = ['Urgent Care', 'Emergency Room']
        else:  # routine
            facility_types = ['Primary Care', 'Urgent Care']
        
        # Mock facilities based on urgency
        for i, facility_type in enumerate(facility_types):
            facilities.append({
                "name": f"{facility_type} Center {i+1}",
                "address": f"{100+i} Medical Parkway, Healthcare City",
                "distance": f"{i+1} miles",
                "type": facility_type,
                "rating": 4.5 - (i * 0.2),
                "wait_time": f"{(i+1) * 15} minutes",
                "insurance_accepted": True if 'insurance_data' in conversation_history else "Unknown",
                "services": ["General Care", "X-ray", "Lab Services"],
                "phone": f"555-{100+i}",
                "website": f"https://example.com/facility{i+1}",
                "google_maps_url": f"https://maps.google.com/?q={100+i}+Medical+Parkway+Healthcare+City"
            })
        
        return facilities

# ===== AGENT MANAGER =====
# Manages agent instances and handles agent selection and handoff

class AgentManager:
    """Manages agent instances and handles agent selection and handoff"""
    
    def __init__(self):
        # Initialize agent instances
        self.agents = {
            "coordinator": CoordinatorAgent(),
            "symptom_assessment": SymptomAssessmentAgent(),
            "insurance_verification": InsuranceVerificationAgent(),
            "facility_recommendation": FacilityRecommendationAgent()
        }
        self.current_agent = "coordinator"  # Default agent
    
    def process_message(self, user_message, conversation_history):
        """Process a user message using the appropriate agent"""
        # Determine which agent to use based on the message and conversation state
        agent_type = self._determine_agent(user_message, conversation_history)
        
        # Get the agent instance
        agent = self.agents[agent_type]
        
        # Process the message with the selected agent
        if agent_type == "facility_recommendation":
            response, updated_history, facilities = agent.process(user_message, conversation_history)
            return response, updated_history, agent_type, facilities
        else:
            response, updated_history = agent.process(user_message, conversation_history)
            return response, updated_history, agent_type, None
    
    def _determine_agent(self, user_message, conversation_history):
        """Determine which agent should handle the current message"""
        # Check for explicit handoff keywords in the user message
        symptom_keywords = ['pain', 'hurt', 'sick', 'fever', 'cough', 'headache', 'injury', 'nausea', 'vomiting', 'dizziness', 'symptoms']
        insurance_keywords = ['insurance', 'coverage', 'plan', 'provider', 'aetna', 'blue cross', 'blue shield', 'cigna', 'humana', 'kaiser', 'medicare', 'medicaid']
        location_keywords = ['location', 'near me', 'nearby', 'closest', 'address', 'where']
        facility_keywords = ['hospital', 'clinic', 'doctor', 'emergency room', 'er', 'urgent care', 'facility', 'recommendation']
        
        # Check if the message contains keywords for a specific agent
        if any(keyword in user_message.lower() for keyword in symptom_keywords):
            return "symptom_assessment"
        elif any(keyword in user_message.lower() for keyword in insurance_keywords):
            return "insurance_verification"
        elif any(keyword in user_message.lower() for keyword in facility_keywords) or \
             any(keyword in user_message.lower() for keyword in location_keywords):
            return "facility_recommendation"
        
        # If no specific keywords, check the conversation state to determine next steps
        has_symptoms = bool(conversation_history.get('symptom_data', {}))
        has_insurance = bool(conversation_history.get('insurance_data', {}))
        has_location = conversation_history.get('location_data', {}).get('detected', False)
        
        # If we have all the necessary information, recommend facilities
        if has_symptoms and has_insurance and has_location:
            return "facility_recommendation"
        # If we have symptoms but no insurance, ask about insurance
        elif has_symptoms and not has_insurance:
            return "insurance_verification"
        # If we have no symptoms, start with symptom assessment
        elif not has_symptoms:
            return "symptom_assessment"
        # Default to coordinator for general conversation management
        else:
            return "coordinator"


# Initialize the agent manager as a global variable
agent_manager = AgentManager()


@app.route('/')
def index():
    return render_template('index.html')

# Initialize or get conversation history from session
def get_conversation_history():
    if 'conversation' not in session:
        session['conversation'] = {
            'messages': [],
            'current_agent': 'coordinator',
            'symptom_data': {},
            'insurance_data': {},
            'location_data': {},
            'urgency_level': None,
            'insurance_file': None,
            'treatment_available': None,
            'insurance_covers': None
        }
    return session['conversation']

# Helper function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_analysis(conversation):
    """Generate an analysis of the user's symptoms, urgency, and insurance coverage"""
    # Extract relevant data from the conversation
    symptoms = list(conversation.get('symptom_data', {}).keys())
    urgency = conversation.get('urgency_level', 'routine')
    insurance = conversation.get('insurance_data', {}).get('provider', 'Unknown')
    
    # Generate a simple analysis message
    if not symptoms:
        return "No symptoms have been reported yet."
    
    symptom_text = ", ".join(symptoms)
    
    urgency_descriptions = {
        'emergency': "This appears to be an emergency situation that requires immediate medical attention.",
        'urgent': "This situation appears to be urgent and should be addressed within 24 hours.",
        'routine': "This appears to be a routine matter that can be addressed during a regular appointment."
    }
    
    urgency_text = urgency_descriptions.get(urgency, "The urgency of this situation is unclear.")
    
    insurance_text = f"Based on your {insurance} insurance" if insurance != "Unknown" else "Without insurance information"
    
    treatment_options = {
        'emergency': ["Emergency Room"],
        'urgent': ["Urgent Care Center", "Emergency Room"],
        'routine': ["Primary Care Physician", "Urgent Care Center"]
    }
    
    treatment_text = ", ".join(treatment_options.get(urgency, ["healthcare provider"]))
    
    analysis = f"Based on your reported symptoms ({symptom_text}), {urgency_text} {insurance_text}, I recommend seeking treatment at a {treatment_text}."
    
    return analysis

# Function to analyze if symptoms can be treated and covered by insurance
def analyze_treatment_and_coverage(symptoms, urgency_level, insurance_provider):
    # This would typically involve a more sophisticated analysis
    # For now, return placeholder data
    
    # Determine if treatment is available based on symptoms and urgency
    treatment_available = True
    treatment_message = "Your symptoms can be treated at the recommended facilities."
    
    # Check if insurance covers the treatment
    insurance_covers = False
    coverage_message = "Your insurance may not cover this treatment. Please verify with your provider."
    
    # Simple logic for demonstration purposes
    if insurance_provider and insurance_provider.lower() in ['blue cross blue shield', 'aetna', 'medicare', 'blue cross', 'bluecross']:
        insurance_covers = True
        coverage_message = "Your insurance covers this treatment at the recommended facilities."
    
    # If emergency, assume coverage regardless of insurance (emergency care laws)
    if urgency_level and urgency_level.lower() == 'emergency':
        insurance_covers = True
        coverage_message = "Emergency care is typically covered by all insurance plans. Your specific coverage details may vary."
    
    return {
        "treatment_available": treatment_available,
        "treatment_message": treatment_message,
        "insurance_covers": insurance_covers,
        "coverage_message": coverage_message
    }

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Get user message from request
        user_message = request.json.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get conversation history from session
        conversation_history = get_conversation_history()
        
        # Process the message using the agent manager
        print(f"Processing message with agent manager: {user_message}")
        
        # The agent manager will determine which agent to use and process the message
        response, updated_history, agent_type, facilities = agent_manager.process_message(user_message, conversation_history)
        
        # Update session with the updated conversation history
        session['conversation'] = updated_history
        
        # Log the current state for debugging
        print(f"Current agent: {agent_type}")
        print(f"Urgency level: {updated_history.get('urgency_level')}")
        print(f"Has symptom data: {bool(updated_history.get('symptom_data'))}")
        print(f"Has insurance data: {bool(updated_history.get('insurance_data') or updated_history.get('insurance_file'))}")
        print(f"Has location data: {bool(updated_history.get('location_data'))}")
        
        # Add the exchange to the conversation history if not already there
        if user_message and (not updated_history['messages'] or 
                            updated_history['messages'][-1]['role'] != 'user' or 
                            updated_history['messages'][-1]['content'] != user_message):
            updated_history['messages'].append({"role": "user", "content": user_message})
        
        # Add the assistant's response to the conversation history
        updated_history['messages'].append({"role": "assistant", "content": response})
        session['conversation'] = updated_history
        
        # If we have facilities (from facility recommendation agent) or all necessary data, include facility suggestions
        if facilities or (agent_type == 'facility_recommendation' or 
            (updated_history.get('symptom_data') and 
             (updated_history.get('insurance_data') or updated_history.get('insurance_file')) and 
             updated_history.get('location_data'))):
            
            # If we don't have facilities yet but have all the necessary data, search for them
            if not facilities:
                # Get relevant data for facility search
                location = updated_history.get('location_data', {})
                urgency_level = updated_history.get('urgency_level')
                insurance_provider = updated_history.get('insurance_data', {}).get('provider')
                
                # Use the facility recommendation agent to search for facilities
                facility_agent = agent_manager.agents['facility_recommendation']
                _, _, facilities = facility_agent._search_nearby_facilities(updated_history)
            
            # Analyze if symptoms can be treated and covered by insurance
            symptoms = updated_history.get('symptom_data', {})
            urgency_level = updated_history.get('urgency_level')
            insurance_provider = updated_history.get('insurance_data', {}).get('provider')
            analysis = analyze_treatment_and_coverage(symptoms, urgency_level, insurance_provider)
            
            # Store analysis results in conversation history
            updated_history['treatment_available'] = analysis['treatment_available']
            updated_history['insurance_covers'] = analysis['insurance_covers']
            session['conversation'] = updated_history
            
            # Add a message about the analysis to the assistant's response
            analysis_message = f"\n\nBased on your symptoms and information, I've analyzed your situation:\n"
            analysis_message += f"- {analysis['treatment_message']}\n"
            analysis_message += f"- {analysis['coverage_message']}\n"
            
            if facilities:
                analysis_message += f"\nHere are some recommended facilities that can help you."
            
            # Combine the original message with the analysis message
            combined_message = response + analysis_message
            
            return jsonify({
                'reply': combined_message,
                'facilities': facilities,
                'analysis': analysis
            })
        
        return jsonify({
            'reply': response
        })
    
    except Exception as e:
        print(f"Error in /api/chat: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Route to reset the conversation
@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    if 'conversation' in session:
        session.pop('conversation')
    return jsonify({'status': 'success', 'message': 'Conversation reset successfully'})

# Route to get insurance information (placeholder for actual database/API integration)
@app.route('/api/insurance_info', methods=['GET'])
def get_insurance_info():
    insurance_provider = request.args.get('provider', '')
    
    # This would typically query a database or external API
    # For now, return placeholder data
    insurance_data = {
        "blue_cross": {
            "name": "Blue Cross Blue Shield",
            "coverage": ["Emergency Room", "Urgent Care", "Primary Care"],
            "network_restrictions": "In-network providers only for non-emergency care"
        },
        "aetna": {
            "name": "Aetna",
            "coverage": ["Emergency Room", "Urgent Care", "Primary Care", "Telehealth"],
            "network_restrictions": "Preferred rates with in-network providers"
        },
        "medicare": {
            "name": "Medicare",
            "coverage": ["Emergency Room", "Hospital Care", "Primary Care"],
            "network_restrictions": "Must accept Medicare assignment"
        }
    }
    
    if insurance_provider.lower() in insurance_data:
        return jsonify(insurance_data[insurance_provider.lower()])
    else:
        return jsonify({
            "name": "Unknown Provider",
            "message": "Please provide more details about your insurance for accurate information."
        })

# Route to handle location data
@app.route('/api/location', methods=['POST'])
def update_location():
    print("Location API endpoint called")
    try:
        data = request.json
        print(f"Received location data: {data}")
        
        if not data or 'latitude' not in data or 'longitude' not in data:
            print("Error: Invalid location data received")
            return jsonify({'error': 'Invalid location data'}), 400
        
        # Initialize conversation history if it doesn't exist
        conversation_history = session.get('conversation', {})
        if not conversation_history:
            conversation_history = {
                'messages': [],
                'symptom_data': {},
                'insurance_data': {},
                'location_data': {}
            }
        
        # Store location data in session
        location_data = {
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'detected': True
        }
        
        # Update the conversation history with location data
        conversation_history['location_data'] = location_data
        
        # Add a message about the location being shared
        location_message = f"I've shared my location: {data['latitude']}, {data['longitude']}"
        conversation_history['messages'].append({
            'role': 'user',
            'content': location_message
        })
        
        # Save updated conversation history to session
        session['conversation'] = conversation_history
        print(f"Location data stored in session: {location_data}")
        
        return jsonify({
            'status': 'success', 
            'message': 'Location updated successfully',
            'latitude': data['latitude'],
            'longitude': data['longitude']
        }), 200
    except Exception as e:
        print(f"Error in update_location: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Route to handle insurance file upload
@app.route('/api/upload_insurance', methods=['POST'])
def upload_insurance():
    print("Insurance upload endpoint called")
    print("Request files:", request.files)
    
    try:
        if 'file' not in request.files:
            print("Error: No file part in the request")
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        print(f"Received file: {file.filename}, type: {file.content_type}")
        
        if file.filename == '':
            print("Error: Empty filename")
            return jsonify({'error': 'No selected file'}), 400
            
        if file and allowed_file(file.filename):
            # Generate a secure filename with timestamp to avoid collisions
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_filename = f"{timestamp}_{uuid.uuid4().hex}_{filename}"
            print(f"Secured filename: {unique_filename}")
            
            # Save the file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            print(f"File saved to: {file_path}")
            
            # Update conversation history with insurance file info
            conversation_history = get_conversation_history()
            conversation_history['insurance_file'] = {
                'filename': filename,  # Original filename for display
                'path': file_path,     # Server path for processing
                'uploaded_at': timestamp
            }
            
            # In a real application, you might extract insurance details from the file
            # For now, just acknowledge the upload
            conversation_history['insurance_data'] = conversation_history.get('insurance_data', {})
            conversation_history['insurance_data']['file_uploaded'] = True
            session['conversation'] = conversation_history
            print(f"Insurance file stored in session: {filename}")
            
            return jsonify({
                'status': 'success',
                'message': 'Insurance file uploaded successfully',
                'filename': filename
            })
        
        print(f"Error: File type not allowed for {file.filename}")
        return jsonify({'error': 'File type not allowed'}), 400
    
    except Exception as e:
        print(f"Error in upload_insurance: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Route to get treatment and coverage analysis
@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    try:
        conversation_history = get_conversation_history()
        
        # Check if we have the necessary data
        if not conversation_history.get('symptom_data'):
            return jsonify({'error': 'No symptom data available'}), 400
            
        # Get relevant data
        symptoms = conversation_history.get('symptom_data', {})
        urgency_level = conversation_history.get('urgency_level')
        insurance_provider = conversation_history.get('insurance_data', {}).get('provider')
        
        # Perform analysis
        analysis = analyze_treatment_and_coverage(symptoms, urgency_level, insurance_provider)
        
        # Store analysis results in conversation history
        conversation_history['treatment_available'] = analysis['treatment_available']
        conversation_history['insurance_covers'] = analysis['insurance_covers']
        session['conversation'] = conversation_history
        
        return jsonify(analysis)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render gives a PORT variable
    app.run(host='0.0.0.0', port=port)
