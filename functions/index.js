"use strict";

const {initializeApp} = require("firebase-admin/app");
const {getFirestore} = require("firebase-admin/firestore");
const {logger} = require("firebase-functions");
const {defineSecret} = require("firebase-functions/params");
const {onDocumentCreated} = require("firebase-functions/v2/firestore");
const {onSchedule} = require("firebase-functions/v2/scheduler");
const {Resend} = require("resend");

initializeApp();

const db = getFirestore();
const RESEND_API_KEY = defineSecret("RESEND_API_KEY");
const FROM = "SpeakMasri <hello@speakmasri.com>";
const APP_URL = "https://speakmasri.com";
const VALID_MOMENT_TYPES = new Set(["partner", "traveler", "heritage"]);

function utcDateString(date = new Date()) {
  return date.toISOString().slice(0, 10);
}

function addUtcDays(dateString, days) {
  const [year, month, day] = dateString.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  date.setUTCDate(date.getUTCDate() + days);
  return utcDateString(date);
}

function escapeHtml(value) {
  return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
}

function momentSummary(moment) {
  if (!moment || !VALID_MOMENT_TYPES.has(moment.type)) return null;

  if (moment.type === "traveler") return "your trip to Egypt";
  if (moment.type === "heritage") return "reconnecting with your heritage";

  const name = typeof moment.personName === "string" ? moment.personName.trim() : "";
  return name ? `meeting ${name}` : "meeting the family";
}

function ownedPhraseCount(itemStats) {
  if (!itemStats || typeof itemStats !== "object" || Array.isArray(itemStats)) {
    return 0;
  }

  return Object.values(itemStats).filter((stats) => {
    if (!stats || typeof stats !== "object") return false;
    const correct = Number(stats.correct) || 0;
    const incorrect = Number(stats.incorrect) || 0;
    return correct >= 3 && correct >= incorrect * 3;
  }).length;
}

async function sendEmail(message) {
  const resend = new Resend(RESEND_API_KEY.value());
  const result = await resend.emails.send({...message, from: FROM});
  if (result.error) throw new Error(result.error.message || "Resend send failed");
  return result.data;
}

exports.onUserCreated = onDocumentCreated(
    {document: "users/{uid}", secrets: [RESEND_API_KEY]},
    async (event) => {
      const user = event.data && event.data.data();
      const email = user && user.email;
      if (!email) {
        logger.warn("Welcome email skipped: user has no email", {uid: event.params.uid});
        return;
      }

      const hasMoment = Boolean(user.moment && momentSummary(user.moment) && user.moment.date);
      const momentText = hasMoment ? "" : `\n\nOne useful next step: set your Moment in the app. It can be meeting the family, a trip, or reconnecting with your heritage. Giving that real scenario a date helps your learning point somewhere specific.`;
      const momentHtml = hasMoment ? "" : `<p>One useful next step: set your Moment in the app. It can be meeting the family, a trip, or reconnecting with your heritage. Giving that real scenario a date helps your learning point somewhere specific.</p>`;

      try {
        await sendEmail({
          to: email,
          subject: "Welcome to SpeakMasri — here's how it actually works",
          text: `Welcome to SpeakMasri.\n\nInstead of asking you to chase a streak, SpeakMasri tracks Owned Phrases: phrases you've gotten right consistently, not just once. Because the real goal is being able to say something out loud when it matters — not watching a habit-tracking number go up.${momentText}\n\nOpen SpeakMasri: ${APP_URL}\n\nI'm glad you're here,\nSpeakMasri`,
          html: `<p>Welcome to SpeakMasri.</p><p>Instead of asking you to chase a streak, SpeakMasri tracks <strong>Owned Phrases</strong>: phrases you've gotten right consistently, not just once. Because the real goal is being able to say something out loud when it matters — not watching a habit-tracking number go up.</p>${momentHtml}<p><a href="${APP_URL}">Open SpeakMasri</a></p><p>I'm glad you're here,<br>SpeakMasri</p>`,
        });
        logger.info("Welcome email sent", {uid: event.params.uid});
      } catch (error) {
        logger.error("Welcome email failed", {uid: event.params.uid, error});
      }
    },
);

exports.momentReminder = onSchedule(
    {schedule: "0 14 * * *", timeZone: "UTC", secrets: [RESEND_API_KEY]},
    async () => {
      const today = utcDateString();
      const inThreeDays = addUtcDays(today, 3);
      const snapshot = await db.collection("users")
          .where("moment.date", "in", [today, inThreeDays])
          .where("moment.reflection.choice", "==", "")
          .get();

      for (const doc of snapshot.docs) {
        const user = doc.data();
        const summary = momentSummary(user.moment);
        if (!user.email || !summary) {
          logger.warn("Moment reminder skipped", {uid: doc.id, reason: !user.email ? "missing email" : "invalid moment type"});
          continue;
        }

        const isToday = user.moment.date === today;
        const safeSummary = escapeHtml(summary);
        const message = isToday ? {
          subject: "Today's the day",
          text: `Today's the day for ${summary}. No pressure — take a breath, trust what you've practiced, and say what you can. You've got this.\n\nOpen SpeakMasri: ${APP_URL}`,
          html: `<p>Today's the day for ${safeSummary}.</p><p>No pressure — take a breath, trust what you've practiced, and say what you can. You've got this.</p><p><a href="${APP_URL}">Open SpeakMasri</a></p>`,
        } : {
          subject: `Your moment is in 3 days`,
          text: `Your moment — ${summary} — is in 3 days. A quick review of your Owned Phrases in the Phrasebook can help bring the words closer when you need them.\n\nReview your Phrasebook: ${APP_URL}`,
          html: `<p>Your moment — ${safeSummary} — is in 3 days.</p><p>A quick review of your <strong>Owned Phrases</strong> in the Phrasebook can help bring the words closer when you need them.</p><p><a href="${APP_URL}">Review your Phrasebook</a></p>`,
        };

        try {
          await sendEmail({to: user.email, ...message});
          logger.info("Moment reminder sent", {uid: doc.id, timing: isToday ? "today" : "three-days"});
        } catch (error) {
          logger.error("Moment reminder failed", {uid: doc.id, error});
        }
      }
    },
);

exports.reengagementNudge = onSchedule(
    {schedule: "0 15 * * *", timeZone: "UTC", secrets: [RESEND_API_KEY]},
    async () => {
      const today = utcDateString();
      const sevenDaysAgo = addUtcDays(today, -7);
      const thirtyDaysAgo = addUtcDays(today, -30);
      const snapshot = await db.collection("users")
          .where("lastActive", "==", sevenDaysAgo)
          .get();

      for (const doc of snapshot.docs) {
        const user = doc.data();
        if (!user.email) {
          logger.warn("Re-engagement email skipped: user has no email", {uid: doc.id});
          continue;
        }
        if (typeof user.lastReengagementEmailAt === "string" &&
            user.lastReengagementEmailAt > thirtyDaysAgo) {
          continue;
        }

        const count = ownedPhraseCount(user.itemStats);
        const progressText = count > 0 ?
          `You've got ${count} ${count === 1 ? "phrase" : "phrases"} ready to use.` :
          "Your progress is still here whenever you're ready.";

        try {
          await sendEmail({
            to: user.email,
            subject: "Your progress is still here",
            text: `${progressText}\n\nCome back for a short review and keep the words close to the people and moments you're learning them for.\n\nOpen SpeakMasri: ${APP_URL}`,
            html: `<p>${escapeHtml(progressText)}</p><p>Come back for a short review and keep the words close to the people and moments you're learning them for.</p><p><a href="${APP_URL}">Open SpeakMasri</a></p>`,
          });
          await doc.ref.set({lastReengagementEmailAt: today}, {merge: true});
          logger.info("Re-engagement email sent", {uid: doc.id, ownedPhrases: count});
        } catch (error) {
          logger.error("Re-engagement email failed", {uid: doc.id, error});
        }
      }
    },
);
