const fs = require('fs');
const path = require('path');

const VOICE_ID = 'Xb7hH8MSUJpSbSDYk0k2'; // Alice - clear, educational
const key = process.env.ELEVENLABS_API_KEY;
if (!key) { console.error('ELEVENLABS_API_KEY not set'); process.exit(1); }

const htmlPath = path.join(__dirname, '..', 'index.html');
const html = fs.readFileSync(htmlPath, 'utf8');
const start = html.indexOf('const COURSE=') + 'const COURSE='.length;
let depth = 0, end = -1;
for (let i = start; i < html.length; i++) {
  if (html[i] === '{') depth++;
  if (html[i] === '}') { depth--; if (depth === 0) { end = i + 1; break; } }
}
const COURSE = eval('(' + html.slice(start, end) + ')');

const outDir = path.join(__dirname, '..', 'audio');
fs.mkdirSync(outDir, { recursive: true });

async function gen(text, outFile) {
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`, {
    method: 'POST',
    headers: { 'xi-api-key': key, 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, model_id: 'eleven_multilingual_v2' }),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`${res.status}: ${errText.slice(0, 200)}`);
  }
  const buf = Buffer.from(await res.arrayBuffer());
  fs.writeFileSync(outFile, buf);
}

async function main() {
  const jobs = [];
  COURSE.units.forEach(u => u.lessons.forEach(l => {
    l.vocab.forEach((v, idx) => {
      const outFile = path.join(outDir, `${l.id}_${idx}.mp3`);
      jobs.push({ text: v.ar, outFile, label: `${l.id}_${idx}` });
    });
  }));
  console.log(`Generating ${jobs.length} audio files...`);
  let done = 0, failed = [];
  for (const job of jobs) {
    try {
      await gen(job.text, job.outFile);
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
