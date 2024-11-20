async function sendMessage() {
    const inputField = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    const typingIndicator = document.getElementById("typing-indicator");
    const userMessage = inputField.value.trim();

    if (userMessage === "") return;

    // Display the user's message
    chatBox.innerHTML += `<div class="message user"><div class="message-content">${userMessage}</div></div>`;
    inputField.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;

    // Show typing indicator
    typingIndicator.style.display = "block";

    try {
        // Send the message to the backend
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: userMessage, context: chatBox.innerText })
        });
        
        const data = await response.json();

        // Hide typing indicator
        typingIndicator.style.display = "none";

        // Display the bot's response
        chatBox.innerHTML += `<div class="message bot"><div class="message-content">${data.response}</div></div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
        console.error('Error:', error);
        typingIndicator.style.display = "none";
        chatBox.innerHTML += `<div class="message bot"><div class="message-content">Sorry, something went wrong.</div></div>`;
    }
}
