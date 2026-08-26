// One-off generator for vocab items missing audio, using the same
// ElevenLabs params/QA logic as regen_audio_elevenlabs.js, but reading
// jobs directly from a JSON job file instead of requiring an IPA entry
// (the ipa field is validated but never actually sent to the API anyway).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const PROJECT = 'project-7a4984f2-f553-4982-bb6';
const MODEL_ID = 'eleven_turbo_v2_5';
const ROOT = path.join(__dirname, '..');
const TTS_API_BASE_URL = 'https://api.elevenlabs.io/v1/text-to-speech';
const STT_API_URL = 'https://speech.googleapis.com/v1p1beta1/speech:recognize';
const STT_LANGUAGE = 'ar-EG';
const AUDIO_SAMPLE_RATE_HERTZ = 44100;
const QA_SIMILARITY_THRESHOLD = 0.6;
const TOKEN_MAX_AGE_MS = 40 * 60 * 1000;
const MAX_ATTEMPTS = 5;

function getToken() {
  return execFileSync('gcloud', ['auth', 'print-access-token'], { encoding: 'utf8' }).trim();
}
function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

async function synthesize(ar, apiKey, voiceId) {
  const response = await fetch(`${TTS_API_BASE_URL}/${encodeURIComponent(voiceId)}`, {
    method: 'POST',
    headers: { 'xi-api-key': apiKey, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: ar,
      model_id: MODEL_ID,
      language_code: 'ar',
      voice_settings: { stability: 0.30, similarity_boost: 0.85, style: 0.0, use_speaker_boost: true, speed: 0.80 },
    }),
  });
  if (!response.ok) {
    const body = await response.text();
    const error = new Error(`${response.status}: ${body.slice(0, 500)}`);
    error.status = response.status;
    throw error;
  }
  return Buffer.from(await response.arrayBuffer());
}

async function transcribe(audio, token) {
  const response = await fetch(STT_API_URL, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'x-goog-user-project': PROJECT, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      config: { encoding: 'MP3', sampleRateHertz: AUDIO_SAMPLE_RATE_HERTZ, languageCode: STT_LANGUAGE, model: 'latest_short' },
      audio: { content: audio.toString('base64') },
    }),
  });
  if (!response.ok) {
    const body = await response.text();
    const error = new Error(`${response.status}: ${body.slice(0, 500)}`);
    error.status = response.status;
    throw error;
  }
  const data = await response.json();
  return (data.results || []).map(r => r.alternatives?.[0]?.transcript || '').join(' ').trim();
}

function normalizeArabic(value) {
  return value.normalize('NFKC')
    .replace(/[ً-ٰٟۖ-ۭـ]/g, '')
    .replace(/[أإآٱ]/g, 'ا').replace(/ى/g, 'ي').replace(/ة/g, 'ه')
    .replace(/ؤ/g, 'و').replace(/ئ/g, 'ي')
    .replace(/[^ء-غف-ي]/g, '');
}
function levenshteinDistance(a, b) {
  const previous = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    let diagonal = previous[0]; previous[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const above = previous[j];
      previous[j] = Math.min(previous[j] + 1, previous[j - 1] + 1, diagonal + (a[i - 1] === b[j - 1] ? 0 : 1));
      diagonal = above;
    }
  }
  return previous[b.length];
}
function assessTranscript(expected, transcript) {
  const ne = normalizeArabic(expected), nt = normalizeArabic(transcript);
  if (!ne || !nt) return { passed: false, similarity: 0 };
  const distance = levenshteinDistance(ne, nt);
  const similarity = 1 - distance / Math.max(ne.length, nt.length);
  return { passed: similarity >= QA_SIMILARITY_THRESHOLD, similarity };
}

async function main() {
  const jobsFile = process.argv[2];
  const voiceId = process.argv[3];
  const outDir = path.join(ROOT, process.argv[4]);
  if (!jobsFile || !voiceId || !outDir) throw new Error('usage: node gen_missing_audio.js <jobsFile.json> <voiceId> <outDir>');
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) throw new Error('ELEVENLABS_API_KEY not set');

  const jobs = JSON.parse(fs.readFileSync(jobsFile, 'utf8'));
  fs.mkdirSync(outDir, { recursive: true });
  console.log(`Generating ${jobs.length} file(s) with voice ${voiceId} -> ${outDir}`);

  let token = getToken(), tokenTime = Date.now();
  let passedQa = 0;
  const qaInconclusive = [], qaFlagged = [], failures = [];

  for (const [i, job] of jobs.entries()) {
    const label = `${job.lessonId}_${job.idx}`;
    let lastError;
    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
      if (Date.now() - tokenTime > TOKEN_MAX_AGE_MS) { token = getToken(); tokenTime = Date.now(); }
      try {
        const audio = await synthesize(job.ar, apiKey, voiceId);
        fs.writeFileSync(path.join(outDir, `${label}.mp3`), audio);
        let qa;
        try {
          const transcript = await transcribe(audio, token);
          qa = { transcript, ...assessTranscript(job.ar, transcript) };
        } catch (e) {
          qa = { passed: false, transcript: '', similarity: 0, error: e.message };
        }
        if (!qa.transcript) {
          qaInconclusive.push({ label, expected: job.ar, ...(qa.error ? { error: qa.error } : {}) });
          console.warn(`${i + 1}/${jobs.length} QA INCONCLUSIVE ${label}: expected=${JSON.stringify(job.ar)}${qa.error ? `, error=${qa.error}` : ''}`);
        } else if (qa.passed) {
          passedQa++;
          console.log(`${i + 1}/${jobs.length} done: ${label}; QA PASS (similarity=${qa.similarity.toFixed(3)})`);
        } else {
          qaFlagged.push({ label, expected: job.ar, transcript: qa.transcript, similarity: qa.similarity });
          console.warn(`${i + 1}/${jobs.length} QA FAILURE ${label}: expected=${JSON.stringify(job.ar)}, transcript=${JSON.stringify(qa.transcript)}, similarity=${qa.similarity.toFixed(3)}`);
        }
        lastError = null;
        break;
      } catch (error) {
        lastError = error;
        const authError = error.status === 401 || error.status === 403;
        const retryable = authError || error.status === 429 || error.status >= 500;
        if (!retryable || attempt === MAX_ATTEMPTS) break;
        const delayMs = Math.min(1000 * (2 ** (attempt - 1)), 16000);
        console.warn(`Retrying ${label} after attempt ${attempt}/${MAX_ATTEMPTS}: ${lastError.message}`);
        await sleep(delayMs);
      }
    }
    if (lastError) {
      failures.push({ label, error: lastError.message });
      console.error(`${i + 1}/${jobs.length} FAILED ${label}: ${lastError.message}`);
    }
  }
  console.log(`Finished: ${passedQa} passed QA; ${qaInconclusive.length} inconclusive; ${qaFlagged.length} flagged; ${failures.length} failed.`);
  if (qaInconclusive.length) console.warn('Inconclusive:', JSON.stringify(qaInconclusive, null, 2));
  if (qaFlagged.length) console.warn('Flagged:', JSON.stringify(qaFlagged, null, 2));
  if (failures.length) { console.error('Failures:', JSON.stringify(failures, null, 2)); process.exitCode = 1; }
}
main().catch(e => { console.error(`Fatal: ${e.stack || e.message}`); process.exitCode = 1; });
