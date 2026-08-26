# SpeakMasri lifecycle emails

Three functions: `onUserCreated` (welcome email), `momentReminder` (daily, T-3 and same-day nudges for a user's set Moment), `reengagementNudge` (daily, one nudge per 30 days for users inactive exactly 7 days).

Firebase billing (Blaze) and the required GCP APIs (cloudfunctions, cloudbuild, run, eventarc, artifactregistry, pubsub) are already enabled on `speakmasri-app`. The Firestore composite index `momentReminder` needs (`moment.date` + `moment.reflection.choice`) is already deployed (`firebase/firestore.indexes.json`).

## Remaining steps to go live

1. Sign up for Resend (resend.com) and verify the `speakmasri.com` sending domain (DNS records go through IONOS - ask for these to be added).
2. Set the secret from the repo's `firebase/` directory (where `firebase.json` lives):
   ```sh
   cd firebase && firebase functions:secrets:set RESEND_API_KEY --project speakmasri-app
   ```
3. Deploy:
   ```sh
   cd firebase && firebase deploy --only functions --project speakmasri-app
   ```
