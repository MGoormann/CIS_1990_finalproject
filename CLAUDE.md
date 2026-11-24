# Project: CIS 1990 final project (Credit Transfer Advocate & Critic)

## About the user
I am a Wirtschaftsingenieur student without a computer science background. I am building
my CIS 1990 final project (see the handout and my approved proposal) as a solo student.

## How to work with me
- Explain everything in plain language. Avoid jargon, or explain each term the first time it appears.
- For every step, say what it is, why we do it, and which part of the handout it serves
  (for example the Evaluation row in Section 4, or the protocol in Section 4.2).
- Be encouraging, and be honest about problems, risks and results that are not good.
- Do not change, commit or push anything without asking me first. Ask when a decision is mine to make.
- Never put my API key into chat, code or git. It lives only in `.env`.

## Project facts
- Final submission is due December 1, 2026 (strict); private demo December 2, 2026.
- Language: Python. Model: Gemini via the Gemini API (model name is set in `src/llm.py`).
- Cases live in `eval/cases.csv`; check them with `python -m src.cases`.
- Test cases must never be used to tune prompts or code (handout, Section 4.2).
