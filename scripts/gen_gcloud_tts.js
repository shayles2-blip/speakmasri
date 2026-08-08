const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT = 'project-7a4984f2-f553-4982-bb6';
const VOICE = 'ar-XA-Chirp3-HD-Achernar';
const ROOT = path.join(__dirname, '..');

function getToken() {
  return execSync('gcloud auth print-access-token').toString().trim();
}

const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const start = html.indexOf('const COURSE=') + 'const COURSE='.length;
let depth = 0, end = -1;
for (let i = start; i < html.length; i++) {
  if (html[i] === '{') depth++;
  if (html[i] === '}') { depth--; if (depth === 0) { end = i + 1; break; } }
}
const COURSE = eval('(' + html.slice(start, end) + ')');

const outDir = path.join(ROOT, 'audio');
fs.mkdirSync(outDir, { recursive: true });

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
  const jobs = [];
  COURSE.units.forEach(u => u.lessons.forEach(l => {
    l.vocab.forEach((v, idx) => {
      const outFile = path.join(outDir, `${l.id}_${idx}.mp3`);
      jobs.push({ text: v.ar, outFile, label: `${l.id}_${idx}` });
    });
  }));
  console.log(`Generating ${jobs.length} audio files with voice ${VOICE}...`);
  let done = 0, failed = [];
  let token = getToken();
  let tokenTime = Date.now();
  for (const job of jobs) {
    if (Date.now() - tokenTime > 40 * 60 * 1000) { token = getToken(); tokenTime = Date.now(); }
    try {
      await synth(job.text, job.outFile, token);
      done++;
      if (done % 10 === 0) console.log(`  ${done}/${jobs.length}`);
    } catch (e) {
      failed.push({ label: job.label, error: e.message });
      console.error(`FAILED ${job.label}: ${e.message}`);
    }
  }
  console.log(`Done: ${done}/${jobs.length}`);
  if (failed.length) console.log('Failures:', JSON.stringify(failed, null, 2));
}

main();
