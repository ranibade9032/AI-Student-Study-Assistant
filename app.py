import os
import json
import gradio as gr
from google import genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def ask_ai(prompt):
    if client is None:
        return "ERROR: GEMINI_API_KEY is not configured."
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
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
        return parts[0].strip(), "## ⭐ Important Points" + parts[1]
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
        start, end = result.find("["), result.rfind("]") + 1
        if start < 0 or end <= start:
            raise ValueError("No JSON array found")
        questions = json.loads(result[start:end])
        if not isinstance(questions, list) or not questions:
            raise ValueError("No questions generated")
        valid = []
        for q in questions[:5]:
            if not isinstance(q, dict):
                continue
            if not all(k in q for k in ("question", "options", "answer", "explanation")):
                continue
            if not isinstance(q["options"], list) or len(q["options"]) != 4:
                continue
            if q["answer"] not in q["options"]:
                continue
            valid.append(q)
        if not valid:
            raise ValueError("Invalid quiz format")
        return valid, f"✨ {len(valid)} questions are ready! Choose your answers below."
    except (ValueError, TypeError, json.JSONDecodeError):
        return [], "Quiz generation failed. Please try again."


def show_quiz(questions):
    updates = []
    for i in range(5):
        if questions and i < len(questions):
            q = questions[i]
            updates.append(gr.update(
                label=f"Q{i + 1}. {q['question']}",
                choices=q["options"], value=None, visible=True
            ))
        else:
            updates.append(gr.update(choices=[], value=None, visible=False))
    return (*updates, gr.update(visible=bool(questions)))


def grade_quiz(questions, a1, a2, a3, a4, a5):
    if not questions:
        return "Please generate a quiz first."
    answers = [a1, a2, a3, a4, a5]
    score, feedback = 0, []
    for i, q in enumerate(questions):
        selected = answers[i]
        correct = q["answer"]
        if selected == correct:
            score += 1
            status = "✅ Correct!"
        else:
            status = f"❌ Correct answer: {correct}" if selected else f"⚠️ Not answered. Correct answer: {correct}"
        feedback.append(f"### Question {i + 1}: {status}\n{q['explanation']}")
    percentage = round(score / len(questions) * 100)
    return f"# 🏆 Your Result: {score}/{len(questions)}\n### 📊 Score: {percentage}%\n\n" + "\n\n---\n\n".join(feedback)


def clear_all():
    return (
        "", "", "", [], "",
        gr.update(choices=[], value=None, visible=False),
        gr.update(choices=[], value=None, visible=False),
        gr.update(choices=[], value=None, visible=False),
        gr.update(choices=[], value=None, visible=False),
        gr.update(choices=[], value=None, visible=False),
        gr.update(visible=False), ""
    )


CSS = """
:root { color-scheme: dark; }
.gradio-container {
    background: #070b27 !important;
    color: #f8fafc !important;
    max-width: 1500px !important;
}
body, .main { background: #070b27 !important; }
.main-title {
    background: linear-gradient(110deg, #075be8, #7c22df, #315dff) !important;
    border-radius: 22px;
    padding: 24px 28px;
    margin: 8px 0 18px;
    color: white !important;
    box-shadow: 0 10px 28px #28116b66;
}
.main-title h1, .main-title p { color: white !important; margin: 0; }
.main-title h1 { font-size: clamp(26px, 3vw, 38px) !important; font-weight: 800 !important; }
.main-title p { margin-top: 8px; font-size: 16px; font-weight: 600; }
.tagline { color: #cbd5ff !important; text-align: center; margin: 6px 0 18px; }
.panel {
    background: #0c1640 !important;
    border: 1px solid #4338ca !important;
    border-radius: 18px !important;
    padding: 18px !important;
    box-shadow: 0 8px 24px #0005;
}
.panel h1, .panel h2, .panel h3, .panel p, .panel li,
.panel strong, .panel em, .panel label, .panel .prose,
.panel .markdown, .panel span {
    color: #f8fafc !important;
}
.panel h2 { font-size: 23px !important; }
.panel .prose code {
    color: #312e81 !important; background: #e0e7ff !important;
    border-radius: 5px; padding: 2px 5px;
}
.panel .prose pre, .panel .prose pre code {
    background: #111827 !important; color: #f8fafc !important;
}
.gradio-container textarea,
.gradio-container input:not([type="radio"]):not([type="checkbox"]) {
    background: #f8fafc !important; color: #111827 !important;
    border: 1px solid #818cf8 !important; border-radius: 12px !important;
}
.gradio-container textarea::placeholder { color: #64748b !important; }
.gradio-container button { border-radius: 10px !important; font-weight: 700 !important; }
.gradio-container button.primary {
    background: linear-gradient(90deg, #2563eb, #7c3aed) !important;
    color: white !important; border: 0 !important;
}
.gradio-container button.secondary {
    background: #4c1d95 !important; color: white !important; border: 1px solid #8b5cf6 !important;
}
.gradio-container input[type="radio"] { accent-color: #6366f1; }
.quiz-status { color: #c4b5fd !important; }
.footer { color: #cbd5e1 !important; text-align: center; padding: 12px; }
@media (max-width: 800px) {
    .main-title { padding: 18px; }
    .panel { padding: 12px !important; }
}
"""


with gr.Blocks(
    title="AI Student Study Assistant",
    theme=gr.themes.Soft(
        primary_hue="violet", secondary_hue="blue", neutral_hue="slate"
    ),
    css=CSS
) as app:
    gr.HTML("""
    <div class="main-title">
      <h1>🎓 AI Student Study Assistant</h1>
      <p>Learn smarter&nbsp; • &nbsp;Revise faster&nbsp; • &nbsp;Practice better</p>
    </div>
    <div class="tagline">✨ Your personal AI tutor for notes, revision and practice ✨</div>
    """)

    with gr.Row(equal_height=False):
        with gr.Column(scale=1):
            with gr.Column(elem_classes=["panel"]):
                gr.Markdown("## 📚 Start Learning")
                notes = gr.Textbox(
                    label="Your Study Notes",
                    placeholder="Paste your class notes or study material here...",
                    lines=8
                )
                with gr.Row():
                    summary_btn = gr.Button("✨ Generate Summary", variant="primary")
                    quiz_btn = gr.Button("🧠 Generate Quiz", variant="secondary")
                clear_btn = gr.Button("🗑️ Clear")

            with gr.Column(elem_classes=["panel"]):
                gr.Markdown("## 📖 Simple Summary")
                summary_output = gr.Markdown()
                gr.Markdown("## ⭐ Important Points & Quick Revision")
                points_output = gr.Markdown()

        with gr.Column(scale=1):
            with gr.Column(elem_classes=["panel"]):
                gr.Markdown("## 📘 Study Dashboard")
                gr.Markdown(
                    "Your generated summary, key concepts and revision tips will appear on the left. "
                    "Use the quiz section below to test what you learned."
                )
                gr.Markdown("### 💡 How to use")
                gr.Markdown(
                    "- Paste your study notes.\n"
                    "- Select **Generate Summary** to get easy explanations.\n"
                    "- Select **Generate Quiz** to create five MCQs.\n"
                    "- Submit your answers to see your score and explanations."
                )

            with gr.Column(elem_classes=["panel"]):
                gr.Markdown("## 📝 Knowledge Check")
                quiz_status = gr.Markdown(elem_classes=["quiz-status"])
                quiz_questions = gr.State([])
                q1 = gr.Radio(label="Question 1", choices=[], visible=False)
                q2 = gr.Radio(label="Question 2", choices=[], visible=False)
                q3 = gr.Radio(label="Question 3", choices=[], visible=False)
                q4 = gr.Radio(label="Question 4", choices=[], visible=False)
                q5 = gr.Radio(label="Question 5", choices=[], visible=False)
                submit_btn = gr.Button("✅ Submit Quiz", variant="primary", visible=False)
                result = gr.Markdown()

    gr.HTML('<div class="footer">✨ Build your skills • Create a better future ✨</div>')

    summary_btn.click(
        fn=study_assistant, inputs=notes,
        outputs=[summary_output, points_output]
    )
    quiz_btn.click(
        fn=make_quiz, inputs=notes,
        outputs=[quiz_questions, quiz_status]
    ).then(
        fn=show_quiz, inputs=quiz_questions,
        outputs=[q1, q2, q3, q4, q5, submit_btn]
    )
    submit_btn.click(
        fn=grade_quiz, inputs=[quiz_questions, q1, q2, q3, q4, q5],
        outputs=result
    )
    clear_btn.click(
        fn=clear_all,
        outputs=[notes, summary_output, points_output, quiz_questions,
                 quiz_status, q1, q2, q3, q4, q5, submit_btn, result]
    )


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 10000))
    )
