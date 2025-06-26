document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const resetButton = document.getElementById('reset-button');
    const detectLocationButton = document.getElementById('detect-location');
    const locationStatus = document.getElementById('location-status');
    const insuranceUpload = document.getElementById('insurance-upload');
    const insuranceStatus = document.getElementById('insurance-status');
    const editProfileBtn = document.getElementById('edit-profile-btn');
    const profileModal = document.getElementById('profile-modal');
    const closeProfileModal = document.getElementById('close-profile-modal');
    const profileForm = document.getElementById('profile-form');
    const mapModal = document.getElementById('map-modal');
    const closeMapModal = document.getElementById('close-map-modal');
    const mapIframe = document.getElementById('map-iframe');
    
    // User profile data
    let userProfile = {
        nationality: '',
        insurance_type: 'None',
        insurance_provider: '',
        country: '',
        city: '',
        language: 'English',
        chronic_conditions: '',
        allergies: ''
    };
    
    // Load user profile from localStorage if available
    loadUserProfile();
    
    // Event Listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    resetButton.addEventListener('click', resetConversation);
    detectLocationButton.addEventListener('click', detectLocation);
    insuranceUpload.addEventListener('change', uploadInsuranceFile);
    editProfileBtn.addEventListener('click', openProfileModal);
    closeProfileModal.addEventListener('click', closeModal);
    profileForm.addEventListener('submit', saveUserProfile);
    closeMapModal.addEventListener('click', closeModal);
    
    // Close modals when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === profileModal) {
            closeModal();
        }
        if (event.target === mapModal) {
            closeModal();
        }
    });
    
    // Functions
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;
        
        // Add user message to chat
        addMessage(message, 'user');
        userInput.value = '';
        
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'message bot typing';
        typingIndicator.innerHTML = '<div class="message-content"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>';
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Send message to backend
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                user_profile: userProfile
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            chatMessages.removeChild(typingIndicator);
            
            // Add bot response to chat
            addMessage(data.response, 'bot');
            
            // If map link is provided, show map button
            if (data.map_link) {
                showMapLink(data.map_link);
            }
            
            // If checklist is provided, display it
            if (data.checklist && data.checklist.length > 0) {
                displayChecklist(data.checklist);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            chatMessages.removeChild(typingIndicator);
            addMessage('Sorry, there was an error processing your request. Please try again.', 'bot');
        });
    }
    
    function addMessage(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Convert markdown-like syntax to HTML
        let formattedMessage = message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
        
        // Convert bullet points
        if (formattedMessage.includes('- ')) {
            const lines = formattedMessage.split('<br>');
            let inList = false;
            
            formattedMessage = lines.map(line => {
                if (line.trim().startsWith('- ')) {
                    if (!inList) {
                        inList = true;
                        return '<ul><li>' + line.trim().substring(2) + '</li>';
                    }
                    return '<li>' + line.trim().substring(2) + '</li>';
                } else {
                    if (inList) {
                        inList = false;
                        return '</ul>' + line;
                    }
                    return line;
                }
            }).join('');
            
            if (inList) {
                formattedMessage += '</ul>';
            }
        }
        
        messageContent.innerHTML = formattedMessage;
        messageElement.appendChild(messageContent);
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function resetConversation() {
        // Clear chat messages except the first welcome message
        while (chatMessages.children.length > 1) {
            chatMessages.removeChild(chatMessages.lastChild);
        }
        
        // Reset conversation on the server
        fetch('/api/reset', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Conversation reset:', data);
        })
        .catch(error => {
            console.error('Error resetting conversation:', error);
        });
    }
    
    function detectLocation() {
        if (navigator.geolocation) {
            detectLocationButton.disabled = true;
            locationStatus.textContent = 'Detecting location...';
            
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    
                    // Reverse geocode to get city and country
                    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`)
                    .then(response => response.json())
                    .then(data => {
                        const city = data.address.city || data.address.town || data.address.village || '';
                        const country = data.address.country || '';
                        
                        // Update user profile
                        userProfile.city = city;
                        userProfile.country = country;
                        saveUserProfileToLocalStorage();
                        
                        // Update location status
                        locationStatus.textContent = `${city}, ${country}`;
                        
                        // Send location to server
                        fetch('/api/location', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                latitude: latitude,
                                longitude: longitude,
                                city: city,
                                country: country
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            console.log('Location updated:', data);
                        })
                        .catch(error => {
                            console.error('Error updating location:', error);
                        });
                    })
                    .catch(error => {
                        console.error('Error geocoding:', error);
                        locationStatus.textContent = 'Location detection failed';
                    })
                    .finally(() => {
                        detectLocationButton.disabled = false;
                    });
                },
                function(error) {
                    console.error('Geolocation error:', error);
                    locationStatus.textContent = 'Location access denied';
                    detectLocationButton.disabled = false;
                }
            );
        } else {
            locationStatus.textContent = 'Geolocation not supported';
        }
    }
    
    function uploadInsuranceFile() {
        const file = insuranceUpload.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        insuranceStatus.textContent = 'Uploading...';
        
        fetch('/api/upload_insurance', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            insuranceStatus.textContent = 'File uploaded: ' + file.name;
            console.log('Insurance file uploaded:', data);
        })
        .catch(error => {
            console.error('Error uploading insurance file:', error);
            insuranceStatus.textContent = 'Upload failed';
        });
    }
    
    function openProfileModal() {
        // Populate form with current profile data
        document.getElementById('nationality').value = userProfile.nationality;
        document.getElementById('insurance-type').value = userProfile.insurance_type;
        document.getElementById('insurance-provider').value = userProfile.insurance_provider;
        document.getElementById('country').value = userProfile.country;
        document.getElementById('city').value = userProfile.city;
        document.getElementById('language').value = userProfile.language;
        document.getElementById('chronic-conditions').value = userProfile.chronic_conditions;
        document.getElementById('allergies').value = userProfile.allergies;
        
        // Show modal
        profileModal.style.display = 'block';
    }
    
    function closeModal() {
        profileModal.style.display = 'none';
        mapModal.style.display = 'none';
    }
    
    function saveUserProfile(event) {
        event.preventDefault();
        
        // Update user profile from form
        userProfile.nationality = document.getElementById('nationality').value;
        userProfile.insurance_type = document.getElementById('insurance-type').value;
        userProfile.insurance_provider = document.getElementById('insurance-provider').value;
        userProfile.country = document.getElementById('country').value;
        userProfile.city = document.getElementById('city').value;
        userProfile.language = document.getElementById('language').value;
        userProfile.chronic_conditions = document.getElementById('chronic-conditions').value;
        userProfile.allergies = document.getElementById('allergies').value;
        
        // Save to localStorage
        saveUserProfileToLocalStorage();
        
        // Send to server
        fetch('/api/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userProfile)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Profile updated:', data);
            // Close modal
            closeModal();
            // Add confirmation message to chat
            addMessage('Your profile has been updated. I now have your latest information to provide better assistance.', 'bot');
        })
        .catch(error => {
            console.error('Error updating profile:', error);
        });
    }
    
    function loadUserProfile() {
        const savedProfile = localStorage.getItem('nurseAllyUserProfile');
        if (savedProfile) {
            userProfile = JSON.parse(savedProfile);
            
            // Update location status if city and country are available
            if (userProfile.city && userProfile.country) {
                locationStatus.textContent = `${userProfile.city}, ${userProfile.country}`;
            }
        }
    }
    
    function saveUserProfileToLocalStorage() {
        localStorage.setItem('nurseAllyUserProfile', JSON.stringify(userProfile));
    }
    
    function showMapLink(mapUrl) {
        // Create a button to open the map
        const mapButton = document.createElement('button');
        mapButton.className = 'map-button';
        mapButton.innerHTML = '<i class="fas fa-map-marked-alt"></i> View Healthcare Facilities';
        mapButton.addEventListener('click', function() {
            openMapModal(mapUrl);
        });
        
        // Add to chat as a bot message
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot';
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.appendChild(mapButton);
        messageElement.appendChild(messageContent);
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function openMapModal(mapUrl) {
        mapIframe.src = mapUrl;
        mapModal.style.display = 'block';
    }
    
    function displayChecklist(checklist) {
        let checklistHtml = '<strong>Insurance Claim Checklist:</strong><ul>';
        checklist.forEach(item => {
            checklistHtml += `<li>${item}</li>`;
        });
        checklistHtml += '</ul>';
        
        addMessage(checklistHtml, 'bot');
    }
});