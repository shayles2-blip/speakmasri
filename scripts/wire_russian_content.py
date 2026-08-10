#!/usr/bin/env python3
"""Wire scripts/translatable_content_ru.json into index.html.

Run once against the Phase 1 index.html. The strict replacements intentionally
fail if the source markup has drifted, so a partial localization is never saved.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
TRANSLATIONS = ROOT / "scripts" / "translatable_content_ru.json"


def js_string(value):
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def replace_once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one source match, found {count}")
    return source.replace(old, new, 1)


data = json.loads(TRANSLATIONS.read_text())
source = INDEX.read_text()

# COURSE titles are uniquely addressable by id. Preserve the compact literal.
for group, field in ((data["unitTitles"], "unit"), (data["lessonTitles"], "lesson")):
    for row in group:
        old = f'{{id:{js_string(row["id"])},title:{js_string(row["title"])}'
        new = old + f',title_ru:{js_string(row["title_ru"])}'
        source = replace_once(source, old, new, f'{field} title {row["id"]}')

# Each lesson occupies one source line. Match vocab by lesson id + array index,
# while verifying its English source text before inserting after register/franco.
vocab_by_lesson = {}
for row in data["vocab"]:
    vocab_by_lesson.setdefault(row["lessonId"], []).append(row)
for lesson_id, rows in vocab_by_lesson.items():
    rows.sort(key=lambda row: row["idx"])
    line_pattern = re.compile(rf'(?m)^.*\{{id:{re.escape(js_string(lesson_id))},title:.*$')
    match = line_pattern.search(source)
    if not match:
        raise RuntimeError(f"vocab lesson not found: {lesson_id}")
    line = match.group(0)
    objects = list(re.finditer(r'\{en:"(?:\\.|[^"\\])*",ar:"(?:\\.|[^"\\])*",franco:"(?:\\.|[^"\\])*"(?:,register:"(?:\\.|[^"\\])*")?\}', line))
    if len(objects) != len(rows) or [row["idx"] for row in rows] != list(range(len(rows))):
        raise RuntimeError(f"vocab shape mismatch for {lesson_id}: HTML={len(objects)}, JSON={len(rows)}")
    updated = line
    for obj_match, row in reversed(list(zip(objects, rows))):
        obj = obj_match.group(0)
        en_match = re.search(r'^\{en:("(?:\\.|[^"\\])*")', obj)
        if json.loads(en_match.group(1)) != row["en"]:
            raise RuntimeError(f'English mismatch at {lesson_id}[{row["idx"]}]')
        insertion = f',ru:{js_string(row["ru"])}'
        updated_obj = obj[:-1] + insertion + '}'
        updated = updated[:obj_match.start()] + updated_obj + updated[obj_match.end():]
    source = source[:match.start()] + updated + source[match.end():]

# Static HTML uses data attributes consumed by applyStaticStrings(). Text nodes
# that share a parent with a dynamic number get a small dedicated span.
static_replacements = [
    ('<title>SpeakMasri – Learn Egyptian Arabic (Masri)</title>', '<title>SpeakMasri – Learn Egyptian Arabic (Masri)</title>'),
    ('role="group" aria-label="Base language" style="margin-bottom:12px"', 'role="group" aria-label="Base language" data-i18n-aria-label="settings.base_language" style="margin-bottom:12px"'),
    ('<p class="landing-in landing-in-3" style="color:var(--ink-soft);margin:8px 0 20px;font-size:15px">Learn <b>Egyptian Arabic (Masri)</b> through short, practical lessons built around real-life situations. <strong>Try a lesson free — no account needed.</strong></p>', '<p class="landing-in landing-in-3" style="color:var(--ink-soft);margin:8px 0 20px;font-size:15px"><span data-i18n="nav.learn">Learn</span> <b data-i18n="ui.egyptian_arabic_masri">Egyptian Arabic (Masri)</b> <span data-i18n="ui.through_short_practical_lessons_built_around_real_li">through short, practical lessons built around real-life situations.</span> <strong data-i18n="ui.try_a_lesson_free_no_account_needed">Try a lesson free — no account needed.</strong></p>'),
    ('<button class="btn btn-sheen landing-in landing-in-5" onclick="startGuestLesson()">Try a Lesson Free</button>', '<button class="btn btn-sheen landing-in landing-in-5" onclick="startGuestLesson()" data-i18n="btn.try_lesson_free">Try a Lesson Free</button>'),
    ('onclick="showLogin()" style=', 'onclick="showLogin()" data-i18n="btn.login" style='),
    ('onclick="showSignup()" style=', 'onclick="showSignup()" data-i18n="btn.signup" style='),
    ('<button id="signupSubmit" class="btn hidden" onclick="signup()">Sign Up</button>', '<button id="signupSubmit" class="btn hidden" onclick="signup()" data-i18n="btn.signup">Sign Up</button>'),
    ('<button id="loginSubmit" class="btn btn-ghost hidden" onclick="login()">Log In</button>', '<button id="loginSubmit" class="btn btn-ghost hidden" onclick="login()" data-i18n="btn.login">Log In</button>'),
    ('id="name" placeholder="Name (for signup)"', 'id="name" placeholder="Name (for signup)" data-i18n-placeholder="placeholder.name"'),
    ('id="email" placeholder="Email"', 'id="email" placeholder="Email" data-i18n-placeholder="placeholder.email"'),
    ('id="pass" placeholder="Password (min 8 characters)"', 'id="pass" placeholder="Password (min 8 characters)" data-i18n-placeholder="placeholder.pass"'),
    ('<option value="">What\'s your learning goal? (optional)</option>', '<option value="" data-i18n="ui.what_s_your_learning_goal_optional">What\'s your learning goal? (optional)</option>'),
    ('<option value="partner">Egyptian partner / in-laws</option>', '<option value="partner" data-i18n="ui.egyptian_partner_in_laws">Egyptian partner / in-laws</option>'),
    ('<option value="traveler">Upcoming trip to Egypt</option>', '<option value="traveler" data-i18n="ui.upcoming_trip_to_egypt">Upcoming trip to Egypt</option>'),
    ('<option value="heritage">Reconnecting with heritage</option>', '<option value="heritage" data-i18n="ui.reconnecting_with_heritage">Reconnecting with heritage</option>'),
    ('<option value="other">Other</option>', '<option value="other" data-i18n="ui.other">Other</option>'),
    ('onclick="backToChoice()" style=', 'onclick="backToChoice()" data-i18n="ui.back" style='),
    ('onclick="resetPassword()" style=', 'onclick="resetPassword()" data-i18n="ui.forgot_password" style='),
    ('<a href="privacy.html" style="color:var(--ink-soft)">Privacy Policy</a>', '<a href="privacy.html" style="color:var(--ink-soft)" data-i18n="ui.privacy_policy">Privacy Policy</a>'),
    ('<a href="terms.html" style="color:var(--ink-soft)">Terms of Service</a>', '<a href="terms.html" style="color:var(--ink-soft)" data-i18n="ui.terms_of_service">Terms of Service</a>'),
    ('<span id="milestoneCount">0</span> said', '<span id="milestoneCount">0</span> <span data-i18n="ui.said">said</span>'),
    ('<span style="flex:1">Verify your email to secure your account</span>', '<span style="flex:1" data-i18n="ui.verify_your_email_to_secure_your_account">Verify your email to secure your account</span>'),
    ('id="resendVerificationBtn" type="button"', 'id="resendVerificationBtn" type="button" data-i18n="ui.resendverificationbtn"'),
    ('aria-label="Dismiss email verification reminder"', 'aria-label="Dismiss email verification reminder" data-i18n-aria-label="aria.dismiss_email_verification_reminder"'),
    ('<h2>📖 Phrasebook</h2>', '<h2 data-i18n="ui.phrasebook">📖 Phrasebook</h2>'),
    ('<p style="padding:0 16px 12px;color:var(--ink-soft)">Everything you\'ve unlocked so far — pull this up mid-conversation.</p>', '<p style="padding:0 16px 12px;color:var(--ink-soft)" data-i18n="ui.everything_you_ve_unlocked_so_far_pull_this_up_mid_c">Everything you\'ve unlocked so far — pull this up mid-conversation.</p>'),
    ('<p style="padding:0 16px 12px;color:var(--ink-soft);font-size:12px">Formal = elders, in-laws, show respect · Casual = friends, peers · Intimate = partner only</p>', '<p style="padding:0 16px 12px;color:var(--ink-soft);font-size:12px" data-i18n="ui.formal_elders_in_laws_show_respect_casual_friends_pe">Formal = elders, in-laws, show respect · Casual = friends, peers · Intimate = partner only</p>'),
    ('id="pXp">0</div>Total XP</div>', 'id="pXp">0</div><span data-i18n="ui.total_xp">Total XP</span></div>'),
    ('id="pMilestones">0</div>Phrases Said</div>', 'id="pMilestones">0</div><span data-i18n="ui.phrases_said">Phrases Said</span></div>'),
    ('<div style="font-weight:800;margin-bottom:8px">Your moments</div>', '<div style="font-weight:800;margin-bottom:8px" data-i18n="ui.your_moments">Your moments</div>'),
    ('<div style="font-weight:800;margin-bottom:4px">Partner Phrases</div>', '<div style="font-weight:800;margin-bottom:4px" data-i18n="ui.partner_phrases">Partner Phrases</div>'),
    ('<p style="color:var(--ink-soft);font-size:13px;margin-bottom:10px">Send your partner this link — they add family names, in-jokes, whatever they\'d actually say, right from their phone. No account needed for them.</p>', '<p style="color:var(--ink-soft);font-size:13px;margin-bottom:10px" data-i18n="ui.send_your_partner_this_link_they_add_family_names_in">Send your partner this link — they add family names, in-jokes, whatever they\'d actually say, right from their phone. No account needed for them.</p>'),
    ('id="shareLinkBtn" style=', 'id="shareLinkBtn" data-i18n="ui.sharelinkbtn" style='),
    ('<summary style="color:var(--ink-soft);font-size:13px;cursor:pointer">Prefer the JSON file instead?</summary>', '<summary style="color:var(--ink-soft);font-size:13px;cursor:pointer" data-i18n="ui.prefer_the_json_file_instead">Prefer the JSON file instead?</summary>'),
    ('onclick="downloadPhraseTemplate()">⬇️ Template</button>', 'onclick="downloadPhraseTemplate()" data-i18n="ui.template">⬇️ Template</button>'),
    ('<label class="btn btn-ghost" style="font-size:13px;padding:10px;text-align:center;cursor:pointer">\n              ⬆️ Import', '<label class="btn btn-ghost" style="font-size:13px;padding:10px;text-align:center;cursor:pointer">\n              <span data-i18n="ui.import">⬆️ Import</span>'),
    ('<div style="font-weight:800;margin-bottom:8px">Account</div>', '<div style="font-weight:800;margin-bottom:8px" data-i18n="ui.account">Account</div>'),
    ('id="editNameBtn" onclick=', 'id="editNameBtn" data-i18n="ui.editnamebtn" onclick='),
    ('id="nameEditInput" maxlength="40" placeholder="Your name"', 'id="nameEditInput" maxlength="40" placeholder="Your name" data-i18n-placeholder="placeholder.your_name"'),
    ('id="saveNameBtn" style=', 'id="saveNameBtn" data-i18n="ui.savenamebtn" style='),
    ('onclick="hideNameEdit()">Cancel</button>', 'onclick="hideNameEdit()" data-i18n="ui.cancel">Cancel</button>'),
    ('onclick="changePasswordFromProfile()" style=', 'onclick="changePasswordFromProfile()" data-i18n="ui.change_password" style='),
    ('<div style="font-weight:800;margin:12px 0 8px">Base language</div>', '<div style="font-weight:800;margin:12px 0 8px" data-i18n="settings.base_language">Base language</div>'),
    ('<div class="lang-toggle" role="group" aria-label="Base language">', '<div class="lang-toggle" role="group" aria-label="Base language" data-i18n-aria-label="settings.base_language">'),
    ('<button class="btn btn-ghost" onclick="logout()">Log Out</button>', '<button class="btn btn-ghost" onclick="logout()" data-i18n="btn.logout">Log Out</button>'),
    ('id="nLearn" onclick="tab(\'learn\')" aria-label="Learn"', 'id="nLearn" onclick="tab(\'learn\')" aria-label="Learn" data-i18n-aria-label="nav.learn"'),
    ('id="nPhrasebook" onclick="tab(\'phrasebook\')" aria-label="Phrasebook"', 'id="nPhrasebook" onclick="tab(\'phrasebook\')" aria-label="Phrasebook" data-i18n-aria-label="nav.phrasebook"'),
    ('id="nProfile" onclick="tab(\'profile\')" aria-label="Profile"', 'id="nProfile" onclick="tab(\'profile\')" aria-label="Profile" data-i18n-aria-label="nav.profile"'),
    ('onclick="quitLesson()" aria-label="Quit lesson"', 'onclick="quitLesson()" aria-label="Quit lesson" data-i18n-aria-label="aria.quit_lesson"'),
    ('id="checkBtn" onclick="check()" disabled>Check</button>', 'id="checkBtn" onclick="check()" disabled data-i18n="btn.check">Check</button>'),
    ('<h1 id="doneTitle">Lesson Complete!</h1>', '<h1 id="doneTitle" data-i18n="ui.donetitle">Lesson Complete!</h1>'),
    ('id="dXp">+10</div>XP Earned</div>', 'id="dXp">+10</div><span data-i18n="ui.xp_earned">XP Earned</span></div>'),
    ('id="dAcc">100%</div>Accuracy</div>', 'id="dAcc">100%</div><span data-i18n="ui.accuracy">Accuracy</span></div>'),
    ('<button class="btn btn-ghost" onclick="startRehearsal()">🎙️ Rehearse This Lesson</button>', '<button class="btn btn-ghost" onclick="startRehearsal()" data-i18n="ui.rehearse_this_lesson">🎙️ Rehearse This Lesson</button>'),
    ('<button class="btn" onclick="finishLesson()">Continue</button>', '<button class="btn" onclick="finishLesson()" data-i18n="btn.continue">Continue</button>'),
]
for old, new in static_replacements:
    if old != new:
        source = replace_once(source, old, new, old[:60])

# Generate the complete dictionary next to the Phase 1 helpers.
entries = []
for row in data["uiStrings"]:
    entries.append(f'  {js_string(row["key"])}:{{en:{js_string(row["text"])},ru:{js_string(row["ru"])}}}')
strings_block = "const STRINGS={\n" + ",\n".join(entries) + "\n};\nfunction t(key){\n  const entry=STRINGS[key];\n  if(!entry)return key;\n  return (baseLang!=='en'&&entry[baseLang])?entry[baseLang]:entry.en;\n}\nfunction applyStaticStrings(){\n  document.title=t('ui.speakmasri_learn_egyptian_arabic_masri');\n  document.documentElement.lang=baseLang;\n  document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n);});\n  document.querySelectorAll('[data-i18n-placeholder]').forEach(el=>{el.placeholder=t(el.dataset.i18nPlaceholder);});\n  document.querySelectorAll('[data-i18n-aria-label]').forEach(el=>{el.setAttribute('aria-label',t(el.dataset.i18nAriaLabel));});\n}\n\n"
anchor = "function vocabText(item){return (baseLang!=='en'&&item[baseLang])?item[baseLang]:item.en;}\n"
source = replace_once(source, anchor, strings_block + anchor, "STRINGS insertion point")
source = replace_once(source, "  renderBaseLangToggles();\n  if(refreshLandingPhrase)", "  renderBaseLangToggles();\n  applyStaticStrings();\n  if(refreshLandingPhrase)", "setBaseLang static refresh")
source = replace_once(source, "renderBaseLangToggles();\nif(\"speechSynthesis\"", "renderBaseLangToggles();\napplyStaticStrings();\nif(\"speechSynthesis\"", "bootstrap static refresh")
source = replace_once(source, "  renderBaseLangToggles();\n}\n\nasync function saveProgress", "  renderBaseLangToggles();\n  applyStaticStrings();\n}\n\nasync function saveProgress", "loaded preference static refresh")

# Dynamic UI strings. Replacements are deliberately precise and every key is
# subsequently checked for a reference outside STRINGS.
dynamic = {
"ui.name_can_t_be_empty": [("msg.textContent=\"Name can't be empty.\"", "msg.textContent=t('ui.name_can_t_be_empty')")],
"ui.saved": [("btn.textContent='Saved ✓'", "btn.textContent=t('ui.saved')")],
"ui.couldn_t_save_try_again": [("msg.textContent=\"Couldn't save. Try again.\"", "msg.textContent=t('ui.couldn_t_save_try_again')")],
"ui.no_email_on_file": [("pwMsg.textContent='No email on file.'", "pwMsg.textContent=t('ui.no_email_on_file')")],
"ui.check_your_email_for_a_reset_link": [("pwMsg.textContent='Check your email for a reset link.'", "pwMsg.textContent=t('ui.check_your_email_for_a_reset_link')"), ("msg.textContent=\"Check your email for a reset link.\"", "msg.textContent=t('ui.check_your_email_for_a_reset_link')")],
"ui.couldn_t_send_reset_email_try_again": [("pwMsg.textContent=\"Couldn't send reset email. Try again.\"", "pwMsg.textContent=t('ui.couldn_t_send_reset_email_try_again')")],
"ui.fill_in_all_fields_to_sign_up": [("err.textContent=\"Fill in all fields to sign up.\"", "err.textContent=t('ui.fill_in_all_fields_to_sign_up')")],
"ui.password_must_be_at_least_8_characters": [("err.textContent=\"Password must be at least 8 characters.\"", "err.textContent=t('ui.password_must_be_at_least_8_characters')")],
"ui.enter_your_email_above_first_then_tap_forgot_passwor": [("err.textContent=\"Enter your email above first, then tap Forgot password.\"", "err.textContent=t('ui.enter_your_email_above_first_then_tap_forgot_passwor')")],
"ui.copied": [("btn.textContent=\"Copied! ✅\"", "btn.textContent=t('ui.copied')")],
"ui.sent": [("btn.textContent=\"Sent! ✅\"", "btn.textContent=t('ui.sent')")],
"exercise.listen_prompt": [("q.textContent=\"Listen and choose the meaning\"", "q.textContent=t('exercise.listen_prompt')")],
"exercise.franco_prompt": [("q.textContent=\"Type it in Franco-Arabic\"", "q.textContent=t('exercise.franco_prompt')")],
"ui.e_g_shukran": [("inp.placeholder=\"e.g. Shukran\"", "inp.placeholder=t('ui.e_g_shukran')")],
"exercise.match_prompt": [("q.textContent=\"Match the pairs\"", "q.textContent=t('exercise.match_prompt')")],
"btn.check": [("checkBtn.textContent=\"Check\"", "checkBtn.textContent=t('btn.check')")],
"btn.continue": [("checkBtn.textContent=\"Continue\"", "checkBtn.textContent=t('btn.continue')")],
"ui.recording": [("btn.textContent='🔴 Recording...'", "btn.textContent=t('ui.recording')")],
"ui.hold_to_record": [("if(btn)btn.textContent='🎙️ Hold to Record'", "if(btn)btn.textContent=t('ui.hold_to_record')")],
"ui.nice": [("btn.textContent=\"Nice! 🎉\"", "btn.textContent=t('ui.nice')")],
"ui.nice_sign_up_to_save_this_progress": [("document.getElementById(\"doneTitle\").textContent=\"Nice! Sign up to save this progress\"", "document.getElementById(\"doneTitle\").textContent=t('ui.nice_sign_up_to_save_this_progress')")],
"ui.donetitle": [("document.getElementById(\"doneTitle\").textContent=\"Lesson Complete!\"", "document.getElementById(\"doneTitle\").textContent=t('ui.donetitle')")],
"msg.that_file_couldn_t_be_read_as_a_phrase_list_make_sur": [("alert(\"That file couldn't be read as a phrase list. Make sure it's the JSON template with en/ar/franco fields.\")", "alert(t('msg.that_file_couldn_t_be_read_as_a_phrase_list_make_sur'))")],
"msg.quit_this_lesson_you_ll_lose_your_progress_in_it": [("confirm(\"Quit this lesson? You'll lose your progress in it.\")", "confirm(t('msg.quit_this_lesson_you_ll_lose_your_progress_in_it'))")],
"register.formal": [("formal:{label:'Formal'", "formal:{label:t('register.formal')")],
"register.casual": [("casual:{label:'Casual'", "casual:{label:t('register.casual')")],
"register.intimate": [("intimate:{label:'Intimate'", "intimate:{label:t('register.intimate')")],
"msg.this_email_is_already_registered": [("'auth/email-already-in-use':'This email is already registered.'", "'auth/email-already-in-use':t('msg.this_email_is_already_registered')")],
"msg.incorrect_password": [("'auth/wrong-password':'Incorrect password.'", "'auth/wrong-password':t('msg.incorrect_password')")],
"msg.invalid_email_or_password": [("'auth/invalid-credential':'Invalid email or password.'", "'auth/invalid-credential':t('msg.invalid_email_or_password')")],
"msg.password_should_be_at_least_6_characters": [("'auth/weak-password':'Password should be at least 6 characters.'", "'auth/weak-password':t('msg.password_should_be_at_least_6_characters')")],
"msg.please_enter_a_valid_email_address": [("'auth/invalid-email':'Please enter a valid email address.'", "'auth/invalid-email':t('msg.please_enter_a_valid_email_address')")],
"msg.no_account_found_with_this_email": [("'auth/user-not-found':'No account found with this email.'", "'auth/user-not-found':t('msg.no_account_found_with_this_email')")],
"msg.something_went_wrong_please_try_again": [("return map[code]||'Something went wrong. Please try again.'", "return map[code]||t('msg.something_went_wrong_please_try_again')")],
"ui.copy_this_link_to_send_your_partner": [("prompt(\"Copy this link to send your partner:\",url)", "prompt(t('ui.copy_this_link_to_send_your_partner'),url)")],
"msg.no_moments_yet_finish_a_lesson_and_try_the_mission_t": [("log.innerHTML='<p style=\"color:var(--ink-soft)\">No moments yet — finish a lesson and try the mission tonight.</p>'", "log.innerHTML=`<p style=\"color:var(--ink-soft)\">${t('msg.no_moments_yet_finish_a_lesson_and_try_the_mission_t')}</p>`")],
"msg.no_partner_phrases_yet": [("listEl.innerHTML='<p style=\"color:var(--ink-soft);font-size:13px\">No partner phrases yet.</p>'", "listEl.innerHTML=`<p style=\"color:var(--ink-soft);font-size:13px\">${t('msg.no_partner_phrases_yet')}</p>`")],
"aria.delete_phrase": [("del.setAttribute(\"aria-label\",\"Delete phrase\")", "del.setAttribute(\"aria-label\",t('aria.delete_phrase'))")],
"msg.nothing_unlocked_yet_finish_your_first_lesson": [("list.innerHTML='<p style=\"padding:16px;color:var(--ink-soft)\">Nothing unlocked yet — finish your first lesson.</p>'", "list.innerHTML=`<p style=\"padding:16px;color:var(--ink-soft)\">${t('msg.nothing_unlocked_yet_finish_your_first_lesson')}</p>`")],
"exercise.translate_prompt": [("q.textContent=\"Translate: \\\"\"+ex.q+\"\\\"\"", "q.textContent=t('exercise.translate_prompt')+' \\\"'+ex.q+'\\\"'")],
"ui.correct": [("${ok?\"Correct! ✅\":\"Not quite ❌\"}", "${ok?t('ui.correct')+' ✅':t('ui.not_quite')+' ❌'}")],
"ui.answer": [("<div>Answer: <b>${answerText}</b></div>", "<div>${t('ui.answer')} <b>${answerText}</b></div>")],
"ui.tonight_s_mission": [("🎯 Tonight's mission</div>", "🎯 ${t('ui.tonight_s_mission')}</div>")],
"ui.say_this_to_them": [("<div>Say this to them: <span", "<div>${t('ui.say_this_to_them')} <span")],
"ui.i_said_it": [(">I said it! ✅</button>`", ">${t('ui.i_said_it')} ✅</button>`")],
"ui.finish": [("${rehearsalIdx===rehearsalPack.length-1?'Finish':'Next'}", "${rehearsalIdx===rehearsalPack.length-1?t('ui.finish'):t('ui.next')}")],
"aria.hear_native_pronunciation": [("aria-label=\"Hear native pronunciation\"", "aria-label=\"${t('aria.hear_native_pronunciation')}\"")],
"aria.hold_to_record_yourself": [("aria-label=\"Hold to record yourself\"", "aria-label=\"${t('aria.hold_to_record_yourself')}\"")],
"ui.hold_to_record": [(">🎙️ Hold to Record</button>`", ">${t('ui.hold_to_record')}</button>`")],
"ui.mic_access_not_available_just_practice_saying_it_out": [(">Mic access not available — just practice saying it out loud</p>`", ">${t('ui.mic_access_not_available_just_practice_saying_it_out')}</p>`")],
"ui.all_done": [("<h2>All done! 🎉</h2>", "<h2>${t('ui.all_done')} 🎉</h2>")],
"msg.you_ve_practiced_the_whole_lesson": [("<p style=\"color:var(--ink-soft)\">You've practiced the whole lesson.</p>", "<p style=\"color:var(--ink-soft)\">${t('msg.you_ve_practiced_the_whole_lesson')}</p>")],
"ui.back_to_lessons": [(">Back to lessons</button>", ">${t('ui.back_to_lessons')}</button>")],
"demo.phrase.my_love": [("{ ar: \"حبيبي\", franco: \"Habibi\", en: \"My love\" }", "{ ar: \"حبيبي\", franco: \"Habibi\", en: \"My love\", ru:STRINGS['demo.phrase.my_love'].ru }")],
"demo.phrase.how_are_you": [("{ ar: \"إزيك\", franco: \"Ezzayak\", en: \"How are you\" }", "{ ar: \"إزيك\", franco: \"Ezzayak\", en: \"How are you\", ru:STRINGS['demo.phrase.how_are_you'].ru }")],
}
for key, replacements in dynamic.items():
    for old, new in replacements:
        source = replace_once(source, old, new, key)

# Keys handled statically are present as data attributes; dynamic keys use t().
# ui.not_quite and ui.next share a conditional replacement with their paired key.
dictionary_end = source.index("};\nfunction t(key)", source.index("const STRINGS={"))
without_dictionary = source[:source.index("const STRINGS={")] + source[dictionary_end + 3:]
missing = [row["key"] for row in data["uiStrings"] if row["key"] not in without_dictionary]
if missing:
    raise RuntimeError(f"UI keys not wired outside STRINGS: {missing}")

INDEX.write_text(source)
print(f'Wired {len(data["vocab"])} vocab, {len(data["lessonTitles"])} lessons, '
      f'{len(data["unitTitles"])} units, and {len(data["uiStrings"])} UI strings.')
