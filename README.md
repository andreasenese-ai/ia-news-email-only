# IA News Agent — Email Only (07:50 Europe/Rome)

Invia una email al giorno con notizie su IA. Nessun server: usa GitHub Actions.
- Orario: **07:50 Europe/Rome** (gestito con due cron UTC e dedup giornaliera).
- Modifica i feed in `ia_news_email_only.py` (lista `RSS_FEEDS`).

## Setup
1. Carica questi file su un nuovo repo:
   - `ia_news_email_only.py`
   - `.github/workflows/run_ia_news.yml`
   - `seen.json` (vuoto)

2. Imposta i Secrets (Settings → Secrets and variables → Actions):
   - `SMTP_HOST` (es. `smtp.office365.com` o `smtp.gmail.com`)
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = il tuo utente email
   - `SMTP_PASS` = password o app password
   - `EMAIL_FROM` = indirizzo mittente
   - `EMAIL_TO` = indirizzo destinatario

3. Vai su **Actions** → abilita i workflow → **Run workflow** per test.

Note: crea `last_sent.json` automaticamente al primo invio.
