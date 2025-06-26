document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements initialization with error handling
    function getElement(id, fallbackSelector = null) {
        const element = document.getElementById(id);
        if (!element && fallbackSelector) {
            console.warn(`Element with ID '${id}' not found, trying fallback selector`);
            return document.querySelector(fallbackSelector);
        }
        if (!element) {
            console.error(`Element with ID '${id}' not found in the DOM`);
        }
        return element;
    }

    // Initialize all DOM elements
    const chatMessages = getElement('chat-messages');
    const userInput = getElement('user-input');
    const sendButton = getElement('send-button');
    const detectLocationBtn = getElement('detect-location');
    const locationStatus = getElement('location-status');
    const insuranceUpload = getElement('insurance-upload');
    const insuranceLabel = document.querySelector('.upload-label');
    const insuranceStatus = getElement('insurance-status');
    const coverageModal = getElement('coverage-modal');
    const closeModalBtn = getElement('close-modal');
    
    // Log all critical elements to verify they're found
    console.log('DOM Elements loaded:');
    console.log('- chatMessages:', chatMessages);
    console.log('- userInput:', userInput);
    console.log('- sendButton:', sendButton);
    console.log('- detectLocationBtn:', detectLocationBtn);
    console.log('- locationStatus:', locationStatus);
    console.log('- insuranceUpload:', insuranceUpload);
    console.log('- insuranceLabel:', insuranceLabel);
    console.log('- insuranceStatus:', insuranceStatus);
    console.log('- coverageModal:', coverageModal);
    console.log('- closeModalBtn:', closeModalBtn);

    // Function to add a message to the chat
    function addMessage(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Check if the message is a string or HTML content
        if (typeof message === 'string') {
            // Process message text to add line breaks
            const formattedMessage = message.replace(/\n/g, '<br>');
            messageContent.innerHTML = formattedMessage;
        } else {
            messageContent.appendChild(message);
        }

        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);

        // Scroll to the bottom of the chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to create a facility card
    function createFacilityCard(facility) {
        const facilityCard = document.createElement('div');
        facilityCard.className = 'facility-card';
        
        const facilityName = document.createElement('h3');
        facilityName.textContent = facility.name;
        facilityCard.appendChild(facilityName);
        
        const facilityType = document.createElement('p');
        facilityType.className = 'facility-type';
        facilityType.textContent = `Type: ${facility.type}`;
        facilityCard.appendChild(facilityType);
        
        const facilityAddress = document.createElement('p');
        facilityAddress.textContent = `Address: ${facility.address}`;
        facilityCard.appendChild(facilityAddress);
        
        const facilityPhone = document.createElement('p');
        facilityPhone.textContent = `Phone: ${facility.phone}`;
        facilityCard.appendChild(facilityPhone);
        
        const facilityDistance = document.createElement('p');
        facilityDistance.textContent = `Distance: ${facility.distance}`;
        facilityCard.appendChild(facilityDistance);
        
        const facilityWaitTime = document.createElement('p');
        facilityWaitTime.textContent = `Estimated wait time: ${facility.wait_time}`;
        facilityCard.appendChild(facilityWaitTime);
        
        // Add insurance acceptance information if available
        if (facility.accepts_insurance && facility.accepts_insurance.length > 0) {
            const facilityInsurance = document.createElement('p');
            facilityInsurance.textContent = `Accepts: ${facility.accepts_insurance.join(', ')}`;
            facilityCard.appendChild(facilityInsurance);
        }
        
        // Add services information if available
        if (facility.services && facility.services.length > 0) {
            const facilityServices = document.createElement('p');
            facilityServices.textContent = `Services: ${facility.services.join(', ')}`;
            facilityCard.appendChild(facilityServices);
        }
        
        // Add rating if available
        if (facility.rating) {
            const facilityRating = document.createElement('p');
            facilityRating.textContent = `Rating: ${facility.rating}/5`;
            facilityCard.appendChild(facilityRating);
        }
        
        const mapLink = document.createElement('a');
        mapLink.href = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(facility.name + ' ' + facility.address)}`;
        mapLink.target = '_blank';
        mapLink.className = 'map-link';
        mapLink.textContent = 'View on Google Maps';
        facilityCard.appendChild(mapLink);
        
        return facilityCard;
    }
    
    // Function to display facility recommendations
    function displayFacilities(facilities, analysis) {
        const facilitiesContainer = document.createElement('div');
        facilitiesContainer.className = 'facilities-container';
        
        // If we have analysis data, display it first
        if (analysis) {
            const analysisContainer = document.createElement('div');
            analysisContainer.className = 'analysis-container';
            
            const analysisHeader = document.createElement('h3');
            analysisHeader.textContent = 'Treatment & Coverage Analysis:';
            analysisContainer.appendChild(analysisHeader);
            
            // Treatment availability
            const treatmentDiv = document.createElement('div');
            treatmentDiv.className = 'analysis-section';
            const treatmentHeader = document.createElement('h4');
            treatmentHeader.textContent = 'Treatment Availability:';
            treatmentDiv.appendChild(treatmentHeader);
            
            const treatmentMessage = document.createElement('p');
            treatmentMessage.textContent = analysis.treatment_message;
            treatmentDiv.appendChild(treatmentMessage);
            analysisContainer.appendChild(treatmentDiv);
            
            // Insurance coverage
            const coverageDiv = document.createElement('div');
            coverageDiv.className = 'analysis-section';
            const coverageHeader = document.createElement('h4');
            coverageHeader.textContent = 'Insurance Coverage:';
            coverageDiv.appendChild(coverageHeader);
            
            const coverageMessage = document.createElement('p');
            coverageMessage.textContent = analysis.coverage_message;
            coverageDiv.appendChild(coverageMessage);
            analysisContainer.appendChild(coverageDiv);
            
            facilitiesContainer.appendChild(analysisContainer);
        }
        
        const facilitiesHeader = document.createElement('h3');
        facilitiesHeader.textContent = 'Recommended Facilities:';
        facilitiesContainer.appendChild(facilitiesHeader);
        
        facilities.forEach(facility => {
            const facilityCard = createFacilityCard(facility);
            facilitiesContainer.appendChild(facilityCard);
        });
        
        addMessage(facilitiesContainer, false);
    }

    // Function to send a message to the server
    async function sendMessage(message) {
        try {
            // Display user message in the chat
            addMessage(message, true);

            // Clear input field
            userInput.value = '';

            // Show loading indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message bot';
            const loadingContent = document.createElement('div');
            loadingContent.className = 'message-content';
            loadingContent.textContent = 'Typing...';
            loadingDiv.appendChild(loadingContent);
            chatMessages.appendChild(loadingDiv);

            // Send message to server
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            // Remove loading indicator
            chatMessages.removeChild(loadingDiv);

            if (!response.ok) {
                throw new Error('Failed to get response');
            }

            const data = await response.json();
            
            // Display bot response
            addMessage(data.reply, false);
            
            // If facilities are included in the response, display them with analysis if available
            if (data.facilities && data.facilities.length > 0) {
                displayFacilities(data.facilities, data.analysis);
            }
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your request.', false);
        }
    }
    
    // Function to detect user's location
async function detectLocation() {
    console.log('Detect location function called');
    
    if (!navigator.geolocation) {
        console.error('Geolocation not supported');
        locationStatus.textContent = 'Geolocation is not supported by your browser';
        locationStatus.style.color = 'red';
        return;
    }
    
    locationStatus.textContent = 'Detecting location...';
    locationStatus.style.color = '#666';
    
    navigator.geolocation.getCurrentPosition(async (position) => {
        try {
            console.log('Position obtained:', position.coords.latitude, position.coords.longitude);
            
            const locationData = {
                coordinates: {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                },
                timestamp: new Date().toISOString()
            };
            
            console.log('Sending location data to server:', locationData);
            
            // Send location data to server
            const response = await fetch('/api/location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(locationData)
            });
            
            console.log('Location API response status:', response.status);
            
            if (!response.ok) {
                throw new Error('Failed to update location');
            }
            
            const data = await response.json();
            console.log('Location API response data:', data);
            
            locationStatus.textContent = 'Location detected';
            locationStatus.style.color = 'green';
            
            // Inform the user that their location has been detected
            addMessage('I\'ve detected your location. This will help me find healthcare facilities near you.', false);
            
        } catch (error) {
            console.error('Error updating location:', error);
            locationStatus.textContent = 'Failed to update location';
            locationStatus.style.color = 'red';
        }
    }, (error) => {
        console.error('Geolocation error:', error);
        locationStatus.textContent = 'Unable to get location';
        locationStatus.style.color = 'red';
        
        // Provide more specific error messages
        switch(error.code) {
            case error.PERMISSION_DENIED:
                addMessage('You denied the request for geolocation. Please enable location services to get nearby facility recommendations.', false);
                break;
            case error.POSITION_UNAVAILABLE:
                addMessage('Location information is unavailable. Please try again later.', false);
                break;
            case error.TIMEOUT:
                addMessage('The request to get your location timed out. Please try again.', false);
                break;
            default:
                addMessage('An unknown error occurred while trying to get your location.', false);
                break;
        }
    }, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
    });
    }
    
    // Function to handle insurance file upload
async function uploadInsuranceFile(file) {
    console.log('Upload insurance file function called with file:', file.name, file.type, file.size);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        insuranceStatus.textContent = 'Uploading...';
        insuranceStatus.style.color = '#666';
        
        console.log('Sending insurance file to server');
        
        const response = await fetch('/api/upload_insurance', {
            method: 'POST',
            body: formData
        });
        
        console.log('Insurance upload API response status:', response.status);
        
        if (!response.ok) {
            throw new Error('Failed to upload file');
        }
        
        const data = await response.json();
        console.log('Insurance upload API response data:', data);
        
        insuranceStatus.textContent = 'File uploaded: ' + data.filename;
        insuranceStatus.style.color = 'green';
        
        // Inform the user that their insurance file has been uploaded
        addMessage('I\'ve received your insurance information. This will help me find facilities that accept your insurance.', false);
        
    } catch (error) {
            console.error('Error uploading insurance file:', error);
            insuranceStatus.textContent = 'Upload failed';
            insuranceStatus.style.color = 'red';
            addMessage('There was an error uploading your insurance file. Please try again.', false);
        }
    }
    
    // Function to reset the conversation
    async function resetConversation() {
        try {
            const response = await fetch('/api/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to reset conversation');
            }
            
            // Clear chat messages except for the initial greeting
            while (chatMessages.childNodes.length > 1) {
                chatMessages.removeChild(chatMessages.lastChild);
            }
            
            // Add a new greeting message
            addMessage("Hello! I'm Nurse Ally. How can I help you today?", false);
            
        } catch (error) {
            console.error('Error resetting conversation:', error);
        }
    }
    
    // Add reset button to the UI
    const resetButton = document.createElement('button');
    resetButton.id = 'reset-button';
    resetButton.textContent = 'New Conversation';
    resetButton.addEventListener('click', resetConversation);
    
    // Add the reset button to the page
    const chatHeader = document.querySelector('.chat-header');
    chatHeader.appendChild(resetButton);

    // Event listener for send button
    sendButton.addEventListener('click', function() {
        const message = userInput.value.trim();
        if (message) {
            sendMessage(message);
        }
    });

    // Event listener for Enter key
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const message = userInput.value.trim();
            if (message) {
                sendMessage(message);
            }
        }
    });

    // Focus on input field when page loads
    userInput.focus();
    
    // Event listener for detect location button
    console.log('Setting up event listeners');
    
    if (detectLocationBtn) {
        console.log('Adding click event listener to detect location button');
        detectLocationBtn.addEventListener('click', function() {
            console.log('Detect location button clicked');
            detectLocation();
        });
    } else {
        console.error('Detect location button not found in the DOM');
    }
    
    // Event listener for insurance file upload
    if (insuranceUpload) {
        console.log('Adding change event listener to insurance upload input');
        insuranceUpload.addEventListener('change', function(e) {
            console.log('Insurance file input changed, files:', e.target.files);
            if (e.target.files.length > 0) {
                uploadInsuranceFile(e.target.files[0]);
            }
        });
    } else {
        console.error('Insurance upload input not found in the DOM');
    }
    
    // Event listener for insurance upload label (for better UX)
    if (insuranceLabel) {
        console.log('Adding click event listener to insurance label');
        insuranceLabel.addEventListener('click', function() {
            console.log('Insurance label clicked, triggering file input click');
            insuranceUpload.click();
        });
    } else {
        console.error('Insurance label not found in the DOM');
    }
    
    // Function to open the coverage modal
    window.openCoverageModal = function() {
        const modal = document.getElementById('coverage-modal');
        if (modal) {
            modal.style.display = 'block';
        }
    }
    
    // Function to close the coverage modal
    window.closeCoverageModal = function() {
        const modal = document.getElementById('coverage-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('coverage-modal');
        if (modal && event.target === modal) {
            modal.style.display = 'none';
        }
    });
});