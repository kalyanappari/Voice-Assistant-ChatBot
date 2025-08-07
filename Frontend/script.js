let isRecording = false;
let mediaRecorder;
let audioChunks = [];

// DOM elements
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");

// Event listeners
sendBtn.addEventListener("click", handleSendMessage);
userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        handleSendMessage();
    }
});
micBtn.addEventListener("click", handleMicButton);

function handleSendMessage() {
    const userMessage = userInput.value.trim();
    if (!userMessage) return;
    
    appendMessage("You", userMessage);
    userInput.value = "";
    sendBtn.disabled = true;
    sendBtn.textContent = "Sending...";
    
    fetchTextResponse(userMessage);
}

function handleMicButton() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log("Microphone access granted");

        // Use WebM since WAV is not supported
        const mimeType = 'audio/webm';
        mediaRecorder = new MediaRecorder(stream, { mimeType });
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: mimeType });
            sendVoiceMessage(audioBlob, "recording.webm");
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;
        micBtn.textContent = "🔴 Stop";
        micBtn.style.backgroundColor = "#dc3545";

    } catch (error) {
        console.error("Microphone error:", error);
        appendMessage("System", `Microphone error: ${error.message}`);
    }
}



function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        micBtn.textContent = "🎤";
        micBtn.style.backgroundColor = "#007bff";
    }
}

function appendMessage(sender, message) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "message";
    messageDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function fetchTextResponse(message) {
    fetch("/process-text", {
        method: "POST",
        headers: { 
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            appendMessage("System", `Error: ${data.error}`);
        } else {
            appendMessage("Assistant", data.responseText);
            
            // Play audio response if available
            if (data.responseAudio) {
                playAudio(data.responseAudio);
            }
        }
    })
    .catch(error => {
        console.error("Error:", error);
        appendMessage("System", "Error: Failed to get response from server.");
    })
    .finally(() => {
        sendBtn.disabled = false;
        sendBtn.textContent = "Send";
    });
}

function sendVoiceMessage(audioBlob, fileName) {
    const formData = new FormData();
    formData.append("audio", audioBlob, fileName);

    appendMessage("System", "Processing voice message...");

    fetch("/process-voice", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            appendMessage("System", `Error: ${data.error}`);
        } else {
            appendMessage("You", data.userText);
            appendMessage("Assistant", data.responseText);

            if (data.responseAudio) {
                playAudio(data.responseAudio);
            }
        }
    })
    .catch(error => {
        console.error("Error:", error);
        appendMessage("System", "Error: Failed to process voice message.");
    });
}

function playAudio(base64Audio) {
    try {
        if (base64Audio) {
            const audio = new Audio("data:audio/wav;base64," + base64Audio);
            audio.play().catch(error => {
                console.error("Error playing audio:", error);
                appendMessage("System", "Note: Could not play audio response.");
            });
        }
    } catch (error) {
        console.error("Error creating audio:", error);
    }
}

// Clear chat function (optional)
function clearChat() {
    chatBox.innerHTML = "";
}

// Initialize
appendMessage("System", "Voice Assistant ready! You can type or click the microphone to speak.");