import streamlit as st
from dotenv import load_dotenv
import os

from pdf_utils import extract_pdf_text, create_question_pdf
from generator import analyze_syllabus, generate_questions, validate_questions

load_dotenv()

st.set_page_config(
    page_title="AI Question Paper Generator",
    page_icon="📝",
    layout="wide"
)

st.title("🎓 AI-Powered Question Paper and Assessment Generator")
st.caption("Generate syllabus-based question papers with configurable difficulty and Bloom's Taxonomy.")

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("GROQ_API_KEY is missing. Add it to the .env file and restart the app.")
    st.code("GROQ_API_KEY=your_groq_api_key_here")
    st.stop()

if "syllabus_text" not in st.session_state:
    st.session_state.syllabus_text = ""
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "questions" not in st.session_state:
    st.session_state.questions = []
if "paper_settings" not in st.session_state:
    st.session_state.paper_settings = {}

BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
QUESTION_TYPES = ["MCQ", "Short Answer", "Long Answer", "Case Study"]

with st.sidebar:
    st.header("About")
    st.write("Upload a syllabus PDF, analyze its units and topics, configure an exam, and generate an editable question paper.")
    st.info("Faculty should review AI-generated questions and answer keys before using them in an actual examination.")

st.header("1. Upload syllabus")
uploaded = st.file_uploader("Choose a syllabus PDF", type=["pdf"])

if uploaded:
    st.success(f"Selected file: {uploaded.name}")
    if st.button("Extract syllabus text", type="primary"):
        with st.spinner("Reading PDF..."):
            text = extract_pdf_text(uploaded)
        if text.strip():
            st.session_state.syllabus_text = text
            st.session_state.analysis = None
            st.session_state.questions = []
            st.success(f"Extracted {len(text):,} characters.")
        else:
            st.error("No text was extracted. If this is a scanned PDF, install Tesseract OCR and follow the README instructions.")

if st.session_state.syllabus_text:
    st.text_area("Extracted syllabus text", st.session_state.syllabus_text, height=220, disabled=True)
    st.download_button(
        "Download extracted text",
        st.session_state.syllabus_text,
        file_name="extracted_syllabus.txt",
        mime="text/plain"
    )

    st.header("2. Analyze syllabus")
    if st.button("Analyze syllabus with AI"):
        try:
            with st.spinner("Identifying subject, units, topics and learning outcomes..."):
                st.session_state.analysis = analyze_syllabus(st.session_state.syllabus_text, api_key)
            st.success("Syllabus analysis completed.")
        except Exception as exc:
            st.error(f"Syllabus analysis failed: {exc}")

if st.session_state.analysis:
    analysis = st.session_state.analysis
    st.subheader(f"Subject: {analysis.get('subject_name', 'Not identified')}")
    if analysis.get("description"):
        st.write(analysis["description"])
    for unit_data in analysis.get("units", []):
        with st.expander(unit_data.get("unit_name", "Unit")):
            st.markdown("**Topics**")
            for topic in unit_data.get("topics", []):
                st.write(f"• {topic}")
            st.markdown("**Learning outcomes**")
            for outcome in unit_data.get("learning_outcomes", []):
                st.write(f"• {outcome}")

st.header("3. Configure question paper")
if not st.session_state.syllabus_text:
    st.info("Upload and extract a syllabus PDF to enable question generation.")
else:
    c1, c2 = st.columns(2)
    with c1:
        subject = st.text_input(
            "Subject name",
            value=(st.session_state.analysis or {}).get("subject_name", "")
        )
        unit = st.text_input("Unit or topic to assess", placeholder="Example: Unit 1 - Introduction to Machine Learning")
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    with c2:
        bloom = st.selectbox("Bloom's Taxonomy level", BLOOM_LEVELS)
        duration = st.number_input("Exam duration (minutes)", min_value=15, max_value=300, value=60, step=5)

    st.markdown("**Question distribution**")
    st.caption("Set the number of questions and marks per question. Set a count to zero to skip that type.")
    section_configs = []
    cols = st.columns(4)
    defaults = {"MCQ": (5, 1), "Short Answer": (3, 2), "Long Answer": (2, 5), "Case Study": (0, 10)}
    for idx, qtype in enumerate(QUESTION_TYPES):
        with cols[idx]:
            st.markdown(f"**{qtype}**")
            count = st.number_input("Number", min_value=0, max_value=20, value=defaults[qtype][0], key=f"count_{qtype}")
            marks = st.number_input("Marks each", min_value=1, max_value=50, value=defaults[qtype][1], key=f"marks_{qtype}")
            if count:
                section_configs.append({"type": qtype, "count": int(count), "marks": int(marks)})

    total_questions = sum(x["count"] for x in section_configs)
    total_marks = sum(x["count"] * x["marks"] for x in section_configs)
    m1, m2, m3 = st.columns(3)
    m1.metric("Questions requested", total_questions)
    m2.metric("Total marks", total_marks)
    m3.metric("Duration", f"{duration} min")

    if st.button("🚀 Generate question paper", type="primary", use_container_width=True):
        if not subject.strip():
            st.error("Enter a subject name.")
        elif not unit.strip():
            st.error("Enter a unit or topic.")
        elif not section_configs:
            st.error("Choose at least one question type.")
        else:
            try:
                with st.spinner("Generating questions. This may take a little time..."):
                    generated = generate_questions(
                        syllabus_text=st.session_state.syllabus_text,
                        subject=subject.strip(),
                        unit=unit.strip(),
                        difficulty=difficulty,
                        bloom_level=bloom,
                        sections=section_configs,
                        api_key=api_key
                    )
                errors, actual_marks = validate_questions(generated, section_configs)
                if errors:
                    st.session_state.questions = []
                    st.error("The generated paper did not pass validation:")
                    for error in errors:
                        st.write(f"• {error}")
                    st.caption("Try generating again or reduce the number of questions.")
                else:
                    st.session_state.questions = generated
                    st.session_state.paper_settings = {
                        "subject": subject.strip(),
                        "duration": int(duration),
                        "total_marks": actual_marks,
                        "difficulty": difficulty,
                        "bloom_level": bloom,
                        "unit": unit.strip()
                    }
                    st.success("Question paper generated and basic structure validated.")
            except Exception as exc:
                st.error(f"Generation failed: {exc}")

if st.session_state.questions:
    st.header("4. Review and edit questions")
    questions = st.session_state.questions

    for i, q in enumerate(questions):
        label = f"Q{i + 1} · {q.get('question_type', 'Question')} · {q.get('marks', 0)} marks"
        with st.expander(label, expanded=(i == 0)):
            q["question"] = st.text_area("Question", q.get("question", ""), key=f"q_text_{i}")
            st.caption(f"Bloom's level: {q.get('bloom_level', '')} | Difficulty: {q.get('difficulty', '')}")
            if q.get("question_type") == "MCQ":
                options = list(q.get("options") or [])
                options = (options + ["", "", "", ""])[:4]
                for j in range(4):
                    options[j] = st.text_input(f"Option {chr(65+j)}", options[j], key=f"q_{i}_opt_{j}")
                q["options"] = options
                answer = q.get("correct_answer", "A")
                q["correct_answer"] = st.selectbox(
                    "Correct option",
                    ["A", "B", "C", "D"],
                    index=["A", "B", "C", "D"].index(answer) if answer in ["A", "B", "C", "D"] else 0,
                    key=f"q_{i}_answer"
                )
                q["explanation"] = st.text_area("Explanation", q.get("explanation", ""), key=f"q_{i}_explanation")
            else:
                q["model_answer"] = st.text_area("Model answer / marking guidance", q.get("model_answer", ""), key=f"q_{i}_model")

    st.header("5. Answer key")
    if st.checkbox("Show answer key on screen"):
        for i, q in enumerate(questions):
            st.markdown(f"**Q{i+1}. {q.get('question', '')}**")
            if q.get("question_type") == "MCQ":
                st.success(f"Correct answer: {q.get('correct_answer', '')}")
                st.write(q.get("explanation", ""))
            else:
                st.write(q.get("model_answer", ""))

    st.header("6. Export PDF")
    include_answers = st.checkbox("Include answer key and model answers in this PDF", value=False)
    settings = st.session_state.paper_settings
    try:
        pdf_bytes = create_question_pdf(
            subject=settings["subject"],
            questions=questions,
            duration=settings["duration"],
            total_marks=settings["total_marks"],
            include_answers=include_answers,
            unit=settings.get("unit", "")
        )
        st.download_button(
            "📥 Download question paper PDF",
            data=pdf_bytes,
            file_name="AI_Question_Paper.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as exc:
        st.error(f"PDF creation failed: {exc}")

    if st.button("Clear generated paper"):
        st.session_state.questions = []
        st.session_state.paper_settings = {}
        st.rerun()

st.divider()
st.caption("AI-Powered Question Paper and Assessment Generator · Review all AI-generated content before examination use.")
