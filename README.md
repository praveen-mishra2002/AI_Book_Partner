# Agentic AI Book Authoring System — Local MVP

A Python starter application that takes an author's book concept and produces:
- a book brief and chapter outline,
- research notes with web-search-enabled source discovery,
- chapter drafts,
- Mermaid diagrams,
- independent review reports,
- a compiled DOCX manuscript and project artifacts.

This is a **human-in-the-loop MVP**, not a plagiarism-certification system. AI reviews are fallible; citations and similarity risks require verification before publication.

## Architecture

```text
Author input
   |
   v
Book Director -> Book Architect
                    |
                    v
              Research Agent (web search)
                    |
                    v
              Chapter Writer
                 /      \
                v        v
         Diagram Agent  Review Agents
                \        /
                 v      v
              Revision loop (bounded)
                    |
                    v
          Manuscript assembler (DOCX)
```

Each role is a separately prompted agent function. The first version deliberately uses a controlled Python workflow rather than letting agents autonomously call one another. This makes it easier to test, trace, and debug.

## Requirements

- Python 3.11+
- An OpenAI API key with access to a model that supports the Responses API and web search.
- Internet access for research.

## Install

### macOS / Linux
```bash
cd agentic_book_authoring_mvp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add OPENAI_API_KEY to .env
streamlit run app.py
```

### Windows PowerShell
```powershell
cd agentic_book_authoring_mvp
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Add OPENAI_API_KEY to .env
streamlit run app.py
```

## Run

1. Enter the working title, concept, audience, tone, and desired number of chapters.
2. Click **Generate book package**.
3. Review the outline and chapter drafts in the app.
4. Download the ZIP of project artifacts and the assembled DOCX.

Generated artifacts are saved under `workspace/<project-slug>/`:
- `book_brief.md`
- `outline.json`
- `research/`
- `chapters/`
- `diagrams/`
- `reviews/`
- `manuscript.docx`
- `run_log.json`

## Configuration

Set these in `.env`:
- `OPENAI_API_KEY` — required
- `OPENAI_MODEL` — defaults to `gpt-4.1` in this starter; change to a model available to your API account.
- `MAX_REVISION_ROUNDS` — defaults to `1`

If the configured model is unavailable to your API account, set `OPENAI_MODEL` to an available Responses API model.

## MVP design decisions

- **Orchestration:** deterministic sequential Python pipeline.
- **Research:** Responses API web-search tool; source references must be preserved in the research output and verified by the author.
- **State:** files on local disk, so the first version does not require a database.
- **Diagrams:** Mermaid source files (`.mmd`). To render them as PNG/SVG, install Mermaid CLI separately; see below.
- **Manuscript:** python-docx compiles chapter text and figure references into a DOCX.
- **Review:** separate prompts for factual support/citation risk, originality/attribution risk, readability, relevance, and consistency.
- **Human gate:** outline and manuscript review are author responsibilities in this MVP.

## Optional: render Mermaid diagrams to SVG/PNG

Install Node.js, then:
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i workspace/<project-slug>/diagrams/chapter-01.mmd -o workspace/<project-slug>/diagrams/chapter-01.svg
```
This MVP creates diagram source and includes a figure placeholder in the DOCX. The next iteration should render SVG/PNG and embed the images directly into the manuscript.

## Important quality limitations

- A model review is not a legal determination of plagiarism or originality.
- A similarity detector should be added for publication workflows where required.
- Research citations and claims need human verification; web-search results can be incomplete or stale.
- Do not submit confidential or unpublished material unless your data-handling requirements and API settings permit it.
- Use version control and test prompts on a known evaluation set before using this for a full-length book.

## Recommended next milestones

1. Render Mermaid diagrams and embed them in DOCX.
2. Add chapter-by-chapter author approval and resume-from-checkpoint.
3. Store source/claim mappings in SQLite or PostgreSQL.
4. Add an external similarity-check provider (licensed and authorized).
5. Add regression evaluations for factuality, citation correctness, readability, and chapter consistency.
6. Add a proper project dashboard, version history, and cost/token tracking.
