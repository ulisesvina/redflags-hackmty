# HackMTY 2026 — Infosys Challenge Briefing

Transcript of the audio-only recording (`WhatsApp Audio 2026-09-11 at 21.47.02.mp4`), ~12 min.
Cleaned up: filler words removed, ASR errors fixed, organized by topic.
Recording cuts off mid-sentence at the end — the second problem statement is only named, never described.

**Speakers:**
- **Richard** — Senior Enterprise Architect, Strategic Technologies Group (STG), Infosys. Currently a forward-deployed engineer / "AI architect" in the finance sector, designing an AI-based system for a global financial firm in New York. *(ASR garbled his surname — "Honoratum" is likely wrong.)*
- **Koss** — joined Infosys straight out of college ~17 years ago, did enterprise work for ~12–13 years, then moved into product development. Now manages a small R&D team within a healthcare product at Infosys, as part of STG. *(Name per ASR; spelling uncertain.)*

---

## Intro — who we are (00:00)

**Richard:** We're not going to spend a tremendous amount of time going through this. Primarily I'm here to answer as many questions as you have, to make sure you have what you need to start the hackathon successfully. We'll be here tomorrow during the day too, for any questions.

**Koss:** I started my career with Infosys just like you guys — I graduated, joined, and it's been about 17 years now. For the first 12–13 years I did enterprise work, then I wanted to try building a product — something of our own that Infosys could use. We pitched the idea, got a big team, and today I manage a small R&D team within a healthcare product at Infosys. The great thing about Infosys and STG is there are many avenues: enterprise projects, building your own products, entrepreneurship programs where you can pitch your own idea and get funding for it if it's worth it.

## What we expect from you (02:46)

**Koss:** When we started these hackathons maybe 10 years back, the pitch was very different — a small, superficial problem statement where you'd build some small part of a big system. It was never this big. With AI, you guys can build this overnight.

What we expect is to see **how you think about the problem**: your understanding of it, the scenarios you're going to tackle, how you approach it. We're as interested in your failures as in the successful use cases. Note down your learnings throughout these 36 hours and present them with your solution.

**Richard:** One thing you learn going through life, especially in business and technology: you fail more times than you succeed. I learned from my failures — if I succeed right off the bat, there was no trial, no error, no struggle, and I didn't learn anything. Going through that struggle is what we're looking for. This won't be perfect right out of the bat. Yes, you can pump this into AI and it'll spit something out — but you'll have to explain to us exactly how you got there: your train of thought from the problem statement to the end solution. That's what we want to see.

## Problem statement 1: Forensics Auditor (04:18)

**Richard:** This one is a real-world problem — you'll see it in finance. Finance is a fun industry because it's highly regulated: you're dealing with people's money and everything has to be explained. We get trained on these problems constantly, every year.

Every country has this problem: illegal money in your area. How do you flag those transactions — and do it quickly, so it's detected before it's too late to do anything about it? Say you're a business dealing with a supplier who turns out not to be legitimate — by the time you figure it out, you're already on the hook for the money.

The challenge: you don't want to flag something that isn't actually a problem. You have to be able to explain why you did what you did. That's part of the proof — you had this set of transactions, you followed the money, and this is why you believe this company is not legitimate, and why this particular company is flagged while that transaction is not.

**Koss:** Pay attention to this part of the statement: this is **not just anomaly detection** or one-off challenges. Given a company's books with many transactions, you need to trace the flow of the transactions — and you don't want to accuse anyone over a one-off. The big challenge lines in the PDF capture the essence of the problem.

## Resources you have access to (06:56)

**Richard:** Use what's already open-sourced and what governments put out. The government tracks these transactions and publishes the patterns you should be looking for — it's not just a dataset.

And with AI, the vast majority of your time goes into the data anyway: understanding it, making sure it's correct, and driving the AI from it. That's critical.

Models: you can pull free models from Hugging Face — we don't dictate which one. Gemini on a free account, Anthropic's models, OpenAI — we don't care, as long as it works. *(Note: the speaker mentions his Infosys laptop blocked access to several of these sites while he was working on the problems, so the slide wasn't exhaustive.)*

Data: there are major fraud/financial-crime datasets on Kaggle and elsewhere, open source. Use one — or, if you understand the problem really well, build your own synthetic dataset and use that.

## How it will be judged (08:51)

**Richard:** Once again, it's about the journey, not just the destination. From the problem statement to your end solution — how did you get there, what was that pattern? That's one of the big things we look for.

We also want to see the system running: if we inject something into it — synthetic data found to be fraudulent — how does the system react, and how does it explain itself?

**Explainability is critical.** Especially in regulated domains: when the government audits your system — and they will audit it before it ever makes it out the door — they'll want to see that it explains itself. It can't just say "I found the answer." How did it find it? What path did it take? Why was this one flagged as fraud and that one not? It has to show us why it made the decisions it made.

## Advice and closing (10:40)

**Richard:** With AI tools, software development is the easy part. Think of it like an entrepreneur: you have a problem statement, you have something to build. Imagine you're coming in to ask for money to build your company. In that mindset, look at the problem and be clear on: what can you offer, what does your MVP look like, what can you *not* do. Have all those answers clear in your mind. Don't only focus on the development part.

We do want you to be creative. If you go above and beyond, that's great to see. Look at the problem and come up with a genuinely creative solution. Have fun with it.

**Richard:** All right, so the second one we have—
*(recording ends)*

---

### TL;DR

- Two problem statements to choose from; #1 is the **Forensics Auditor**: trace transactions across a company's books, flag illegitimate money/suppliers, fast, with minimal false accusations.
- Not one-off anomaly detection — follow the **trail of transactions**.
- Judged on **explainability and the journey**: show your reasoning from problem statement to solution, demo the system reacting to injected fraudulent data, and present your failures/learnings.
- Any models (Hugging Face, Gemini, Anthropic, OpenAI) and any open fraud datasets (or your own synthetic data) are fair game; most of the work is understanding the data.
- Think like an entrepreneur pitching for funding: know your MVP, your value, and your limits — not just the code.
