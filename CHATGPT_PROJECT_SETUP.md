# ChatGPT Project setup — one-time UI step

The technical handoff and all project decisions are held in the public GitHub repository. **A GitHub project memory does not automatically create a ChatGPT Project or guarantee that new conversations read the repository.**

## One-time setup the account owner controls
1. In ChatGPT, create a Project called **Hyperliquid BTC — Viprasol Development** using the Projects UI.
2. Move relevant prior chats into that Project where supported. Keep all future project conversations in it.
3. Set the Project's instructions to:

> Act as engineering partner for `https://github.com/Elikers/hyperliquid-btc-dashboard`. At the start of substantial tasks, read `PROJECT_STATE.md`, `DECISIONS.md`, and `HANDOFF.md` from the connected GitHub repository, plus the actual latest source code and GitHub Actions results. Treat the repository as the versioned source of truth rather than the longest chat. Continue safe research engineering sequentially without repetitive approvals. Keep original Viprasol Classic settings and the working Pages dashboard unchanged. Separate source-supported Macro-Off Classic, original 8-factor Macro-On and experimental BTC-only Lab. Never activate trading/wallet execution or live Discord trading signals, buy data, or report unverified success/profitability. Update the state/handoff docs after material verified changes. Be concise.

4. A new conversation in that Project can use the continuation prompt at the bottom of `HANDOFF.md`.

## What this does and does not do
- Prevents starting each chat from scratch by giving a stable repo location, decisions, latest evidence and next task.
- A ChatGPT Project may help group chats/instructions/files, but **does not eliminate message limits, guarantee recall of every past conversation, or guarantee autonomous code execution**.
- GitHub Actions and the separately configured hourly ChatGPT automation operate independently of the chat. Both still require run-level verification.
- Creating/moving ChatGPT Projects and chats is an account/UI action; it cannot be inferred or marked done merely by creating this repository file.
