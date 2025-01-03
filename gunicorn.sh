gunicorn -w 8 -b 0.0.0.0:5000 VoiceTranslator:app --log-level debug --access-logfile access.log --error-logfile error.log
