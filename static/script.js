    async function fetchData() {
        try {
            const response = await fetch('/get_texts');
            const data = await response.json();

            // Update German texts (only last 5 items, in large font)
            const germanTexts = document.getElementById('german-texts');
            germanTexts.innerHTML = '';  // Clear existing text
            data.german.forEach(text => {
                const item = document.createElement('div');
                item.className = 'list-item';
                item.innerText = text;
                germanTexts.appendChild(item);
            });

            // Update partial text
            document.getElementById('german-partial').innerText = data.partial || '';

            // Update Russian texts (only last 5 items, in large font)
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

    setInterval(fetchData, 1000); // Fetch data every second