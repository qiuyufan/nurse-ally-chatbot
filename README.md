# Nurse Ally - Healthcare Navigation Assistant

Nurse Ally is an advanced healthcare navigation chatbot built with Flask and the OpenAI API. It uses a multi-agent system to help users assess symptom urgency, understand insurance coverage, and find appropriate healthcare facilities.

## Features

- **Multi-Agent System**: Specialized agents for symptom assessment, insurance verification, and facility recommendations
- **Conversation Management**: Maintains context across the conversation
- **Facility Recommendations**: Displays healthcare facility options with Google Maps integration
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Medical Disclaimer**: Clear indication that this is for navigation assistance only, not medical advice

## Prerequisites

- Python 3.7 or higher
- OpenAI API key

## Installation

1. Clone this repository or download the files

2. Navigate to the project directory

```bash
cd "AI nurse"
```

3. Install the required dependencies

```bash
pip install -r requirements.txt
```

4. Set up your environment variables

Edit the `.env` file and replace the placeholder values with your actual API keys:

```
# Required
OPENAI_API_KEY=your_api_key_here

# Optional but recommended for production
SECRET_KEY=your-secure-secret-key

# Optional for Google Maps integration
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

## Usage

1. Start the Flask application

```bash
python app.py
```

2. Open your web browser and go to `http://127.0.0.1:5000`

3. Start chatting with the AI nurse assistant!

## Project Structure

```
.
├── app.py              # Main Flask application with multi-agent system
├── .env                # Environment variables
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── static/             # Static files
│   ├── css/
│   │   └── style.css   # CSS styles
│   └── js/
│       └── script.js   # JavaScript for the chat interface
└── templates/
    └── index.html      # HTML template for the chat interface
```

## How It Works

Nurse Ally uses a multi-agent system to provide comprehensive healthcare navigation assistance:

1. **Coordinator Agent**: Manages the conversation flow and determines which specialized agent to call
2. **Symptom Assessment Agent**: Asks about symptoms and assesses urgency (Emergency, Urgent, or Routine)
3. **Insurance Verification Agent**: Helps users understand their insurance coverage options
4. **Facility Recommendation Agent**: Suggests appropriate healthcare facilities based on location, urgency, and insurance

The system maintains conversation context in Flask sessions, allowing for a coherent user experience across multiple exchanges.

## Customization

- **Agent Prompts**: Modify the system prompts in the `SYSTEM_PROMPTS` dictionary in `app.py`
- **Agent Logic**: Adjust the agent switching logic in the `determine_next_agent()` function
- **Facility Search**: Implement actual Google Maps API integration in the `search_nearby_facilities()` function
- **Insurance Database**: Expand the insurance information in the `get_insurance_info()` route
- **UI/UX**: Customize the appearance in `static/css/style.css` and behavior in `static/js/script.js`

## Future Enhancements

- **Real Google Maps Integration**: Replace the placeholder facility data with actual Google Maps API calls
- **Insurance Database**: Build a comprehensive database of insurance providers and their coverage details
- **User Accounts**: Allow users to save their insurance information and location for future sessions
- **Symptom Database**: Improve symptom assessment with a structured database of symptoms and urgency levels
- **Mobile App**: Develop a native mobile application for improved user experience

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgements

- [OpenAI](https://openai.com/) for providing the GPT API
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Font Awesome](https://fontawesome.com/) for the icons

## Disclaimer

Nurse Ally is designed to provide healthcare navigation assistance only, not medical advice. For medical emergencies, users should call emergency services (911 in the US) immediately. Always consult with qualified healthcare professionals for medical advice.