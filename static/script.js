async function updateText() {
    try {
        const response = await fetch('/get_texts');
        const data = await response.json();

        const germanContainer = document.getElementById('german');
        const russianContainer = document.getElementById('russian');

        // Очистка контейнеров
        germanContainer.innerHTML = '';
        russianContainer.innerHTML = '';

        // Добавляем новые предложения
        data.german.forEach(sentence => {
            const p = document.createElement('p');
            p.textContent = sentence;
            germanContainer.appendChild(p);
        });

        data.russian.forEach(sentence => {
            const p = document.createElement('p');
            p.textContent = sentence;
            russianContainer.appendChild(p);
        });

        // Прокрутка к последней фразе
        germanContainer.scrollTop = germanContainer.scrollHeight;
        russianContainer.scrollTop = russianContainer.scrollHeight;

    } catch (error) {
        console.error('Ошибка обновления текста:', error);
    }
}

// Обновление текста каждые 2 секунды
setInterval(updateText, 2000);
