import json
from groq import Groq

MODEL = "openai/gpt-oss-120b"


def _client(api_key):
    return Groq(api_key=api_key)


def _json_completion(client, system_prompt, user_prompt, max_tokens=10000):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_completion_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("The AI returned an empty response.")
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"The AI response was not valid JSON: {exc}") from exc


def analyze_syllabus(text, api_key):
    prompt = f"""
Analyze the syllabus. Extract only information explicitly supported by the text.
Do not invent subject details, units, topics or learning outcomes.
Return JSON with this structure:
{{
  "subject_name": "string",
  "description": "string",
  "units": [
    {{
      "unit_name": "string",
      "topics": ["string"],
      "learning_outcomes": ["string"]
    }}
  ]
}}
If an item is unavailable, use an empty string or empty list.
SYLLABUS:
{text[:24000]}
"""
    data = _json_completion(
        _client(api_key),
        "You are an academic syllabus analyzer. Return valid JSON only.",
        prompt,
        max_tokens=5000,
    )
    if not isinstance(data.get("units", []), list):
        data["units"] = []
    return data


def generate_questions(syllabus_text, subject, unit, difficulty, bloom_level, sections, api_key):
    total_requested = sum(s["count"] for s in sections)
    prompt = f"""
Create an examination question set using ONLY the syllabus below.

Subject: {subject}
Unit/topic: {unit}
Difficulty: {difficulty}
Bloom's Taxonomy level: {bloom_level}
Requested sections: {json.dumps(sections)}
Total requested questions: {total_requested}

Rules:
- Generate exactly the requested count for every question type.
- Use only syllabus-supported concepts from the requested unit/topic.
- Do not duplicate or paraphrase the same question.
- Every question must use the requested difficulty and Bloom level.
- Every MCQ must have exactly four plausible options and exactly one correct option.
- For MCQs, correct_answer must be exactly A, B, C, or D.
- For non-MCQs, provide a useful model_answer and use empty options and correct_answer.
- Keep marks exactly as requested for each question type.
- Case studies must be based on syllabus concepts, not unrelated facts.
- If the requested unit/topic cannot be supported by the syllabus, return an empty questions array rather than invent content.

Return valid JSON only, using:
{{
  "questions": [
    {{
      "section": "Section A",
      "question_type": "MCQ",
      "question": "Question text",
      "bloom_level": "{bloom_level}",
      "difficulty": "{difficulty}",
      "marks": 1,
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "A",
      "explanation": "Why this answer is correct",
      "model_answer": ""
    }}
  ]
}}
For non-MCQ questions, set options to [] and correct_answer to "".
Use section labels such as Section A, Section B, etc. Keep questions in the same order as the requested sections.

SYLLABUS:
{syllabus_text[:24000]}
"""
    data = _json_completion(
        _client(api_key),
        "You are a careful university examination paper setter. Follow the requested JSON structure exactly.",
        prompt,
        max_tokens=14000,
    )
    questions = data.get("questions", [])
    if not isinstance(questions, list):
        raise ValueError("AI response did not contain a valid questions list.")
    return questions


def validate_questions(questions, sections):
    errors = []
    expected_counts = {s["type"]: s["count"] for s in sections}
    expected_marks = {s["type"]: s["marks"] for s in sections}
    actual_counts = {}
    total_marks = 0

    if not questions:
        return ["The AI returned no questions. Check the selected unit against the syllabus."], 0

    for index, q in enumerate(questions, start=1):
        qtype = q.get("question_type")
        actual_counts[qtype] = actual_counts.get(qtype, 0) + 1

        try:
            marks = int(q.get("marks", 0))
        except (TypeError, ValueError):
            marks = 0

        if qtype not in expected_marks:
            errors.append(f"Q{index}: unexpected question type {qtype!r}.")
        elif marks != expected_marks[qtype]:
            errors.append(f"Q{index}: expected {expected_marks[qtype]} marks, got {marks}.")
        total_marks += marks

        if not str(q.get("question", "")).strip():
            errors.append(f"Q{index}: question text is empty.")

        if qtype == "MCQ":
            options = q.get("options")
            if not isinstance(options, list) or len(options) != 4:
                errors.append(f"Q{index}: MCQ must have exactly four options.")
            if q.get("correct_answer") not in {"A", "B", "C", "D"}:
                errors.append(f"Q{index}: MCQ correct answer must be A, B, C or D.")
            if not str(q.get("explanation", "")).strip():
                errors.append(f"Q{index}: MCQ explanation is missing.")
        elif qtype in {"Short Answer", "Long Answer", "Case Study"}:
            if not str(q.get("model_answer", "")).strip():
                errors.append(f"Q{index}: model answer is missing.")

    for qtype, expected in expected_counts.items():
        actual = actual_counts.get(qtype, 0)
        if actual != expected:
            errors.append(f"{qtype}: requested {expected}, generated {actual}.")

    expected_total = sum(s["count"] * s["marks"] for s in sections)
    if total_marks != expected_total:
        errors.append(f"Total marks mismatch: expected {expected_total}, generated {total_marks}.")

    return errors, total_marks
