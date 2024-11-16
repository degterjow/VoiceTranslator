    // Fetch data every second to keep text updated
    async function fetchData() {
        try {
            const response = await fetch('/get_texts');
            const data = await response.json();

            // Update German texts
            const germanTexts = document.getElementById('german-texts');
            germanTexts.innerHTML = '';  // Clear existing text
            data.german.forEach(text => {
                const item = document.createElement('div');
                item.className = 'list-item';
                item.innerText = text;
                germanTexts.appendChild(item);
            });

            // Update partial text (display it after the main German text)
            document.getElementById('german-partial').innerText = data.partial || '';

            // Update Russian texts
            const russianTexts = document.getElementById('russian-texts');
            russianTexts.innerHTML = '';  // Clear existing text
            data.russian.forEach(text => {
                const item = document.createElement('div');
                item.className = 'list-item';
                item.innerText = text;
                russianTexts.appendChild(item);
            });
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }

    // Fetch the data every second
    setInterval(fetchData, 1000);