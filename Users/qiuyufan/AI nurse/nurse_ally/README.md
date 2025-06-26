# Nurse Ally - Healthcare Navigation Assistant

Nurse Ally is an AI-powered healthcare navigation assistant designed to help travelers, students abroad, and digital nomads access appropriate healthcare services based on their symptoms, location, and insurance coverage.

## Features

- **Symptom Assessment**: Evaluates user symptoms and determines urgency level
- **Insurance Coverage Check**: Provides information about likely insurance coverage based on user's insurance type
- **Healthcare Facility Recommendations**: Suggests nearby healthcare facilities based on user's location and care needs
- **Insurance Claim Guidance**: Provides checklists of documents needed for insurance claims
- **User Profile Management**: Stores user information including nationality, insurance details, and location

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- OpenAI API key

### Installation

1. Clone this repository or download the source code

2. Navigate to the project directory:
   ```
   cd nurse_ally
   ```

3. Create a virtual environment:
   ```
   python -m venv venv
   ```

4. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

5. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

6. Create a `.env` file in the project root directory with the following content:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_secret_key_here
   PORT=5000
   ```

### Running the Application

1. Start the Flask server:
   ```
   python app.py
   ```

2. Open a web browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

1. **Edit Profile**: Click the "Edit Profile" button to enter your nationality, insurance information, and other details

2. **Detect Location**: Click the "Detect Location" button to allow the application to determine your current location

3. **Upload Insurance**: Upload an image or PDF of your insurance card/policy for reference

4. **Chat Interface**: Describe your symptoms or healthcare needs in the chat interface

5. **View Recommendations**: Receive care recommendations, insurance coverage information, and nearby facility suggestions

## Project Structure

- `app.py`: Main Flask application
- `agent.py`: NurseAlly agent implementation with healthcare navigation tools
- `templates/`: HTML templates
- `static/`: CSS and JavaScript files
- `uploads/`: Directory for uploaded insurance files
- `flask_session/`: Directory for server-side session data

## Tools Implementation

Nurse Ally implements four specialized tools:

1. **Triage Symptoms**: Analyzes symptom descriptions to determine urgency level (mild, moderate, severe)

2. **Check Insurance Coverage**: Evaluates if the user's insurance likely covers their needed care

3. **Map Search**: Generates Google Maps links to find nearby healthcare facilities

4. **Get Claim Checklist**: Provides a customized list of documents needed for insurance claims

## Safety Features

- Emergency detection for symptoms requiring immediate medical attention
- Clear disclaimers about not providing medical diagnoses
- Emphasis on guiding users to appropriate care rather than diagnosing conditions

## License

This project is licensed under the MIT License - see the LICENSE file for details.