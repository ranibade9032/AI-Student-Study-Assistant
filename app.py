
import os
import json
import gradio as gr
from google import genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None
MODEL = "gemini-2.5-flash"


def ask_gemini(prompt):
    if client is None:
        return "Error: GEMINI_API_KEY is missing. Set it in Render Environment Variables."
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return response.text or "No response received. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"


def study_assistant(notes):
    if not notes or not notes.strip():
        return "Please enter your study notes first.", ""

    prompt = f"""
    You are a helpful student study assistant.
    Explain using simple English.

    STUDY NOTES:
    {notes}

    Return:
    SUMMARY:
    Write a clear and easy-to-understand summary.

    IMPORTANT POINTS:
    Give the most important points as a bullet list.
    """
    answer = ask_gemini(prompt)

    if answer.startswith("Error:"):
        return answer, ""

    if "IMPORTANT POINTS:" in answer:
        parts = answer.split("IMPORTANT POINTS:", 1)
        summary = parts[0].replace("SUMMARY:", "").strip()
        points = parts[1].strip()
        return summary, points

    return answer, "Review the key ideas from your summary."


def make_quiz(notes):
    if not notes or not notes.strip():
        return [], "Please enter your study notes first."

    prompt = f"""
    Create exactly 5 multiple-choice questions using ONLY these notes.
    Return valid JSON, with no markdown fences.
    Format:
    [
      {{
        "question": "Question text",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "Option A",
        "explanation": "Short explanation"
      }}
    ]

    Notes:
    {notes}
    """

    answer = ask_gemini(prompt)
    if answer.startswith("Error:"):
        return [], answer

    try:
        start = answer.find("[")
        end = answer.rfind("]") + 1
        questions = json.loads(answer[start:end])

        if not isinstance(questions, list) or not questions:
            return [], "Could not create a quiz. Please try again."

        for item in questions:
            if not all(k in item for k in
                       ("question", "options", "answer", "explanation")):
                return [], "Quiz format was invalid. Please try again."
            if len(item["options"]) != 4:
                return [], "Quiz options were invalid. Please try again."

        return questions[:5], f"{min(len(questions), 5)} questions ready!"
    except (ValueError, TypeError, json.JSONDecodeError):
        return [], "Could not read the quiz. Please click Generate Quiz again."


def display_quiz(questions):
    if not questions:
        return (
            gr.update(choices=[], value=None, visible=False),
            gr.update(choices=[], value=None, visible=False),
            gr.update(choices=[], value=None, visible=False),
            gr.update(choices=[], value=None, visible=False),
            gr.update(choices=[], value=None, visible=False),
            gr.update(visible=False)
        )

    radios = []
    for i in range(5):
        if i < len(questions):
            q = questions[i]
            radios.append(
                gr.update(
                    label=f"{i + 1}. {q['question']}",
                    choices=q["options"],
                    value=None,
                    visible=True
                )
            )
        else:
            radios.append(
                gr.update(choices=[], value=None, visible=False)
            )

    return (*radios, gr.update(visible=True))


def grade_quiz(questions, a1, a2, a3, a4, a5):
    if not questions:
        return "Please generate a quiz first."

    answers = [a1, a2, a3, a4, a5]
    score = 0
    feedback = []

    for i, q in enumerate(questions):
        selected = answers[i]
        correct = q["answer"]

        if selected == correct:
            score += 1
            result = "✅ Correct"
        else:
            result = f"❌ Correct answer: {correct}"

        feedback.append(
            f"**Q{i + 1}: {result}**\n\n"
            f"{q['explanation']}"
        )

    return (
        f"# 🎯 Your Score: {score}/{len(questions)}\n\n"
        + "\n\n---\n\n".join(feedback)
    )


CUSTOM_CSS = """
.gradio-container {
    background: linear-gradient(135deg, #0f172a, #312e81, #581c87) !important;
    color: white !important;
}
.main-title {
    text-align: center;
    padding: 28px 15px;
    border-radius: 20px;
    background: linear-gradient(100deg, #2563eb, #7c3aed, #c026d3);
    color: white;
    margin-bottom: 18px;
    box-shadow: 0 8px 30px #00000040;
}
.main-title h1 {
    color: white !important;
    font-size: 32px !important;
}
.subtitle {
    text-align: center;
    color: #e0e7ff;
    font-size: 16px;
    margin-bottom: 22px;
}
.panel {
    border: 1px solid #ffffff30 !important;
    border-radius: 18px !important;
    background: #ffffff12 !important;
    padding: 18px !important;
}
button {
    border-radius: 12px !important;
    font-weight: 600 !important;
}
"""


with gr.Blocks(
    title="AI Student Study Assistant",
    theme=gr.themes.Soft(
        primary_hue="violet",
        secondary_hue="blue",
        neutral_hue="slate"
    ),
    css=CUSTOM_CSS
) as app:

    gr.HTML("""
    <div class="main-title">
        <h1>🎓 AI Student Study Assistant</h1>
        <p>Learn smarter • Revise faster • Practice better</p>
    </div>
    <div class="subtitle">
        Turn your study notes into simple summaries, key points, and quizzes.
    </div>
    """)

    with gr.Column(elem_classes=["panel"]):
        notes = gr.Textbox(
            label="📚 Your Study Notes",
            placeholder="Paste your class notes or study material here...",
            lines=10
        )

        with gr.Row():
            summary_btn = gr.Button("✨ Generate Summary", variant="primary")
            quiz_btn = gr.Button("🧠 Generate Quiz", variant="secondary")

    with gr.Column(elem_classes=["panel"]):
        gr.Markdown("## 📖 Study Summary")
        summary_output = gr.Markdown()

        gr.Markdown("## ⭐ Important Points")
        points_output = gr.Markdown()

    summary_btn.click(
        fn=study_assistant,
        inputs=notes,
        outputs=[summary_output, points_output]
    )

    with gr.Column(elem_classes=["panel"]):
        gr.Markdown("## 📝 Knowledge Check")

        quiz_status = gr.Textbox(
            label="Quiz Status",
            interactive=False
        )
        quiz_questions = gr.State([])

        q1 = gr.Radio(choices=[], label="Question 1", visible=False)
        q2 = gr.Radio(choices=[], label="Question 2", visible=False)
        q3 = gr.Radio(choices=[], label="Question 3", visible=False)
        q4 = gr.Radio(choices=[], label="Question 4", visible=False)
        q5 = gr.Radio(choices=[], label="Question 5", visible=False)

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


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 10000))
    )
