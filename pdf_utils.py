from io import BytesIO
from xml.sax.saxutils import escape

import fitz
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether


def extract_pdf_text(uploaded_file, enable_ocr=True):
    """Extract text from a Streamlit uploaded PDF. OCR is attempted for image-only pages."""
    raw = uploaded_file.getvalue()
    document = fitz.open(stream=raw, filetype="pdf")
    page_texts = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text("text").strip()
        if len(text) < 30 and enable_ocr:
            try:
                text_page = page.get_textpage_ocr(language="eng", dpi=200, full=True)
                text = page.get_text("text", textpage=text_page).strip()
            except Exception:
                # OCR is optional; ordinary text extraction still works.
                pass
        if text:
            page_texts.append(f"--- PAGE {page_number} ---\n{text}")

    document.close()
    return "\n\n".join(page_texts)


def create_question_pdf(subject, questions, duration, total_marks, include_answers=False, unit=""):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"{subject} Question Paper",
        author="AI Question Paper Generator",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ExamTitle", parent=styles["Title"], fontSize=17, leading=21,
        alignment=TA_CENTER, textColor=colors.HexColor("#17365D"), spaceAfter=12
    )
    question_style = ParagraphStyle(
        "QuestionText", parent=styles["BodyText"], fontSize=10,
        leading=14, spaceAfter=5
    )
    small_style = ParagraphStyle(
        "SmallText", parent=styles["BodyText"], fontSize=9,
        leading=12, leftIndent=12, spaceAfter=3
    )
    answer_style = ParagraphStyle(
        "AnswerText", parent=styles["BodyText"], fontSize=9,
        leading=12, textColor=colors.HexColor("#176B3A"), spaceAfter=8
    )

    story = [
        Paragraph("QUESTION PAPER", title_style),
        Paragraph(f"<b>Subject:</b> {escape(str(subject))}", styles["Normal"]),
    ]
    if unit:
        story.append(Paragraph(f"<b>Unit / Topic:</b> {escape(str(unit))}", styles["Normal"]))
    story.extend([
        Paragraph(f"<b>Duration:</b> {int(duration)} minutes", styles["Normal"]),
        Paragraph(f"<b>Maximum Marks:</b> {int(total_marks)}", styles["Normal"]),
        Spacer(1, 8 * mm),
    ])

    current_section = None
    for idx, q in enumerate(questions, start=1):
        section = str(q.get("section", "Questions"))
        block = []
        if section != current_section:
            current_section = section
            block.append(Paragraph(f"<b>{escape(section)}</b>", styles["Heading2"]))

        question_text = escape(str(q.get("question", "")))
        marks = escape(str(q.get("marks", "")))
        block.append(Paragraph(f"<b>Q{idx}.</b> {question_text} <b>[{marks} Marks]</b>", question_style))

        if q.get("question_type") == "MCQ":
            labels = ["A", "B", "C", "D"]
            for label, option in zip(labels, q.get("options", [])):
                block.append(Paragraph(f"{label}. {escape(str(option))}", small_style))

        if include_answers:
            if q.get("question_type") == "MCQ":
                answer = escape(str(q.get("correct_answer", "")))
                explanation = escape(str(q.get("explanation", "")))
                answer_text = f"<b>Correct answer:</b> {answer}<br/><b>Explanation:</b> {explanation}"
            else:
                answer_text = f"<b>Model answer:</b> {escape(str(q.get('model_answer', '')))}"
            block.append(Paragraph(answer_text, answer_style))

        block.append(Spacer(1, 4 * mm))
        story.append(KeepTogether(block))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
