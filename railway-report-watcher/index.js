import { GoogleAuth } from "google-auth-library";

const FIRESTORE_PROJECT = "speakmasri-app";
const FIRESTORE_DATABASE = "(default)";
const COLLECTIONS = ["audioReports", "partnerSubmissions"];
const CHECKPOINT_VARIABLE = "REPORT_WATCHER_LAST_CHECKED";
const RAILWAY_GRAPHQL_URL = "https://backboard.railway.app/graphql/v2";

function requireEnv(name) {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required environment variable: ${name}`);
  return value;
}

async function railwayRequest(query, variables, token) {
  const response = await fetch(RAILWAY_GRAPHQL_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, variables }),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok || !payload || payload.errors) {
    throw new Error(
      `Railway API request failed (${response.status}): ${JSON.stringify(payload)}`,
    );
  }
  return payload.data;
}

async function getCheckpoint(railway) {
  const query = `query($projectId:String!,$environmentId:String!,$serviceId:String!){
    variables(projectId:$projectId, environmentId:$environmentId, serviceId:$serviceId)
  }`;
  const data = await railwayRequest(query, railway.ids, railway.token);
  const value = data.variables?.[CHECKPOINT_VARIABLE];
  if (!value) return new Date(0).toISOString();
  if (Number.isNaN(Date.parse(value))) {
    throw new Error(`${CHECKPOINT_VARIABLE} is not a valid ISO 8601 timestamp: ${value}`);
  }
  return value;
}

async function updateCheckpoint(railway, value) {
  const query = `mutation($input: VariableUpsertInput!){ variableUpsert(input:$input) }`;
  await railwayRequest(
    query,
    {
      input: {
        ...railway.ids,
        name: CHECKPOINT_VARIABLE,
        value,
        skipDeploys: true,
      },
    },
    railway.token,
  );
}

async function fetchCollection(collection, accessToken) {
  const baseUrl = `https://firestore.googleapis.com/v1/projects/${FIRESTORE_PROJECT}/databases/${encodeURIComponent(FIRESTORE_DATABASE)}/documents/${collection}`;
  const documents = [];
  let pageToken;

  do {
    const url = new URL(baseUrl);
    url.searchParams.set("pageSize", "300");
    if (pageToken) url.searchParams.set("pageToken", pageToken);
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok || !payload) {
      throw new Error(
        `Firestore read failed for ${collection} (${response.status}): ${JSON.stringify(payload)}`,
      );
    }
    documents.push(...(payload.documents ?? []));
    pageToken = payload.nextPageToken;
  } while (pageToken);

  return documents;
}

function decodeFirestoreValue(value) {
  if (!value || typeof value !== "object") return value;
  if ("nullValue" in value) return null;
  if ("stringValue" in value) return value.stringValue;
  if ("booleanValue" in value) return value.booleanValue;
  if ("integerValue" in value) return Number(value.integerValue);
  if ("doubleValue" in value) return value.doubleValue;
  if ("timestampValue" in value) return value.timestampValue;
  if ("referenceValue" in value) return value.referenceValue;
  if ("bytesValue" in value) return value.bytesValue;
  if ("geoPointValue" in value) return value.geoPointValue;
  if ("arrayValue" in value) {
    return (value.arrayValue.values ?? []).map(decodeFirestoreValue);
  }
  if ("mapValue" in value) return decodeFirestoreFields(value.mapValue.fields ?? {});
  return value;
}

function decodeFirestoreFields(fields) {
  return Object.fromEntries(
    Object.entries(fields ?? {}).map(([key, value]) => [key, decodeFirestoreValue(value)]),
  );
}

function printable(value) {
  if (value === undefined) return "(not provided)";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

function buildEmailBody(newDocuments) {
  const audioFields = ["lessonId", "idx", "ar", "franco", "reason", "voicePref", "note"];
  const sections = [];

  for (const collection of COLLECTIONS) {
    const documents = newDocuments[collection];
    if (!documents.length) continue;
    const lines = [`${collection} (${documents.length})`, ""];

    documents.forEach((document, index) => {
      const fields = decodeFirestoreFields(document.fields);
      lines.push(`Report ${index + 1}`);
      if (collection === "audioReports") {
        for (const field of audioFields) lines.push(`${field}: ${printable(fields[field])}`);
      } else {
        for (const [field, value] of Object.entries(fields).sort(([a], [b]) => a.localeCompare(b))) {
          lines.push(`${field}: ${printable(value)}`);
        }
      }
      lines.push(`createTime: ${document.createTime}`, "");
    });
    sections.push(lines.join("\n").trimEnd());
  }

  return sections.join("\n\n--------------------\n\n");
}

async function sendEmail(apiKey, notifyEmail, documents, count) {
  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: "SpeakMasri Reports <reports@updates.speakmasri.com>",
      to: [notifyEmail],
      subject: `${count} new SpeakMasri report(s)`,
      text: buildEmailBody(documents),
    }),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(`Resend API request failed (${response.status}): ${JSON.stringify(payload)}`);
  }
}

async function main() {
  console.log("Report watcher started.");
  const credentialsJson = requireEnv("GOOGLE_APPLICATION_CREDENTIALS_JSON");
  const railway = {
    token: requireEnv("RAILWAY_API_TOKEN"),
    ids: {
      projectId: requireEnv("RAILWAY_PROJECT_ID"),
      environmentId: requireEnv("RAILWAY_ENVIRONMENT_ID"),
      serviceId: requireEnv("RAILWAY_SERVICE_ID"),
    },
  };
  const resendApiKey = requireEnv("RESEND_API_KEY");
  const notifyEmail = requireEnv("NOTIFY_EMAIL");

  let credentials;
  try {
    credentials = JSON.parse(credentialsJson);
  } catch (error) {
    throw new Error(`GOOGLE_APPLICATION_CREDENTIALS_JSON is not valid JSON: ${error.message}`);
  }

  console.log("Reading checkpoint from Railway.");
  const lastChecked = await getCheckpoint(railway);
  const lastCheckedTime = Date.parse(lastChecked);
  console.log(`Checking for documents created after ${lastChecked}.`);

  console.log("Authenticating with Google Cloud.");
  const auth = new GoogleAuth({
    credentials,
    scopes: ["https://www.googleapis.com/auth/datastore"],
  });
  const accessToken = await auth.getAccessToken();
  if (!accessToken) throw new Error("Google Cloud did not return an access token.");

  const newDocuments = {};
  for (const collection of COLLECTIONS) {
    const documents = await fetchCollection(collection, accessToken);
    newDocuments[collection] = documents.filter(
      (document) => document.createTime && Date.parse(document.createTime) > lastCheckedTime,
    );
    console.log(
      `${collection}: read ${documents.length} document(s), found ${newDocuments[collection].length} new document(s).`,
    );
  }

  const newCount = Object.values(newDocuments).reduce((sum, documents) => sum + documents.length, 0);
  if (newCount > 0) {
    console.log(`Sending email for ${newCount} new report(s).`);
    await sendEmail(resendApiKey, notifyEmail, newDocuments, newCount);
    console.log("Email sent successfully.");
  } else {
    console.log("No new reports found; no email sent.");
  }

  const newCheckpoint = new Date().toISOString();
  await updateCheckpoint(railway, newCheckpoint);
  console.log(`Checkpoint updated to ${newCheckpoint}.`);
  console.log("Report watcher finished successfully.");
}

main().catch((error) => {
  console.error("Report watcher failed:", error);
  process.exitCode = 1;
});
