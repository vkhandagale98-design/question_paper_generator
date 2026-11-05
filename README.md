# AI-Powered Question Paper and Assessment Generator

A Streamlit application that reads a syllabus PDF and uses Groq AI to generate editable examination questions based on selected units, difficulty, question types and Bloom's Taxonomy levels.

## Features

- Upload syllabus PDFs.
- Extract selectable PDF text with PyMuPDF.
- Optional OCR fallback for scanned PDFs using Tesseract.
- AI syllabus analysis: subject, units, topics and learning outcomes.
- Generate MCQs, short answers, long answers and case studies.
- Configure question counts and marks per question.
- Select Easy, Medium or Hard difficulty.
- Select Remember, Understand, Apply, Analyze, Evaluate or Create.
- Basic validation of question counts, MCQ options, answer fields and total marks.
- Edit generated questions and answers in the browser.
- Export a PDF with or without answer key.

## Requirements

- Windows, macOS or Linux
- Python 3.11–3.13 recommended
- A Groq API key

## Installation on Windows (PowerShell)

Open a terminal in this project folder.

```powershell
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run this in the current terminal and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

If `py -3.13` is unavailable, install Python 3.13 from https://www.python.org/downloads/ and enable **Add Python to PATH** during installation. You can also use `python -m venv venv` if `python --version` reports a supported version.

## Configure Groq API key

1. Visit https://console.groq.com/keys.
2. Create an API key.
3. Copy `.env.example` to a new file named `.env`.
4. Open `.env` and set:

```env
GROQ_API_KEY=your_actual_api_key
```

Do not commit or share `.env`. The `.gitignore` file excludes it from Git.

The default model is `openai/gpt-oss-120b`, configured in `generator.py`. If Groq changes model availability for your account, replace `MODEL` with a currently supported model from your Groq console.

## Run the application

```powershell
python -m streamlit run app.py
```

Open the local URL printed in the terminal, normally http://localhost:8501.

## OCR for scanned PDFs (optional)

Normal text PDFs do not need OCR. For scanned/image-only PDFs:

1. Install Tesseract OCR for Windows from https://github.com/UB-Mannheim/tesseract/wiki.
2. Ensure `tesseract.exe` is on your Windows PATH.
3. Restart the terminal and run the application again.

PyMuPDF's OCR support uses the Tesseract installation. OCR may fail silently per page if Tesseract or its English language data is unavailable; ordinary text extraction will still be attempted.

## Test with the sample syllabus

The project includes `sample_syllabus.txt`. Copy its contents into a document and export it as PDF, then upload the PDF in the app.

Suggested test:
- Subject: Machine Learning
- Unit/topic: Unit 1 - Introduction to Machine Learning
- Difficulty: Medium
- Bloom level: Understand
- MCQ: 5 questions × 1 mark
- Short Answer: 3 questions × 2 marks
- Long Answer: 2 questions × 5 marks

Expected total: 10 questions and 21 marks.

## Project structure

```text
AI_Question_Paper_Generator/
├── app.py
├── generator.py
├── pdf_utils.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── sample_syllabus.txt
└── tests/
    └── test_validation.py
```

## Important academic note

AI output can contain incorrect facts, ambiguous questions or incorrect answer keys. Faculty must review and approve the generated paper before using it in a real examination. The built-in validation checks structure and arithmetic; it does not prove academic correctness or guarantee complete syllabus coverage.

## Troubleshooting

- **GROQ_API_KEY missing:** Check that `.env` is in the same folder as `app.py`, and restart Streamlit.
- **401 error:** Create a valid API key and update `.env`.
- **429 error:** You have reached an API rate or usage limit. Wait and retry, or review your Groq account limits.
- **Model not found / unavailable:** Update `MODEL` in `generator.py` to a model currently available to your Groq account.
- **No PDF text:** Try a text-based PDF or install Tesseract for OCR.
- **ModuleNotFoundError:** Activate the virtual environment and run `pip install -r requirements.txt`.
- **Question validation failed:** Retry with fewer questions or a more specific unit/topic. Always review the generated result.

## GitHub safety

Before pushing to GitHub, confirm that `.env` is not staged or committed. Never publish API keys.
