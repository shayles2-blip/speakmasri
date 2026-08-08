const { chromium } = require('playwright');
const path = require('path');

const VOCAB_LOOKUP = {
  'أيوة': 'Yes', 'لأ': 'No', 'يلا': "Let's go / Come on",
  'خلاص': 'Finished / Enough / OK', 'إن شاء الله': 'God willing',
};

(async () => {
  const browser = await chromium.launch({ args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] });
  const context = await browser.newContext({ permissions: ['microphone'] });
  const page = await context.newPage();
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') { errors.push(msg.text()); console.log('  >> CONSOLE_ERROR at this point:', msg.text()); } });
  page.on('pageerror', err => {
    const m = 'PAGEERROR: ' + err.message + ' | STACK: ' + (err.stack || '').slice(0,300);
    errors.push(m);
    console.log('  >> PAGEERROR FIRED RIGHT NOW:', m);
  });

  const filePath = 'file://' + path.resolve(__dirname, '..', 'index.html');
  await page.goto(filePath);
  await page.screenshot({ path: '/tmp/e2e_01_auth.png' });

  // Sign up
  await page.fill('#name', 'Test Learner');
  await page.fill('#email', `test${Date.now()}@example.com`);
  await page.fill('#pass', 'testpass123');
  await page.selectOption('#motivation', 'partner');
  await page.click('button:has-text("Sign Up")');
  await page.waitForSelector('#main:not(.hidden)', { timeout: 5000 });
  await page.screenshot({ path: '/tmp/e2e_02_learn.png' });
  console.log('SIGNUP_OK');

  // Start first lesson
  const firstNode = await page.locator('.lesson-row.unlocked').first();
  await firstNode.click();
  await page.waitForSelector('#lesson:not(.hidden)', { timeout: 5000 });
  await page.screenshot({ path: '/tmp/e2e_03_lesson_start.png' });
  console.log('LESSON_STARTED');

  let exerciseCount = 0;
  const maxExercises = 60; // safety cap
  while (exerciseCount < maxExercises) {
    const done = await page.locator('#done:not(.hidden)').count();
    if (done > 0) break;

    exerciseCount++;
    const isMatch = await page.locator('.match-cols').count();
    const dbgBtnText = await page.locator('#checkBtn').textContent().catch(() => 'N/A');
    const dbgQ = await page.locator('.q').first().textContent().catch(() => 'N/A');
    console.log(`[${exerciseCount}] isMatch=${isMatch} btn="${dbgBtnText}" q="${dbgQ}"`);

    if (isMatch > 0) {
      // solve the match exercise using known vocab pairs
      for (let attempt = 0; attempt < 10; attempt++) {
        const enButtons = await page.locator('[data-en]:not(.correct)').all();
        if (enButtons.length === 0) break;
        const enText = await enButtons[0].getAttribute('data-en');
        const targetAr = Object.keys(VOCAB_LOOKUP).find(ar => VOCAB_LOOKUP[ar] === enText);
        await enButtons[0].click();
        if (targetAr) {
          const arBtn = page.locator(`[data-ar="${targetAr}"]`);
          if (await arBtn.count()) await arBtn.click();
        }
        await page.waitForTimeout(700);
      }
      await page.waitForTimeout(600);
      continue;
    }

    const checkBtn = page.locator('#checkBtn');
    const isCheckPhase = (await checkBtn.textContent())?.trim() === 'Check';

    try {
      if (isCheckPhase) {
        const fillInput = await page.locator('#fillInput').count();
        if (fillInput > 0) {
          await page.fill('#fillInput', exerciseCount % 3 === 0 ? 'wronganswer' : 'test');
        } else {
          const opts = await page.locator('.opt').all();
          if (opts.length) await opts[exerciseCount % opts.length].click();
        }
        await checkBtn.click({ timeout: 5000 });
        await page.waitForTimeout(200);
      } else {
        await checkBtn.click({ timeout: 5000 }); // Continue
        await page.waitForTimeout(200);
      }
    } catch (e) {
      console.log('CLICK_FAILED at exercise', exerciseCount, ':', e.message.split('\n')[0]);
      await page.screenshot({ path: `/tmp/e2e_FAIL_ex${exerciseCount}.png` });
      const html = await page.content();
      require('fs').writeFileSync(`/tmp/e2e_FAIL_ex${exerciseCount}.html`, html);
      throw e;
    }
  }

  await page.waitForSelector('#done:not(.hidden)', { timeout: 5000 });
  await page.screenshot({ path: '/tmp/e2e_04_lesson_done.png' });
  console.log('LESSON_COMPLETE after', exerciseCount, 'exercises');

  const missionText = await page.locator('#missionBox').textContent();
  console.log('MISSION_BOX:', missionText.replace(/\s+/g, ' ').trim());
  await page.click('#missionBtn');
  await page.waitForTimeout(300);
  const missionBtnText = await page.locator('#missionBtn').textContent();
  console.log('MISSION_BTN_AFTER_CLICK:', missionBtnText);

  // Rehearsal mode
  await page.click('button:has-text("Rehearse This Lesson")');
  await page.waitForTimeout(300);
  const rehearsalClass = (await page.locator('#rehearsal').getAttribute('class')) || '';
  console.log('REHEARSAL_VISIBLE:', !rehearsalClass.includes('hidden'));
  await page.screenshot({ path: '/tmp/e2e_rehearsal.png' });
  const recordBtn = page.locator('#recordBtn');
  if (await recordBtn.count()) {
    await recordBtn.dispatchEvent('mousedown');
    await page.waitForTimeout(500);
    await recordBtn.dispatchEvent('mouseup');
    await page.waitForTimeout(500);
    console.log('REHEARSAL_RECORD_OK');
  } else {
    console.log('REHEARSAL_MIC_FALLBACK_SHOWN');
  }
  for (let i = 0; i < 10; i++) {
    const nextBtn = page.locator('#nextBtn, #finishRehearsalBtn');
    if (await nextBtn.count() === 0) break;
    await nextBtn.first().click();
    await page.waitForTimeout(300);
    if (await page.locator('#main:not(.hidden)').count()) break;
  }
  await page.waitForSelector('#main:not(.hidden)', { timeout: 5000 });
  console.log('BACK_TO_MAIN');

  // Phrasebook
  await page.click('#nPhrasebook');
  await page.waitForTimeout(300);
  await page.screenshot({ path: '/tmp/e2e_05_phrasebook.png' });
  const pbCount = await page.locator('#pbList > div').count();
  console.log('PHRASEBOOK_ITEMS:', pbCount);
  if (pbCount > 0) {
    await page.locator('#pbList button').first().click();
    await page.waitForTimeout(200);
    console.log('PHRASEBOOK_AUDIO_CLICK_OK');
  }

  // Profile
  await page.click('#nProfile');
  await page.waitForTimeout(300);
  await page.screenshot({ path: '/tmp/e2e_06_profile.png' });
  const xpText = await page.locator('#pXp').textContent();
  const milestoneCount = await page.locator('#pMilestones').textContent();
  const milestoneLog = await page.locator('#milestoneLog').textContent();
  console.log('PROFILE_XP:', xpText, 'MILESTONES:', milestoneCount);
  console.log('MILESTONE_LOG:', milestoneLog.replace(/\s+/g, ' ').trim().slice(0, 200));

  console.log('CONSOLE_ERRORS:', errors.length ? JSON.stringify(errors) : 'none');

  await browser.close();
})().catch(e => { console.error('TEST_CRASHED:', e.message); process.exit(1); });
