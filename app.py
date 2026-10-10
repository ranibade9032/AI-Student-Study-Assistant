
import os
import gradio as gr
from google import genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

client = genai.Client(api_key=API_KEY) if API_KEY else None


def ask_gemini(prompt):
    if client is None:
        return "Error: GEMINI_API_KEY is missing. Check your .env or Render environment variables."

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text or "No response received. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"


def summarize_notes(notes, summary_type):
    if not notes or not notes.strip():
        return "Please enter your study notes first."

    prompts = {
        "Simple Summary": "Explain these study notes in simple English. Keep the meaning accurate.",
        "Important Points": "Extract the most important points from these study notes as clear bullet points.",
        "Quick Revision": "Create short exam revision notes with key terms, definitions and important facts."
    }

    prompt = f"""
    You are an AI Student Study Assistant.

    Task: {prompts[summary_type]}

    Study notes:
    {notes}
    """
    return ask_gemini(prompt)


def generate_mcqs(notes):
    if not notes or not notes.strip():
        return "Please enter your study notes first."

    prompt = f"""
    Create exactly 5 multiple-choice questions using only these study notes.
    Give four options (A, B, C, D) for each question.
    Put the correct answer after each question.
    Keep the questions clear and suitable for students.

    Study notes:
    {notes}
    """
    return ask_gemini(prompt)


def check_quiz(notes, answers):
    if not notes or not notes.strip():
        return "Please enter your study notes first."

    if not answers or not answers.strip():
        return "Please enter your quiz answers first."

    prompt = f"""
    Check the student's answers using the study notes.
    Explain which answers are correct or incorrect.
    Give the correct answer for any incorrect response.
    Do not invent information that is not supported by the notes.

    Study notes:
    {notes}

    Student answers:
    {answers}
    """
    return ask_gemini(prompt)


def clear_all():
    return "", "Simple Summary", "", "", ""


with gr.Blocks(title="StudyFlow | AI Student Study Assistant") as demo:
    gr.Markdown(
        """
        # StudyFlow
        ### AI Student Study Assistant
        Turn your study notes into summaries, revision points and practice questions.
        """
    )

    notes = gr.Textbox(
        label="Your Study Notes",
        placeholder="Paste your notes here...",
        lines=10
    )

    summary_type = gr.Radio(
        choices=[
            "Simple Summary",
            "Important Points",
            "Quick Revision"
        ],
        value="Simple Summary",
        label="Choose what you need"
    )

    with gr.Row():
        summarize_btn = gr.Button("Generate Summary", variant="primary")
        mcq_btn = gr.Button("Generate 5 MCQs")

    summary_output = gr.Textbox(
        label="Study Notes Result",
        lines=10
    )

    gr.Markdown("## Quiz Practice")

    answers = gr.Textbox(
        label="Your Quiz Answers",
        placeholder="Enter your answers, for example: 1-A, 2-C, 3-B...",
        lines=4
    )

    check_btn = gr.Button("Check My Answers", variant="primary")
    quiz_output = gr.Textbox(label="Quiz Feedback", lines=8)

    clear_btn = gr.Button("Clear All")

    summarize_btn.click(
        fn=summarize_notes,
        inputs=[notes, summary_type],
        outputs=summary_output
    )

    mcq_btn.click(
        fn=generate_mcqs,
        inputs=notes,
        outputs=summary_output
    )

    check_btn.click(
        fn=check_quiz,
        inputs=[notes, answers],
        outputs=quiz_output
    )

    clear_btn.click(
        fn=clear_all,
        inputs=[],
        outputs=[
            notes,
            summary_type,
            summary_output,
            answers,
            quiz_output
        ]
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port
    )
