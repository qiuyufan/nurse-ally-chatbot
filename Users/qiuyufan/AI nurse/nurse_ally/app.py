import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, url_for
from flask_session import Session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from agent import NurseAlly

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'nurse-ally-secret-key')

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
Session(app)

# Configure file uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize NurseAlly agent
nurse_ally = NurseAlly(api_key=os.getenv('OPENAI_API_KEY'))

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    # Initialize session variables if they don't exist
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    if 'user_profile' not in session:
        session['user_profile'] = {
            'nationality': '',
            'insurance_type': 'None',
            'insurance_provider': '',
            'country': '',
            'city': '',
            'language': 'English',
            'chronic_conditions': '',
            'allergies': ''
        }
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    user_profile = data.get('user_profile', {})
    
    # Update user profile in session
    if user_profile:
        session['user_profile'] = user_profile
    
    # Add user message to conversation history
    conversation_history = session.get('conversation_history', [])
    conversation_history.append({
        'role': 'user',
        'content': message,
        'timestamp': datetime.now().isoformat()
    })
    
    # Process message with NurseAlly agent
    response = nurse_ally.process(message, conversation_history, session['user_profile'])
    
    # Add bot response to conversation history
    conversation_history.append({
        'role': 'assistant',
        'content': response['response'],
        'timestamp': datetime.now().isoformat()
    })
    
    # Update conversation history in session
    session['conversation_history'] = conversation_history
    
    # Update conversation state in session
    session['conversation_state'] = response.get('conversation_state', {})
    
    # Prepare response data
    response_data = {
        'response': response['response']
    }
    
    # Add map link if available
    if 'map_link' in response:
        response_data['map_link'] = response['map_link']
    
    # Add checklist if available
    if 'checklist' in response:
        response_data['checklist'] = response['checklist']
    
    return jsonify(response_data)

@app.route('/api/reset', methods=['POST'])
def reset():
    # Clear conversation history
    session['conversation_history'] = []
    
    # Reset NurseAlly agent
    nurse_ally.reset()
    
    # Clear conversation state
    session['conversation_state'] = {}
    
    return jsonify({'status': 'success', 'message': 'Conversation reset'})

@app.route('/api/location', methods=['POST'])
def update_location():
    data = request.json
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    city = data.get('city')
    country = data.get('country')
    
    # Update user profile with location data
    user_profile = session.get('user_profile', {})
    user_profile['city'] = city
    user_profile['country'] = country
    session['user_profile'] = user_profile
    
    # Store location data in session
    session['location'] = {
        'latitude': latitude,
        'longitude': longitude,
        'city': city,
        'country': country
    }
    
    return jsonify({'status': 'success', 'message': 'Location updated'})

@app.route('/api/upload_insurance', methods=['POST'])
def upload_insurance():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'})
    
    if file and allowed_file(file.filename):
        # Generate a secure filename with a unique ID
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the file
        file.save(file_path)
        
        # Store file info in session
        session['insurance_file'] = {
            'original_filename': filename,
            'stored_filename': unique_filename,
            'file_path': file_path,
            'upload_time': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'message': 'File uploaded successfully',
            'filename': filename
        })
    
    return jsonify({'status': 'error', 'message': 'File type not allowed'})

@app.route('/api/profile', methods=['POST'])
def update_profile():
    data = request.json
    
    # Update user profile in session
    session['user_profile'] = data
    
    return jsonify({'status': 'success', 'message': 'Profile updated'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))