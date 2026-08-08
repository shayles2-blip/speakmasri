const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT = 'project-7a4984f2-f553-4982-bb6';
const VOICE = 'ar-XA-Chirp3-HD-Achernar';
const ROOT = path.join(__dirname, '..');

function getToken() {
  return execSync('gcloud auth print-access-token').toString().trim();
}

async function synth(text, outFile, token) {
  const res = await fetch('https://texttospeech.googleapis.com/v1/text:synthesize', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'x-goog-user-project': PROJECT,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      input: { text },
      voice: { languageCode: 'ar-XA', name: VOICE },
      audioConfig: { audioEncoding: 'MP3' },
    }),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`${res.status}: ${errText.slice(0, 300)}`);
  }
  const data = await res.json();
  fs.writeFileSync(outFile, Buffer.from(data.audioContent, 'base64'));
}

async function main() {
  const jobs = JSON.parse(fs.readFileSync('/tmp/new_audio_jobs.json', 'utf8'));
  console.log(`Generating ${jobs.length} new audio files...`);
  let done = 0, failed = [];
  let token = getToken();
  let tokenTime = Date.now();
  for (const job of jobs) {
    if (Date.now() - tokenTime > 40 * 60 * 1000) { token = getToken(); tokenTime = Date.now(); }
    try {
      await synth(job.text, path.join(ROOT, job.outFile), token);
      done++;
      if (done % 10 === 0) console.log(`  ${done}/${jobs.length}`);
    } catch (e) {
      failed.push({ label: job.lessonId + '_' + job.idx, error: e.message });
      console.error(`FAILED ${job.lessonId}_${job.idx}: ${e.message}`);
    }
  }
  console.log(`Done: ${done}/${jobs.length}`);
  if (failed.length) console.log('Failures:', JSON.stringify(failed, null, 2));
}

main();
