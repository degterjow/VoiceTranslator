const MAX_TRANSLATION_ROWS = 3; // Maximum number of rows to display in each section

document.addEventListener('DOMContentLoaded', function() {
    // Your existing JavaScript code
    const germanTextsContainer = document.getElementById("german-texts");
    const russianTextsContainer = document.getElementById("russian-texts");
    const germanPartialElement = document.getElementById("german-partial");

    // Initial GET request
    fetch('/get_initial_texts')
        .then(response => response.json())
        .then(data => {
            data.german.forEach(line => {
                const lineElement = document.createElement("div");
                lineElement.textContent = line;
                germanTextsContainer.appendChild(lineElement);
            });

            data.russian.forEach(line => {
                const lineElement = document.createElement("div");
                lineElement.textContent = line;
                russianTextsContainer.appendChild(lineElement);
            });
        })
        .catch(error => {
            console.error('Error loading initial text data:', error);
        });

    // SSE connection for updates
    const eventSource = new EventSource('/stream');

    eventSource.onmessage = function (event) {
        // Default event type handling (fallback)
        const data = JSON.parse(event.data);
        console.log('SSE Parsed Data:', data); // Log the parsed JSON

        // Check for update (both German and Russian lines)
        if (data.new_german && data.new_russian) {
            addNewLines(data.new_german, data.new_russian);
        }

        // Handle german_partial updates
        if (data.german_partial) {
            updatePartial(data.german_partial);
        }
    };

    // Handle specific event types if the server sends them
    eventSource.addEventListener("partial", (event) => {
        const data = JSON.parse(event.data);
        if (data.german_partial) {
            updatePartial(data.german_partial);
        }
    });

    eventSource.addEventListener("update", (event) => {
        const data = JSON.parse(event.data);
        if (data.new_german && data.new_russian) {
            addNewLines(data.new_german, data.new_russian);
        }
    });

    function updatePartial(newPartial) {
        const partialElement = document.getElementById("german-partial");
        partialElement.textContent = newPartial;

        // Add fade-in animation for better visibility
        partialElement.classList.remove("fade-in");
        void partialElement.offsetWidth; // Trigger reflow
        partialElement.classList.add("fade-in");
    }

    function addNewLines(newGerman, newRussian) {
        const newGermanLine = document.createElement("div");
        newGermanLine.textContent = newGerman;
        newGermanLine.classList.add("line", "fade-in");

        const newRussianLine = document.createElement("div");
        newRussianLine.textContent = newRussian;
        newRussianLine.classList.add("line", "fade-in");

        germanTextsContainer.appendChild(newGermanLine);
        russianTextsContainer.appendChild(newRussianLine);

        // Remove old lines if exceeded max rows
        if (germanTextsContainer.children.length > MAX_TRANSLATION_ROWS) {
            germanTextsContainer.removeChild(germanTextsContainer.firstChild);
        }
        if (russianTextsContainer.children.length > MAX_TRANSLATION_ROWS) {
            russianTextsContainer.removeChild(russianTextsContainer.firstChild);
        }
    }

});
