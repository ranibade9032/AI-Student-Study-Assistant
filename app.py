
import os
import json
import gradio as gr
from google import genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None
MODEL = "gemini-3.8-flash"


def ask_ai(prompt):
    if client is None:
        return "ERROR: GEMINI_API_KEY is not configured."
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return response.text or "No response received."
    except Exception as e:
        return f"ERROR: {e}"


def study_assistant(notes):
    if not notes or not notes.strip():
        return "Please enter your study notes first.", ""

    prompt = f"""
You are a friendly AI study tutor. Use simple English.

Create these sections from the student's notes:

## 📖 Simple Summary
Explain the topic in easy words.

## ⭐ Important Points
List the key points as bullets.

## 💡 Quick Revision
Give a few short revision tips.

STUDENT NOTES:
{notes}
"""
    result = ask_ai(prompt)

    if result.startswith("ERROR:"):
        return result, ""

    parts = result.split("## ⭐ Important Points", 1)
    if len(parts) == 2:
        summary = parts[0].strip()
        points = "## ⭐ Important Points" + parts[1]
        return summary, points

    return result, "Review the important ideas from your summary."


def make_quiz(notes):
    if not notes or not notes.strip():
        return [], "Please enter your study notes first."

    prompt = f"""
Create 5 multiple-choice questions using the notes below.
Return ONLY a valid JSON array without markdown fences.

Format:
[
  {{
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Exact correct option text",
    "explanation": "Short explanation"
  }}
]

Ensure every answer exactly matches one of the four options.

NOTES:
{notes}
"""
    result = ask_ai(prompt)

    if result.startswith("ERROR:"):
        return [], result

    try:
        start = result.find("[")
        end = result.rfind("]") + 1
        if start < 0 or end <= start:
            raise ValueError("No JSON array found")

        questions = json.loads(result[start:end])

        if not isinstance(questions, list) or len(questions) < 1:
            raise ValueError("No questions generated")

        valid_questions = []
        for q in questions[:5]:
            if not all(k in q for k in
                       ("question", "options", "answer", "explanation")):
                continue
            if len(q["options"]) != 4:
                continue
            if q["answer"] not in q["options"]:
                continue
            valid_questions.append(q)

        if not valid_questions:
            raise ValueError("Invalid quiz format")

        return valid_questions, (
            f"✨ {len(valid_questions)} questions are ready! "
            "Choose your answers below."
        )

    except (ValueError, TypeError, json.JSONDecodeError):
        return [], "Quiz generation failed. Please try again."


def display_quiz(questions):
    updates = []
    for i in range(5):
        if questions and i < len(questions):
            q = questions[i]
            updates.append(
                gr.update(
                    label=f"Q{i + 1}. {q['question']}",
                    choices=q["options"],
                    value=None,
                    visible=True
                )
            )
        else:
            updates.append(
                gr.update(choices=[], value=None, visible=False)
            )

    return (*updates, gr.update(visible=bool(questions)))


def grade_quiz(questions, a1, a2, a3, a4, a5):
    if not questions:
        return "Please generate a quiz first."

    selected_answers = [a1, a2, a3, a4, a5]
    score = 0
    feedback = []

    for i, q in enumerate(questions):
        selected = selected_answers[i]
        correct = q["answer"]

        if selected == correct:
            score += 1
            status = "✅ Correct!"
        else:
            status = f"❌ Correct answer: {correct}"

        feedback.append(
            f"### Question {i + 1}: {status}\n"
            f"{q['explanation']}"
        )

    percentage = round(score / len(questions) * 100)
    return (
        f"# 🏆 Your Result: {score}/{len(questions)}\n"
        f"### 📊 Score: {percentage}%\n\n"
        + "\n\n---\n\n".join(feedback)
    )


CSS = """
.gradio-container {
    background: linear-gradient(
        135deg, #080b24, #24104f, #4c1d95, #172554
    ) !important;
    color: #ffffff !important;
}

.main-title {
    text-align: center;
    padding: 35px 20px;
    border-radius: 24px;
    background: linear-gradient(
        110deg, #2563eb, #7c3aed, #db2777
    );
    color: #ffffff !important;
    margin-bottom: 20px;
    box-shadow: 0 12px 35px #7c3aed55;
}

.main-title h1,
.main-title p {
    color: #ffffff !important;
}

.main-title h1 {
    font-size: 34px !important;
    font-weight: 800 !important;
}

.subtitle {
    text-align: center;
    color: #f3e8ff !important;
    font-size: 17px;
    margin-bottom: 24px;
}

.panel {
    background: #171d3b !important;
    border: 1px solid #8b5cf6 !important;
    border-radius: 20px !important;
    padding: 22px !important;
    margin-bottom: 18px !important;
    box-shadow: 0 8px 26px #00000035;
}

.gradio-container h1,
.gradio-container h2,
.gradio-container h3,
.gradio-container .prose,
.gradio-container .prose p,
.gradio-container .prose strong {
    color: #ffffff !important;
}

.gradio-container label {
    color: #f3e8ff !important;
    font-weight: 700 !important;
}

.gradio-container textarea,
.gradio-container input:not([type="radio"]):not([type="checkbox"]) {
    background: #ffffff !important;
    color: #111827 !important;
    border: 2px solid #a78bfa !important;
    border-radius: 12px !important;
}

.gradio-container textarea::placeholder {
    color: #6b7280 !important;
}

.gradio-container button {
    border-radius: 12px !important;
    font-weight: 700 !important;
}

.gradio-container button.primary {
    background: linear-gradient(
        90deg, #2563eb, #7c3aed, #c026d3
    ) !important;
    color: #ffffff !important;
    border: none !important;
}

.gradio-container input[type="radio"] {
    accent-color: #a855f7;
}

.gradio-container .markdown,
.gradio-container .prose {
    color: #ffffff !important;
}
"""


with gr.Blocks(
    title="AI Student Study Assistant",
    theme=gr.themes.Soft(
        primary_hue="violet",
        secondary_hue="blue",
        neutral_hue="slate"
    ),
    css=CSS
) as app:

    gr.HTML("""
    <div class="main-title">
        <h1>🎓 AI Student Study Assistant</h1>
        <p>Learn smarter • Revise faster • Practice better</p>
    </div>
    <div class="subtitle">
        Your personal AI tutor for notes, revision and practice.
    </div>
    """)

    with gr.Column(elem_classes=["panel"]):
        gr.Markdown("## 📚 Start Learning")

        notes = gr.Textbox(
            label="Your Study Notes",
            placeholder="Paste your class notes or study material here...",
            lines=10
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
            clear_btn = gr.Button("🗑️ Clear")

    with gr.Column(elem_classes=["panel"]):
        gr.Markdown("## 📖 Study Summary")
        summary_output = gr.Markdown()

        gr.Markdown("## ⭐ Important Points & Quick Revision")
        points_output = gr.Markdown()

    summary_btn.click(
        fn=study_assistant,
        inputs=notes,
        outputs=[summary_output, points_output]
    )

    with gr.Column(elem_classes=["panel"]):
        gr.Markdown("## 📝 Knowledge Check")

        quiz_status = gr.Markdown()
        quiz_questions = gr.State([])

        q1 = gr.Radio(label="Question 1", choices=[], visible=False)
        q2 = gr.Radio(label="Question 2", choices=[], visible=False)
        q3 = gr.Radio(label="Question 3", choices=[], visible=False)
        q4 = gr.Radio(label="Question 4", choices=[], visible=False)
        q5 = gr.Radio(label="Question 5", choices=[], visible=False)

        submit_btn = gr.Button(
            "✅ Submit Quiz",
            variant="primary",
            visible=False
        )
        result = gr.Markdown()

    quiz_btn.click(
        fn=make_quiz,
        inputs=notes,
        outputs=[quiz_questions, quiz_status]
    ).then(
        fn=display_quiz,
        inputs=quiz_questions,
        outputs=[q1, q2, q3, q4, q5, submit_btn]
    )

    submit_btn.click(
        fn=grade_quiz,
        inputs=[quiz_questions, q1, q2, q3, q4, q5],
        outputs=result
    )

    clear_btn.click(
        fn=lambda: (
            "", "", "", [], "",
            gr.update(choices=[], value=None, visible=False),
            gr.update(choices=[], value=None, visible=False),
            gr.update(choices=[], value=None, visible=False),
            gr.update(choices=[], value=None, visible=False),
            gr.update(choices=[], value=None, visible=False),
            gr.update(visible=False),
            ""
        ),
        outputs=[
            notes, summary_output, points_output,
            quiz_questions, quiz_status,
            q1, q2, q3, q4, q5, submit_btn, result
        ]
    )


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 10000))
    )
