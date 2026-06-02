# AI Scam Shield — 15-Minute Defense Script (Simple Words)

**Presenter:** Yoeurn Yan · **Advisor:** Mr. Chhim Bunchhun · **RUPP**

**Time plan (15:00):**
- **Slides:** 0:00 – 7:00 (about 7 minutes)
- **Live demo:** 7:00 – 10:00 (3 minutes)
- **Questions:** 10:00 – 15:00 (5 minutes)

**How to talk:** Slow and clear. Short sentences. On the "divider" slides (10, 13, 15, 17, 19), just say one line and move on.

---

## SLIDES — 0:00 to 7:00

### [0:00–0:25] Slide 1 — Title
> Good morning, everyone. My name is Yoeurn Yan. My project is called **AI Scam Shield**. It is a phone app that uses smart computer learning to catch bad messages — spam, fake links, and scam phone calls. My advisor is Mr. Chhim Bunchhun. Today I will show you the problem, how I built the app, what I found, and then I will show it working on a real phone.

### [0:25–0:35] Slide 2 — Contents
> Here is my plan for today: first the problem, then what others have done, then how I built it, then my results, and at the end, a live test on a phone.

### [0:35–1:05] Slide 3 — Introduction
> These days, bad messages are everywhere. In Cambodia, people get scam text messages and fake links every single day. The old way of blocking them only catches messages it has seen before. Scammers keep changing their tricks, so the old way misses them. We need something smarter — something that can **learn**.

### [1:05–1:35] Slide 4 — The Problem
> Here are the real problems. More scams are hitting people on their phones. The old blockers miss clever tricks that fool people. There is no easy tool for normal Cambodians to check if a message is safe. **Scam phone calls are growing, but almost no tool listens to a call and checks it.** And people keep getting tricked by fake company names and fake links.

### [1:35–2:05] Slide 5 — My Goal
> My goal is simple: build a phone app that can spot scams in **both written messages and voice**, and do it very accurately. To do that, I set five targets — catch scams instantly, find fake links and fake brands, check both text and voice, keep the app easy to use, and save a history so people can look back.

### [2:05–2:25] Slide 6 — What It Covers
> A few honest notes on scope. It is a phone app for iPhone and Android. It is made for normal people, not big companies. Right now it reads **English** — Khmer is my next step. And it needs internet, because the smart part runs on a server.

### [2:25–2:55] Slide 7 — What the App Does
> The app does six things. One: it checks text messages for spam. Two: for voice, it **turns the speech into words, then checks those words**. Three: it checks links for fake brands. Four: it can watch your email inbox and catch bad mail by itself. Five: it shows everything on one simple safety screen. And six — the best part — **it learns from you. When you tell it "this was wrong," it gets better over time.**

### [2:55–3:25] Slide 8 — What Others Have Done
> I studied past research. Other people built scam catchers before, and they got good scores — around 92 to 98 out of 100. But most of them were big, heavy programs made for computers, not phones. So I asked one question: **can a small, light, simple model do just as well — small enough to work on a phone?**

### [3:25–3:50] Slide 9 — The Tools I Used
> Here are the tools. The app itself is built with **Flutter**, so it works on both iPhone and Android. Behind it, a server keeps everything safe and logged in. And a second part — the "brain" — is where the smart checking happens. Think of it as three simple layers: the app you touch, the server that connects, and the brain that decides.

### [3:50–4:25] Slides 10–11 — My Data
*(Slide 10 is just a section title — say one line, then go to 11.)*
> To make the app smart, I had to teach it with examples. I used **three clean sets of examples** — about 14,600 in total. The biggest was text spam, then fake links, then scam phone calls. Each set was **balanced** — half good, half bad — so the app learns both sides fairly. I kept the sets small but very clean, because **clean examples teach better than messy ones.** I also used a fixed setup so anyone can repeat my work and get the same result.

### [4:25–4:45] Slide 12 — What Each Example Looks Like
> Each example is simple: a piece of text, and a label that says "safe" or "scam." That's it. The app learns the difference between the two.

### [4:45–5:25] Slides 13–14 — The Three Brains
*(Slide 13 is a section title — one line: "The app also keeps learning from people's feedback.")*
> I did not build one big brain. I built **three small expert brains**, each good at one job. One expert checks text messages — it is fast and scored about 99 out of 100. One expert checks scam calls. And one expert checks fake links. Using three small experts works better than one brain trying to do everything.

### [5:25–5:50] Slides 15–17 — How It Reads a Message
*(Slides 15 and 17 are section titles — cover both in two lines.)*
> Here is the simple idea. The computer cannot read words like we do, so the app **turns words into numbers**. Rare, suspicious words get a high score; normal everyday words get a low score. For voice, the app **first writes down what was said, then checks those written words** — so voice uses the very same method as text. That trick is what made voice possible.

### [5:50–6:05] Slide 18 — How the App Asks the Brain
> When the app checks a message, it sends it to the brain and gets back three things: how likely it is a scam, how dangerous it is, and **the reasons why** — for example, "scary urgent words" or "a suspicious link." So it never just says "bad" — it tells you **why**, in plain words.

### [6:05–6:40] Slides 19–20 — My Results
*(Slide 19 is a section title — go straight to 20.)*
> Now the results. For **text messages: about 99 out of 100 correct** — very strong. For **scam calls: nearly perfect** — but that was on a small set of examples, so I call it promising, not proven yet. For **fake links: about 81 out of 100** — this was my hardest job, and it was limited by how few examples I had. I am being honest about that.

### [6:40–6:55] Slide 22 — Did I Hit My Targets?
*(Skip slide 21 — already covered the features.)*
> Did I hit my targets? Yes — all of them. It beat my accuracy goals, it answers in **less than the blink of an eye**, voice takes about one second, and it almost never raises a false alarm — under 4 times in 100. **Every target met.**

### [6:55–7:00] Slides 23–25 — What It All Means
> The big lesson: **a small, simple model can do just as well as a big, heavy one** — small enough to live on your phone. And unlike older work, mine also handles **voice**, runs on a **phone**, and always **explains why**. Now, let me show it working.

---

## LIVE DEMO — 7:00 to 10:00 (3 minutes)
*(Have the scam message and fake link ready to paste before you start.)*

1. **Paste a scam text message** → it flags it **99% scam, CRITICAL**, and shows the reasons.
2. **Check a fake link** → it blocks it as **very dangerous**.
3. **Let it scan an email inbox** → it catches the bad mail by itself.
4. **Save the threat** → it goes into the history and the safety screen.

> Talk while you tap: *"Here is a real scam message. I paste it… and it says 99%, CRITICAL — and it tells me why: scary urgent words and a bad link. Now a fake link… blocked. And everything is saved right here."*

**If something is slow:** don't panic and don't stop talking. Just do the text message and the link, and skip the rest.

---

## QUESTIONS — 10:00 to 15:00 (5 minutes)
*(Stay on the Thank You slide while you answer.)*

> That is AI Scam Shield — accurate, easy to understand, and made for normal people. Thank you very much. I am happy to answer your questions.

### Easy answers ready to go
- **Why is the fake-link score only about 81?** I had very few link examples, and I chose clean examples over lots of messy ones. It still passed my target.
- **The voice score looks perfect — is that real?** It was on a small set, so it is a good sign, but it needs more examples to be sure. I am honest about that.
- **Why use a small simple model and not a big famous one?** It is just as accurate on short messages, it is small enough to run on a phone, and it can **explain why** — the big ones often can't.
- **Why does it need internet?** The brain runs on a server today. Making it work offline, right on the phone, is my next step.
- **What about Khmer?** It's on my plan. The hard part is finding enough Khmer examples to teach it.
- **How does it "learn from people"?** When a user says "you got this wrong," I save that and use it to teach the app again later.
- **Does it raise false alarms?** Rarely — under 4 in 100. And since it shows the reasons, a person can always double-check.

---

## Speaking Tips
- **Check the clock at 7:00.** If you are behind, shorten slides 13–18 and protect the demo.
- Say the big numbers slowly: **99 out of 100 · 81 out of 100 · under 4 in 100.**
- Keep sentences short. Pause after each big point. A calm, clear talk beats a fast one.
