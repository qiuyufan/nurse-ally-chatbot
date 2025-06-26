import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, session
from agent import NurseAlly

# Load environment variables from .env file
load_dotenv()

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

# Initialize the NurseAlly agent
nurse_ally = NurseAlly()

# Helper function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize or get conversation context from session
def get_conversation_context():
    if 'conversation_context' not in session:
        session['conversation_context'] = {
            'conversation_history': [],
            'symptoms_assessed': False,
            'insurance_checked': False,
            'facilities_recommended': False,
            'urgency_level': None,
            'symptoms': None,
            'insurance_covers': None,
            'coverage_note': None,
            'map_link': None,
            'user_profile': {
                'nationality': 'Unknown',
                'insurance_type': 'Unknown',
                'insurance_provider': 'Unknown',
                'country': 'Unknown',
                'city': 'Unknown',
                'language': 'English',
                'chronic_conditions': [],
                'allergies': []
            }
        }
    return session['conversation_context']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Get user message from request
        user_message = request.json.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get conversation context from session
        context = get_conversation_context()
        
        # Process the message using the NurseAlly agent
        response, updated_context = nurse_ally.process(user_message, context)
        
        # Update session with the updated context
        session['conversation_context'] = updated_context
        
        # Add the exchange to the conversation history
        if user_message and (not updated_context['conversation_history'] or 
                            updated_context['conversation_history'][-1]['role'] != 'user' or 
                            updated_context['conversation_history'][-1]['content'] != user_message):
            updated_context['conversation_history'].append({"role": "user", "content": user_message})
        
        # Add the assistant's response to the conversation history
        updated_context['conversation_history'].append({"role": "assistant", "content": response})
        session['conversation_context'] = updated_context
        
        # Prepare the response data
        response_data = {
            'reply': response
        }
        
        # Add map link if available
        if updated_context.get('map_link'):
            response_data['map_link'] = updated_context['map_link']
        
        # Add insurance coverage information if available
        if updated_context.get('insurance_covers') is not None:
            response_data['insurance_coverage'] = {
                'covered': updated_context['insurance_covers'],
                'note': updated_context.get('coverage_note', '')
            }
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"Error in /api/chat: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    if 'conversation_context' in session:
        session.pop('conversation_context')
    return jsonify({'status': 'success', 'message': 'Conversation reset successfully'})

@app.route('/api/location', methods=['POST'])
def update_location():
    try:
        data = request.json
        
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({'error': 'Invalid location data'}), 400
        
        # Get conversation context
        context = get_conversation_context()
        
        # Update user profile with location data
        context['user_profile']['location'] = {
            'latitude': data['latitude'],
            'longitude': data['longitude']
        }
        
        # If city is provided, update it
        if 'city' in data:
            context['user_profile']['city'] = data['city']
        
        # If country is provided, update it
        if 'country' in data:
            context['user_profile']['country'] = data['country']
        
        # Save updated context to session
        session['conversation_context'] = context
        
        return jsonify({
            'status': 'success', 
            'message': 'Location updated successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload_insurance', methods=['POST'])
def upload_insurance():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file and allowed_file(file.filename):
            # Generate a secure filename with timestamp to avoid collisions
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_filename = f"{timestamp}_{uuid.uuid4().hex}_{filename}"
            
            # Save the file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Update conversation context with insurance file info
            context = get_conversation_context()
            context['insurance_file'] = {
                'filename': filename,  # Original filename for display
                'path': file_path,     # Server path for processing
                'uploaded_at': timestamp
            }
            
            # Update user profile with insurance information
            # In a real application, you might extract insurance details from the file
            context['user_profile']['has_insurance_file'] = True
            
            # Save updated context to session
            session['conversation_context'] = context
            
            return jsonify({
                'status': 'success',
                'message': 'Insurance file uploaded successfully',
                'filename': filename
            })
        
        return jsonify({'error': 'File type not allowed'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['POST'])
def update_profile():
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No profile data provided'}), 400
        
        # Get conversation context
        context = get_conversation_context()
        
        # Update user profile with provided data
        for key in data:
            if key in context['user_profile']:
                context['user_profile'][key] = data[key]
        
        # Save updated context to session
        session['conversation_context'] = context
        
        return jsonify({
            'status': 'success', 
            'message': 'Profile updated successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)