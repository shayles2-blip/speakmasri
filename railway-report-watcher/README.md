# SpeakMasri Report Watcher

This is a one-shot Node.js job for a scheduled Railway Cron Job service.
It reads new documents from the `audioReports` and `partnerSubmissions` Firestore collections.
When reports are found, it sends a plain-text summary through Resend.
Its read-only checkpoint is stored as `REPORT_WATCHER_LAST_CHECKED` in Railway variables.
The process exits after each invocation; it is not a long-running web server.

Required variables are documented in `.env.example`:
`GOOGLE_APPLICATION_CREDENTIALS_JSON`, `RAILWAY_API_TOKEN`, `RESEND_API_KEY`, and `NOTIFY_EMAIL`.
Railway automatically supplies the project, environment, and service IDs.

Run locally with `npm install` followed by `npm start` after providing the required environment variables.
