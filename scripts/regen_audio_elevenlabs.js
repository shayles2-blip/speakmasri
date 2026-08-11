const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const PROJECT = 'project-7a4984f2-f553-4982-bb6';
const DEFAULT_VOICE_ID = 'R1vEEI2FG1sW3IvcbDTI';
const MODEL_ID = 'eleven_multilingual_v2';
const ROOT = path.join(__dirname, '..');
const IPA_FILE = path.join(__dirname, 'egyptian_ipa.json');
let AUDIO_DIR = path.join(ROOT, 'audio');
const TTS_API_BASE_URL = 'https://api.elevenlabs.io/v1/text-to-speech';
// ElevenLabs' default MP3 response format is mp3_44100_128.
// RecognitionConfig documents MP3 support on the v1p1beta1 endpoint.
const STT_API_URL = 'https://speech.googleapis.com/v1p1beta1/speech:recognize';
const STT_LANGUAGE = 'ar-EG';
const AUDIO_SAMPLE_RATE_HERTZ = 44100;
const QA_SIMILARITY_THRESHOLD = 0.6;
const TOKEN_MAX_AGE_MS = 40 * 60 * 1000;
const MAX_ATTEMPTS = 5;

function getToken() {
  return execFileSync('gcloud', ['auth', 'print-access-token'], {
    encoding: 'utf8',
  }).trim();
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function parseArgs(argv) {
  const options = { limit: Infinity, only: null, voice: DEFAULT_VOICE_ID, outDir: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--limit') {
      const limit = Number(argv[++i]);
      if (!Number.isInteger(limit) || limit < 1) throw new Error('--limit must be a positive integer');
      options.limit = limit;
    } else if (argv[i] === '--only') {
      options.only = argv[++i];
      if (!options.only) throw new Error('--only requires a lessonId_idx label');
    } else if (argv[i] === '--voice') {
      options.voice = argv[++i];
      if (!options.voice) throw new Error('--voice requires a voice ID');
    } else if (argv[i] === '--out-dir') {
      options.outDir = argv[++i];
      if (!options.outDir) throw new Error('--out-dir requires a path');
    } else {
      throw new Error(`Unknown argument: ${argv[i]}`);
    }
  }
  return options;
}

function loadJobs(options) {
  const entries = JSON.parse(fs.readFileSync(IPA_FILE, 'utf8'));
  if (!Array.isArray(entries)) throw new Error(`${IPA_FILE} must contain a JSON array`);

  const seen = new Set();
  for (const [position, entry] of entries.entries()) {
    if (!entry || typeof entry.lessonId !== 'string' || !Number.isInteger(entry.idx) ||
        entry.idx < 0 || typeof entry.ar !== 'string' || typeof entry.ipa !== 'string' ||
        !entry.ar || !entry.ipa) {
      throw new Error(`Invalid IPA entry at array position ${position}`);
    }
    const label = `${entry.lessonId}_${entry.idx}`;
    if (seen.has(label)) throw new Error(`Duplicate IPA entry: ${label}`);
    seen.add(label);
  }

  let jobs = entries;
  if (options.only) jobs = jobs.filter(entry => `${entry.lessonId}_${entry.idx}` === options.only);
  if (options.only && jobs.length === 0) throw new Error(`No IPA entry matches --only ${options.only}`);
  return jobs.slice(0, options.limit);
}

async function synthesize(entry, apiKey, voiceId) {
  const response = await fetch(`${TTS_API_BASE_URL}/${encodeURIComponent(voiceId)}`, {
    method: 'POST',
    headers: {
      'xi-api-key': apiKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: entry.ar,
      model_id: MODEL_ID,
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
    headers: {
      Authorization: `Bearer ${token}`,
      'x-goog-user-project': PROJECT,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      config: {
        encoding: 'MP3',
        sampleRateHertz: AUDIO_SAMPLE_RATE_HERTZ,
        languageCode: STT_LANGUAGE,
        model: 'latest_short',
      },
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
  return (data.results || [])
    .map(result => result.alternatives?.[0]?.transcript || '')
    .join(' ')
    .trim();
}

function normalizeArabic(value) {
  return value
    .normalize('NFKC')
    .replace(/[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]/g, '')
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه')
    .replace(/ؤ/g, 'و')
    .replace(/ئ/g, 'ي')
    .replace(/[^\u0621-\u063A\u0641-\u064A]/g, '');
}

function levenshteinDistance(a, b) {
  const previous = Array.from({ length: b.length + 1 }, (_, index) => index);
  for (let i = 1; i <= a.length; i++) {
    let diagonal = previous[0];
    previous[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const above = previous[j];
      previous[j] = Math.min(
        previous[j] + 1,
        previous[j - 1] + 1,
        diagonal + (a[i - 1] === b[j - 1] ? 0 : 1),
      );
      diagonal = above;
    }
  }
  return previous[b.length];
}

function assessTranscript(expected, transcript) {
  const normalizedExpected = normalizeArabic(expected);
  const normalizedTranscript = normalizeArabic(transcript);
  if (!normalizedExpected || !normalizedTranscript) {
    return { passed: false, similarity: 0, normalizedExpected, normalizedTranscript };
  }
  const distance = levenshteinDistance(normalizedExpected, normalizedTranscript);
  const similarity = 1 - distance / Math.max(normalizedExpected.length, normalizedTranscript.length);
  return {
    passed: similarity >= QA_SIMILARITY_THRESHOLD,
    similarity,
    normalizedExpected,
    normalizedTranscript,
  };
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) throw new Error('ELEVENLABS_API_KEY not set');
  if (options.outDir) AUDIO_DIR = path.isAbsolute(options.outDir) ? options.outDir : path.join(ROOT, options.outDir);
  const jobs = loadJobs(options);
  fs.mkdirSync(AUDIO_DIR, { recursive: true });

  console.log(`Regenerating ${jobs.length} file(s) with ElevenLabs voice ${options.voice}...`);
  let token = getToken();
  let tokenTime = Date.now();
  let passedQa = 0;
  const qaInconclusive = [];
  const qaFlagged = [];
  const failures = [];

  for (const [jobIndex, entry] of jobs.entries()) {
    const label = `${entry.lessonId}_${entry.idx}`;
    let lastError;

    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
      if (Date.now() - tokenTime > TOKEN_MAX_AGE_MS) {
        token = getToken();
        tokenTime = Date.now();
      }

      try {
        const audio = await synthesize(entry, apiKey, options.voice);
        fs.writeFileSync(path.join(AUDIO_DIR, `${label}.mp3`), audio);
        let qa;
        try {
          const transcript = await transcribe(audio, token);
          qa = { transcript, ...assessTranscript(entry.ar, transcript) };
        } catch (error) {
          qa = { passed: false, transcript: '', similarity: 0, error: error.message };
        }

        if (!qa.transcript) {
          qaInconclusive.push({
            label,
            expected: entry.ar,
            ...(qa.error ? { error: qa.error } : {}),
          });
          console.warn(`${jobIndex + 1}/${jobs.length} QA INCONCLUSIVE ${label}: ` +
            `expected=${JSON.stringify(entry.ar)}, transcript=""` +
            `${qa.error ? `, error=${qa.error}` : ''}; needs manual spot-check`);
        } else if (qa.passed) {
          passedQa++;
          console.log(`${jobIndex + 1}/${jobs.length} done: ${label}; QA PASS ` +
            `(expected=${JSON.stringify(entry.ar)}, transcript=${JSON.stringify(qa.transcript)}, ` +
            `similarity=${qa.similarity.toFixed(3)})`);
        } else {
          qaFlagged.push({
            label,
            expected: entry.ar,
            transcript: qa.transcript,
            similarity: qa.similarity,
            ...(qa.error ? { error: qa.error } : {}),
          });
          console.warn(`${jobIndex + 1}/${jobs.length} QA FAILURE ${label}: ` +
            `expected=${JSON.stringify(entry.ar)}, transcript=${JSON.stringify(qa.transcript)}, ` +
            `similarity=${qa.similarity.toFixed(3)}${qa.error ? `, error=${qa.error}` : ''}`);
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
      console.error(`${jobIndex + 1}/${jobs.length} FAILED ${label}: ${lastError.message}`);
    }
  }

  console.log(`Finished: ${passedQa} succeeded and passed QA; ` +
    `${qaInconclusive.length} succeeded with inconclusive QA; ` +
    `${qaFlagged.length} succeeded but QA-flagged for manual review; ` +
    `${failures.length} failed to generate.`);
  if (qaInconclusive.length) {
    console.warn('QA-inconclusive (manual spot-check needed):',
      JSON.stringify(qaInconclusive, null, 2));
  }
  if (qaFlagged.length) {
    console.warn('QA-flagged:', JSON.stringify(qaFlagged, null, 2));
  }
  if (failures.length) {
    console.error('Failures:', JSON.stringify(failures, null, 2));
    process.exitCode = 1;
  }
}

main().catch(error => {
  console.error(`Fatal setup error: ${error.stack || error.message}`);
  process.exitCode = 1;
});
