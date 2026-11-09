# Credit Transfer Advocate & Critic

CIS 1990 final project. An agent that compares a Penn course with an RWTH module and
recommends: recognize / partial / reject / not enough information, with quotes from both
documents as evidence.

Status: early setup (work in progress).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # then put your own Gemini key into .env
```

## Run the agent

TODO (one command, added once the first pipeline exists)

## Run the evaluation

TODO (one command, added once the eval runner exists)

## Layout (planned)

- `data/` - dated copies of course documents and the decisions table (no personal data)
- `src/` - agent code
- `eval/` - dev cases, test cases, runner, per-case results

## Notes

- No credentials are committed. Keys live only in `.env`, which is git-ignored.
- Raw experience reports stay local (`data/raw_reports/`, git-ignored).
