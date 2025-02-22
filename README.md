**Этот проект предназначен для синхронного перевода проповедей с немецкого языка на русский.** 

Проект использует последовательно 3 нейросети: 
  * [gladia.io](https://app.gladia.io/auth/signin)  переводит немецкую речь в немецкий текст (Статус: запрограммировано и протестировано)
  * deepl переводит немецкий текст в русский  (Статус: запрограммировано и протестировано)
  * Elevenlabs переводит русский текст в русскую речь  (Статус: запрограммировано, но НЕ протестировано)

Основная особенность этого проекта что на смартфонах не предусматривается установки никаких программных клиентов, 
тоесть любой нативный браузер на Android или на iPhone сможет подключаться к серверу на котором запущен VoiceTranslator и нативно получать голосовой поток.
Для подключения любого нового клиента достаточно просканировать два 2D  баркода: первый для подключения к WiFi и второй для подключения голосового перевода в реальном времени.

## Настройка проекта

### API keys
для настройки необходимо зарегистрироваться и получить API  ключи на сервисах
* [gladia.io](https://app.gladia.io/auth/signin)
* [DeepL](https://www.deepl.com/de/login) 
* [ElevenLabs](https://elevenlabs.io/app/sign-in) 

API ключи должны быть сохранены в файлах

`
GLADIA_API_KEY_FILE = 'gladia_api_key.txt'
DEEPL_API_KEY_FILE = 'deepl_api_key.txt'
ELEVEN_LABS_API_KEY_FILE = 'eleven_labs_api_key.txt'
`
### Line-In Device ID
Далее выбрать источник звука (LINE IN вашей звуковой карты)
Для идентификации вашего оборудования запустите скрипт device_enumerator.py и внесите код вашей карты в константу 
LINE_IN_DEVICE_ID = 2

### Статус работы
Статус работы отображается в браузере по адресу http://localhost/
По умолчанию там показываются три последние строки немецкого текста, одна строка с текущим переводом и три последние строки русского перевода

### Голосовой поток на смартфоне
http://<voice.translator.server.ip>/audio_stream

---

**Dieses Projekt ist für die Simultanübersetzung von Predigten vom Deutschen ins Russische konzipiert.

Das Projekt verwendet 3 neuronale Netze nacheinander:
* [gladia.io](https://app.gladia.io/auth/signin) übersetzt deutsche Sprache in deutschen Text (Status: programmiert und getestet)
* dee übersetzt deutschen Text in russischen Text (Status: programmiert und getestet)
* Elevenlabs übersetzt russischen Text in russische Sprache (Status: programmiert, aber NICHT getestet)

Das Hauptmerkmal dieses Projekts ist, dass keine Software-Clients auf Smartphones installiert werden müssen,
d.h. jeder native Browser auf Android oder iPhone wird in der Lage sein, sich mit dem Server zu verbinden, auf dem VoiceTranslator läuft und den Sprachstrom nativ zu empfangen.
Um einen neuen Client zu verbinden, müssen lediglich zwei 2D-Barcodes gescannt werden: der erste für die WiFi-Verbindung und der zweite für die Echtzeit-Sprachübersetzung.

### Projekt-Einrichtung

### API-Schlüssel
Um das Projekt zu konfigurieren, müssen Sie sich bei den folgenden Diensten registrieren und API-Schlüssel erhalten
* [gladia.io](https://app.gladia.io/auth/signin)
* [DeepL](https://www.deepl.com/de/login)
* [ElevenLabs](https://elevenlabs.io/app/sign-in)

Die API-Schlüssel sollten in den folgenden Dateien gespeichert werden

`
GLADIA_API_KEY_FILE = 'gladia_api_key.txt'
DEEPL_API_KEY_FILE = 'deepl_api_key.txt'
ELEVEN_LABS_API_API_KEY_FILE = 'eleven_labs_api_key.txt'
`
### Line-In Geräte-ID
Wählen Sie als nächstes die Audioquelle (LINE IN Ihrer Soundkarte)
Um Ihre Hardware zu identifizieren, starten Sie das Skript device_enumerator.py und geben Sie den Code Ihrer Karte in die Konstante
LINE_IN_DEVICE_ID = 2

### Betriebsstatus
Der Betriebsstatus wird im Browser unter http://localhost/ angezeigt.
Standardmäßig zeigt er die letzten drei Zeilen des deutschen Textes, eine Zeile mit der aktuellen Übersetzung und die letzten drei Zeilen der russischen Übersetzung

### Voice Stream auf Smartphone
http://<voice.translator.server.ip>/audio_stream
