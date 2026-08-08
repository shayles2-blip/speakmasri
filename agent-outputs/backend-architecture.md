**Supabase** (supabase.com). It gives you a real PostgreSQL database, built-in secure auth, and a client-side JS SDK you can load as a single `<script>` tag in your static HTML — no build step, no server to manage. The free tier is generous and the relational model maps cleanly to your current users / progress / phrases data, unlike NoSQL which would force awkward nesting or denormalization. It also has Row Level Security so each user can only touch their own data, which keeps the app safe without you writing any server code.

---

### Concrete Schema (replaces localStorage)

All tables live in the `public` schema. The authenticated user’s ID from Supabase Auth is a UUID, used as the primary owner everywhere.

**1. `profiles`** (extends the built-in auth.users)  
- `id` (uuid, primary key, references `auth.users(id)`)  
- `email` (text)  
- `name` (text)  
- `motivation` (text)  
- `xp` (integer, default 0)  
- `created_at` (timestamptz, default now())  

*Why:* One row per user. Supabase can auto‑create this row when a new user signs up (via a trigger on `auth.users`).

**2. `user_milestones`**  
- `user_id` (uuid, references `profiles(id)`)  
- `milestone_name` (text, e.g. `'lesson1_complete'`)  
- `achieved_at` (timestamptz, default now())  
- **Primary key:** (`user_id`, `milestone_name`)  

*Why:* This is how you track which milestones a user has hit. A row exists ⇔ the milestone is achieved. No need for a separate `completed` boolean.

**3. `custom_phrases`**  
- `id` (bigserial, primary key)  
- `user_id` (uuid, references `profiles(id)`)  
- `phrase` (text, not null)  
- `translation` (text, not null)  
- `created_at` (timestamptz, default now())  

*Why:* One row per saved phrase. A user can have many phrases. `bigserial` gives you a simple auto‑increment ID.

---

### Authentication Approach

Use **Supabase Auth’s built‑in email/password sign‑up and sign‑in**.  
- The frontend calls `supabase.auth.signUp({ email, password })` and `supabase.auth.signInWithPassword({ email, password })`.  
- Passwords are **never stored in your database** – Supabase hashes them (bcrypt) and stores the hash in its internal `auth.users` table, which you never touch.  
- After sign‑up, you’ll use a database trigger (provided by Supabase) to automatically insert a new row into `public.profiles` with the new user’s UUID and email. The `name`, `motivation`, and `xp` can be set later via an `update`.  
- Row Level Security (RLS) policies ensure that when the frontend fetches data (e.g., `supabase.from('user_milestones').select()`), the result automatically contains only rows belonging to the logged‑in user – you don’t write any filter logic. Example policy on `user_milestones`:  
  ```sql
  ALTER TABLE user_milestones ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "Users own their milestones" ON user_milestones
    FOR ALL USING (auth.uid() = user_id);
  ```

---

### Frontend Changes (High Level)

The app remains a **single static HTML file** hosted on GitHub Pages.  
1. **Load the Supabase client**: Add a `<script>` tag from CDN, e.g.  
   `<script src="https://unpkg.com/@supabase/supabase-js@2"></script>`.  
2. **Initialize the client** with your project URL and public (anon) key – both safe to expose.  
3. **On page load**, replace all `localStorage` reads with an API call:  
   - Check for an existing session: `supabase.auth.getSession()`.  
   - If logged in, fetch profile + milestones + custom phrases:  
     ```js
     const { data: profile } = await supabase.from('profiles').select('*').single();
     const { data: milestones } = await supabase.from('user_milestones').select('milestone_name');
     const { data: phrases } = await supabase.from('custom_phrases').select('*');
     ```  
4. **For writes** (complete milestone, add phrase, update XP/motivation), use `supabase.from(...).upsert(...)`, `.insert(...)`, or `.update(...)` – the client handles auth tokens automatically.  
5. **Remove all plaintext password handling** – no more `localStorage` user object with a `password` field.  
6. The static file is still served by GitHub Pages; all API calls go directly to `https://<project-id>.supabase.co`, allowed by CORS.

No build step, no Node server, no other library necessary.

---

### Free-Tier Limits & When It Costs Money

Supabase **Free Plan** gives you:  
- **Database**: 500 MB (plenty for hundreds of thousands of profile/milestone/phrase rows).  
- **Auth**: 50,000 monthly active users.  
- **Bandwidth**: 2 GB/month.  
- **API requests**: unlimited, but rate‑limited (the free tier is generous for a side project).  

You will **start paying only if** you exceed 50k monthly active users **or** 2 GB bandwidth **or** 500 MB database storage. For a solo-founder side project, that’s comfortably unlikely – you can stay free for a very long time. The first paid plan is $25/month if you ever need to scale up.
