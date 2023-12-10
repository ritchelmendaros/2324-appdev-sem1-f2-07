let slideIndex = 1;
showSlides(slideIndex);

// Next/previous controls
function plusSlides(n) {
    showSlides(slideIndex += n);
}

// Thumbnail image controls
function currentSlide(n) {
  showSlides(slideIndex = n);
}

function showSlides(n) {
    let i;
    let slides = document.getElementsByClassName("mySlides");
    let dots = document.getElementsByClassName("dot");
    
    if (n > slides.length) {
        slideIndex = 1
    }
    if (n < 1) {
        slideIndex = slides.length
    }

    for (i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }
    
//    slides[slideIndex-1].style.display = "block";
    
}

function sendMessage() {
    var topic = document.getElementById("topic-input").value;
    var num_slides = document.getElementById("num-subtopics").value;
    var objectives = document.getElementById("objectives-textarea").value;

    document.getElementById("topic-input").value = '';
    document.getElementById("num-subtopics").value = '';
    document.getElementById("objectives-textarea").value = '';


    // Send user input to the server
    fetch('/get_response', {
        method: 'POST',
        body: new URLSearchParams({ topic: topic, num_slides: num_slides,  objectives: objectives}),
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    })
    .then(response => response.text())
    .then(data => {
        // Replace newline characters with <br> tags in the response
        data = data.replace(/\n/g, '<br>');
        displayBotMessage(data);
    });
}

function displayUserMessage(message) {
    var chatContainer = document.getElementById("chat-container");
    var messageElement = document.createElement("div");
    messageElement.classList.add("message", "user-message");
    messageElement.innerHTML = `${message}        <i class="fa fa-user-circle"></i>`;
    chatContainer.appendChild(messageElement);
}

function displayBotMessage(message) {
    var chatContainer = document.getElementById("chat-container");
    var messageElement = document.createElement("div");
    messageElement.classList.add("message", "bot-message");
    messageElement.innerHTML = `<i class="fas fa-robot"></i>        ${message}`;
    chatContainer.appendChild(messageElement);
}

function handleCheckboxClick(checkboxId) {
    var checkboxes = document.querySelectorAll('input[name="template"]');
    checkboxes.forEach(function(checkbox) {
        if (checkbox.id !== checkboxId) {
             checkbox.checked = false;
        }
    });
}
function toggleDiv(action) {
    var editDiv = document.getElementById('Edit');
    var generateDiv = document.getElementById('Generate');
    var loadingDiv = document.getElementById('Loading');

    if (action === 'action1') {
        generateDiv.style.display = 'none';
        editDiv.style.display = 'block';
    } else if (action === 'action2') {
        loadingDiv.style.display = 'block'
        editDiv.style.display = 'none';
    }
}