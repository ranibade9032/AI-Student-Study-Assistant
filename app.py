import os
import json
import gradio as gr
from google import genai
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

client = genai.Client(api_key=API_KEY) if API_KEY else None


# ---------------- AI FUNCTION ----------------

def ask_ai(prompt):
    if client is None:
        return "ERROR: GEMINI_API_KEY is missing. Check your .env file."

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return response.text or "No response received."

    except Exception as error:
        return f"ERROR: {error}"


# ---------------- SUMMARY FUNCTION ----------------

def study_assistant(notes):
    if not notes or not notes.strip():
        return "Please enter your study notes first.", ""

    prompt = f"""
You are a friendly AI study tutor.
Explain the notes using simple English.

Create these sections:

## Simple Summary
Explain the topic in easy words.

## Important Points
Give important points as bullet points.

## Quick Revision
Give short revision tips.

STUDENT NOTES:
{notes}
"""

    result = ask_ai(prompt)

    if result.startswith("ERROR:"):
        return result, ""

    marker = "## Important Points"

    if marker in result:
        summary, points = result.split(marker, 1)
        return summary.strip(), marker + points

    return result, "Review the important ideas from your summary."


# ---------------- QUIZ FUNCTION ----------------

def make_quiz(notes):
    if not notes or not notes.strip():
        return [], "Please enter your study notes first."

    prompt = f"""
Create 5 multiple-choice questions from these study notes.

Return ONLY a valid JSON array.
Do not include Markdown code fences.

Each question must contain:
- question
- options: exactly four options
- answer: exact correct option text
- explanation: short explanation

Example:
[
  {{
    "question": "What is Python?",
    "options": [
      "Programming language",
      "Operating system",
      "Web browser",
      "Database"
    ],
    "answer": "Programming language",
    "explanation": "Python is a programming language."
  }}
]

Ensure each answer exactly matches one of its options.

STUDY NOTES:
{notes}
"""

    result = ask_ai(prompt)

    if result.startswith("ERROR:"):
        return [], result

    try:
        start = result.find("[")
        end = result.rfind("]") + 1

        if start == -1 or end <= start:
            return [], "Quiz response was invalid. Please try again."

        questions = json.loads(result[start:end])

        if not isinstance(questions, list):
            return [], "Quiz response was invalid. Please try again."

        valid_questions = []

        for question in questions[:5]:
            if not isinstance(question, dict):
                continue

            options = question.get("options", [])
            answer = question.get("answer", "")

            if (
                question.get("question")
                and isinstance(options, list)
                and len(options) == 4
                and answer in options
                and question.get("explanation")
            ):
                valid_questions.append(question)

        if not valid_questions:
            return [], "No valid quiz questions were generated."

        return (
            valid_questions,
            f"✨ {len(valid_questions)} questions are ready!"
        )

    except (ValueError, TypeError, json.JSONDecodeError):
        return [], "Quiz generation failed. Please try again."


# ---------------- DISPLAY QUIZ ----------------

def show_quiz(questions):
    updates = []

    for index in range(5):
        if index < len(questions):
            question = questions[index]

            updates.append(
                gr.update(
                    label=f"Q{index + 1}. {question['question']}",
                    choices=question["options"],
                    value=None,
                    visible=True
                )
            )
        else:
            updates.append(
                gr.update(
                    choices=[],
                    value=None,
                    visible=False
                )
            )

    return (*updates, gr.update(visible=bool(questions)))


# ---------------- CHECK ANSWERS ----------------

def grade_quiz(questions, a1, a2, a3, a4, a5):
    if not questions:
        return "Please generate a quiz first."

    answers = [a1, a2, a3, a4, a5]
    score = 0
    feedback = []

    for index, question in enumerate(questions):
        selected = answers[index]
        correct = question["answer"]
        explanation = question["explanation"]

        if selected == correct:
            score += 1
            status = "✅ Correct!"
        elif selected is None:
            status = f"⚠️ Not answered. Correct answer: {correct}"
        else:
            status = f"❌ Correct answer: {correct}"

        feedback.append(
            f"### Question {index + 1}: {status}\n{explanation}"
        )

    total = len(questions)
    percentage = round(score / total * 100)

    return (
        f"# 🏆 Your Result: {score}/{total}\n"
        f"### 📊 Score: {percentage}%\n\n"
        + "\n\n---\n\n".join(feedback)
    )


# ---------------- CLEAR ALL ----------------

def clear_all():
    return (
        "",
        "",
        "",
        [],
        "",
        gr.update(choices=[], value=None, visible=False),
        gr.update(choices=[], value=None, visible=False),
        gr.update(choices=[], value=None, visible=False),
        gr.update(choices=[], value=None, visible=False),
        gr.update(choices=[], value=None, visible=False),
        gr.update(visible=False),
        ""
    )


# ---------------- CSS DESIGN ----------------

CSS = """
:root {
    color-scheme: light !important;
}

html,
body,
.gradio-container,
.main,
.wrap,
.contain {
    background: #eef8ff !important;
    color: #172554 !important;
}

.gradio-container {
    max-width: 1400px !important;
    margin: auto !important;
}

/* Make headings and ordinary text readable */
.gradio-container h1,
.gradio-container h2,
.gradio-container h3,
.gradio-container h4,
.gradio-container p,
.gradio-container li,
.gradio-container label,
.gradio-container span,
.gradio-container strong,
.gradio-container em,
.gradio-container .prose,
.gradio-container .markdown {
    color: #172554 !important;
}

/* Main heading */
.main-title {
    background: linear-gradient(
        110deg,
        #dbeafe,
        #bae6fd,
        #ffffff
    ) !important;

    border: 1px solid #93c5fd !important;
    border-radius: 22px !important;
    padding: 24px 28px !important;
    margin: 8px 0 18px !important;
    box-shadow: 0 10px 28px rgba(59, 130, 246, 0.12);
}

.main-title h1 {
    color: #1e3a8a !important;
    font-size: clamp(26px, 3vw, 38px) !important;
    font-weight: 800 !important;
    margin: 0 0 8px 0 !important;
}

.main-title p {
    color: #1d4ed8 !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    margin: 0 !important;
}

.tagline {
    color: #1d4ed8 !important;
    text-align: center;
    margin: 6px 0 18px;
    font-weight: 700 !important;
}

/* White content panels */
.panel {
    background: #ffffff !important;
    border: 1px solid #bfdbfe !important;
    border-radius: 18px !important;
    padding: 18px !important;
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.09) !important;
}

.panel,
.panel * {
    color: #172554 !important;
}

.panel h2,
.panel h3 {
    color: #1e40af !important;
    font-size: 23px !important;
}

/* Input areas */
.gradio-container textarea,
.gradio-container input:not([type="radio"]):not([type="checkbox"]) {
    background: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #60a5fa !important;
    border-radius: 12px !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #111827 !important;
}

.gradio-container textarea::placeholder,
.gradio-container input::placeholder {
    color: #64748b !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #64748b !important;
}

/* Radio buttons */
.gradio-container input[type="radio"] {
    accent-color: #2563eb !important;
}

/* Buttons */
.gradio-container button {
    border-radius: 10px !important;
    font-weight: 700 !important;
}

.gradio-container button.primary {
    background: linear-gradient(
        90deg,
        #2563eb,
        #38bdf8
    ) !important;
    color: #ffffff !important;
    border: 0 !important;
}

.gradio-container button.secondary {
    background: #e0f2fe !important;
    color: #1d4ed8 !important;
    border: 1px solid #7dd3fc !important;
}

/* Footer */
.footer {
    color: #1d4ed8 !important;
    text-align: center;
    padding: 16px;
    font-weight: 600;
}

@media (max-width: 800px) {
    .main-title {
        padding: 18px !important;
    }

    .main-title h1 {
        font-size: 25px !important;
    }

    .panel {
        padding: 12px !important;
    }
}
"""


# ---------------- MAIN APP ----------------

with gr.Blocks(title="AI Student Study Assistant") as app:

    gr.HTML("""
    <div class="main-title">
        <h1>🎓 AI Student Study Assistant</h1>
        <p>Learn smarter • Revise faster • Practice better</p>
    </div>

    <div class="tagline">
        ✨ Your personal AI tutor for notes, revision and practice ✨
    </div>
    """)

    with gr.Row(equal_height=False):

        # Left column
        with gr.Column(scale=1):

            with gr.Column(elem_classes=["panel"]):

                gr.Markdown("## 📚 Start Learning")

                notes = gr.Textbox(
                    label="Your Study Notes",
                    placeholder="Paste your class notes or study material here...",
                    lines=8
                )

                with gr.Row():

                    summary_btn = gr.Button(
                        "✨ Generate Summary",
                        variant="primary"
                    )

                    quiz_btn = gr.Button(
                        "🧠 Generate Quiz",
                        variant="secondary"
                    )

                clear_btn = gr.Button("🗑️ Clear All")

            with gr.Column(elem_classes=["panel"]):

                gr.Markdown("## 📖 Simple Summary")
                summary_output = gr.Markdown()

                gr.Markdown("## ⭐ Important Points & Quick Revision")
                points_output = gr.Markdown()

        # Right column
        with gr.Column(scale=1):

            with gr.Column(elem_classes=["panel"]):

                gr.Markdown("## 💡 How to Use")

                gr.Markdown("""
- Paste your study notes in the box.
- Click **Generate Summary** to understand the topic.
- Click **Generate Quiz** to create five questions.
- Submit your answers to see your score and explanations.
                """)

            with gr.Column(elem_classes=["panel"]):

                gr.Markdown("## 📝 Knowledge Check")

                quiz_status = gr.Markdown()
                quiz_questions = gr.State([])

                q1 = gr.Radio(
                    label="Question 1",
                    choices=[],
                    visible=False
                )

                q2 = gr.Radio(
                    label="Question 2",
                    choices=[],
                    visible=False
                )

                q3 = gr.Radio(
                    label="Question 3",
                    choices=[],
                    visible=False
                )

                q4 = gr.Radio(
                    label="Question 4",
                    choices=[],
                    visible=False
                )

                q5 = gr.Radio(
                    label="Question 5",
                    choices=[],
                    visible=False
                )

                submit_btn = gr.Button(
                    "✅ Submit Quiz",
                    variant="primary",
                    visible=False
                )

                result = gr.Markdown()

    gr.HTML("""
    <div class="footer">
        ✨ Build your skills • Create a better future ✨
    </div>
    """)

    # Button actions
    summary_btn.click(
        fn=study_assistant,
        inputs=notes,
        outputs=[summary_output, points_output]
    )

    quiz_btn.click(
        fn=make_quiz,
        inputs=notes,
        outputs=[quiz_questions, quiz_status]
    ).then(
        fn=show_quiz,
        inputs=quiz_questions,
        outputs=[q1, q2, q3, q4, q5, submit_btn]
    )

    submit_btn.click(
        fn=grade_quiz,
        inputs=[quiz_questions, q1, q2, q3, q4, q5],
        outputs=result
    )

    clear_btn.click(
        fn=clear_all,
        inputs=[],
        outputs=[
            notes,
            summary_output,
            points_output,
            quiz_questions,
            quiz_status,
            q1, q2, q3, q4, q5,
            submit_btn,
            result
        ]
    )


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.launch(
        server_name="127.0.0.1",
        server_port=7861,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="sky",
            neutral_hue="slate"
        ),
        css=CSS
    )
