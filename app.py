from __future__ import annotations

import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from book_agents import (
    MODEL, create_book_brief, create_outline, research_chapter, write_chapter,
    create_diagram, review_chapter, revise_chapter, safe_slug, save_text,
)
from manuscript import compile_docx

load_dotenv()
ROOT = Path(__file__).parent
WORKSPACE = ROOT / "workspace"

st.set_page_config(page_title="Agentic AI Book Authoring", page_icon="📚", layout="wide")
st.title("📚 Agentic AI Book Authoring System")
st.caption("Local MVP • Research → Outline → Draft → Diagrams → Independent review → DOCX")

if not os.getenv("OPENAI_API_KEY"):
    st.warning("Add OPENAI_API_KEY to your .env file, then restart the app.")
    st.stop()

with st.sidebar:
    st.header("Book setup")
    title = st.text_input("Working title", "Practical Guide to Agentic AI")
    concept = st.text_area(
        "Your base concept",
        "Explain agentic AI, its architecture, practical use cases, implementation patterns, governance, and examples.",
        height=160,
    )
    audience = st.text_input("Target audience", "Professionals and technical managers")
    tone = st.selectbox("Writing style", ["Clear and practical", "Academic and evidence-led", "Conversational", "Technical handbook"])
    chapter_count = st.slider("Number of chapters (pilot)", 1, 8, 2)
    run_button = st.button("Generate book package", type="primary", use_container_width=True)
    st.caption(f"Model configured: `{MODEL}`")
    st.caption("API usage may incur charges.")

st.info("The app creates a draft package. Review the outline and all claims before publication. AI review is not a plagiarism certificate.")

if run_button:
    if not title.strip() or not concept.strip():
        st.error("Please provide a working title and base concept.")
        st.stop()

    project = WORKSPACE / safe_slug(title)
    if project.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        project = WORKSPACE / f"{safe_slug(title)}-{stamp}"
    for folder in ["research", "chapters", "diagrams", "reviews"]:
        (project / folder).mkdir(parents=True, exist_ok=True)

    log = {"started_at": datetime.now(timezone.utc).isoformat(), "model": MODEL, "events": []}
    progress = st.progress(0, text="Creating book brief…")
    status = st.empty()

    try:
        brief = create_book_brief(title, concept, audience, tone, chapter_count)
        save_text(project / "book_brief.md", brief)
        log["events"].append({"stage": "book_brief", "status": "complete"})
        progress.progress(10, text="Planning chapters…")

        outline = create_outline(brief, chapter_count)
        save_text(project / "outline.json", json.dumps(outline, ensure_ascii=False, indent=2))
        log["events"].append({"stage": "outline", "status": "complete"})
        progress.progress(18, text="Producing chapters…")

        completed = []
        max_revisions = int(os.getenv("MAX_REVISION_ROUNDS", "1"))
        chapter_items = outline.get("chapters", [])
        if not chapter_items:
            raise ValueError("The outline agent returned no chapters.")

        for idx, chapter in enumerate(chapter_items):
            num = int(chapter.get("number", idx + 1))
            status.markdown(f"**Chapter {num}/{len(chapter_items)}:** {chapter.get('title', 'Untitled')}")
            research = research_chapter(brief, chapter)
            save_text(project / "research" / f"chapter-{num:02d}-research.md", research)

            draft = write_chapter(brief, chapter, research)
            save_text(project / "chapters" / f"chapter-{num:02d}.md", draft)

            diagram = create_diagram(chapter, draft, research)
            diagram = diagram.replace("```mermaid", "").replace("```", "").strip()
            save_text(project / "diagrams" / f"chapter-{num:02d}.mmd", diagram)

            review = review_chapter(brief, chapter, research, draft)
            for round_num in range(max_revisions):
                if str(review.get("overall_status", "")).upper() == "PASS":
                    break
                draft = revise_chapter(brief, chapter, research, draft, review)
                save_text(project / "chapters" / f"chapter-{num:02d}.md", draft)
                review = review_chapter(brief, chapter, research, draft)
            review_text = json.dumps(review, ensure_ascii=False, indent=2)
            save_text(project / "reviews" / f"chapter-{num:02d}-review.json", review_text)

            completed.append({
                "number": num,
                "title": chapter.get("title", f"Chapter {num}"),
                "draft": draft,
                "research": research,
                "diagram": diagram,
                "review": review,
                "review_text": review_text,
            })
            progress.progress(18 + int(72 * (idx + 1) / len(chapter_items)), text=f"Completed chapter {num}")

        compile_docx(title, brief, completed, project / "manuscript.docx")
        log["finished_at"] = datetime.now(timezone.utc).isoformat()
        log["events"].append({"stage": "assembly", "status": "complete"})
        save_text(project / "run_log.json", json.dumps(log, ensure_ascii=False, indent=2))

        # Create portable project archive.
        archive = project.with_suffix(".zip")
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in project.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(project.parent))

        st.session_state["project_dir"] = str(project)
        st.session_state["archive_path"] = str(archive)
        st.session_state["chapters"] = completed
        st.session_state["brief"] = brief
        st.session_state["outline"] = outline
        progress.progress(100, text="Book package created")
        status.success("Draft package created. Review the results below before publication.")
    except Exception as exc:
        st.error(f"Generation stopped: {exc}")
        st.exception(exc)

if "outline" in st.session_state:
    st.subheader("Book brief")
    st.markdown(st.session_state["brief"])
    st.subheader("Chapter plan")
    for ch in st.session_state["outline"].get("chapters", []):
        with st.expander(f"Chapter {ch.get('number')}: {ch.get('title')}"):
            st.write("**Purpose:**", ch.get("purpose", ""))
            st.write("**Context:**", ch.get("context", ""))
            st.write("**Objectives:**", ch.get("learning_objectives", []))
            st.write("**Sections:**", ch.get("sections", []))

    st.subheader("Drafts and quality reports")
    for ch in st.session_state.get("chapters", []):
        with st.expander(f"Chapter {ch['number']}: {ch['title']} — {ch['review'].get('overall_status', 'REVIEW')}"):
            tab1, tab2, tab3, tab4 = st.tabs(["Draft", "Research", "Diagram", "Review"])
            with tab1:
                st.markdown(ch["draft"])
            with tab2:
                st.markdown(ch["research"])
            with tab3:
                st.code(ch["diagram"], language="mermaid")
            with tab4:
                st.json(ch["review"])

    project_dir = Path(st.session_state["project_dir"])
    archive_path = Path(st.session_state["archive_path"])
    docx_path = project_dir / "manuscript.docx"
    st.subheader("Downloads")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Download manuscript DOCX", docx_path.read_bytes(), file_name="manuscript.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with c2:
        st.download_button("Download complete project ZIP", archive_path.read_bytes(), file_name=archive_path.name,
                           mime="application/zip")
