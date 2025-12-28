let sessionId = localStorage.getItem('chatSessionId');

// Initialize session ID if not present
if (!sessionId) {
    sessionId = 'session_' + Date.now() + Math.random().toString(36).substring(2, 9);
    localStorage.setItem('chatSessionId', sessionId);
}

document.getElementById('session-id').textContent = sessionId;

function displayMessage(content, sender) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'assistant-message');
    messageDiv.textContent = content;
    chatBox.appendChild(messageDiv);
    // Scroll to the bottom
    chatBox.scrollTop = chatBox.scrollHeight;
}

function updateStatus(topic, status) {
    document.getElementById('last-topic').textContent = topic;
    document.getElementById('last-status').textContent = status;
}

async function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();

    if (message === "") return;

    // 1. Display User Message
    displayMessage(message, 'user');
    userInput.value = ''; // Clear input

    try {
        const response = await fetch('/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Assuming CSRF token is not strictly necessary for this simple API but add if needed:
                // 'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        const data = await response.json();

        if (response.ok) {
            updateStatus(data.topic, data.status);

            // 2. Display Assistant Response ONLY if status is NOT 'no_response'
            if (data.status !== 'no_response' && data.response) {
                displayMessage(data.response, 'assistant');
            } else if (data.status === 'no_response') {
                // Log the action without showing a message
                console.log("Rule 3v met: Generic acknowledgement, no response sent.");
                // Optionally display a system message for the user's debugging/testing
                const chatBox = document.getElementById('chat-box');
                const systemNote = document.createElement('i');
                systemNote.textContent = "[SYSTEM: No response sent due to OTHERS/acknowledgement rule.]";
                systemNote.style.display = 'block';
                systemNote.style.textAlign = 'center';
                systemNote.style.fontSize = '0.8em';
                systemNote.style.color = '#999';
                chatBox.appendChild(systemNote);
                chatBox.scrollTop = chatBox.scrollHeight;
            }


        } else {
            // Handle server-side errors
            updateStatus('ERROR', 'System Error');
            displayMessage(`[ERROR] Server responded: ${data.error || data.message}`, 'assistant');
        }

    } catch (error) {
        console.error('Fetch error:', error);
        updateStatus('ERROR', 'Network Error');
        displayMessage('An error occurred while connecting to the server.', 'assistant');
    }
}

// Allow sending message with Enter key
document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
