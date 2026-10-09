import os
import json
import re
import time
import gradio as gr
from dotenv import load_dotenv
from google import genai

# Load API key from .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key) if api_key else None


# Call Gemini AI
def ask_gemini(prompt):
    if client is None:
        raise ValueError(
            "API key not found. Check GEMINI_API_KEY in your .env file."
        )

    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            if not response.text:
                raise ValueError("AI returned an empty response.")

            return response.text

        except Exception as e:
            last_error = e
            message = str(e).upper()

            if (
                ("503" in message or "UNAVAILABLE" in message)
                and attempt < 2
            ):
                time.sleep(2 * (attempt + 1))
                continue

            raise last_error

    raise last_error


# Generate summary and important points
def study_assistant(notes):
    if not notes or not notes.strip():
        return "Please enter your study notes.", ""

    try:
        prompt = f"""
You are a helpful student study assistant.

Read the notes below and provide:
1. A simple, easy-to-understand summary.
2. Exactly five important points.

Use simple English.

Follow this format:

SUMMARY:
Write the summary here.

IMPORTANT POINTS:
1. Point one
2. Point two
3. Point three
4. Point four
5. Point five

STUDY NOTES:
{notes}
"""
        answer = ask_gemini(prompt)

        parts = re.split(
            r"IMPORTANT POINTS\s*:",
            answer,
            maxsplit=1,
            flags=re.IGNORECASE
        )

        summary = parts[0].strip()
        points = parts[1].strip() if len(parts) > 1 else ""

        return summary, points

    except Exception as e:
        return f"Summary error: {e}", ""


# Generate quiz questions
def make_quiz(notes):
    if not notes or not notes.strip():
        return [], "Please enter your study notes first."

    try:
        prompt = f"""
Create exactly 5 multiple-choice quiz questions using the study notes.

Return ONLY valid JSON. Do not use Markdown code fences.

Use this exact structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": 0,
      "explanation": "Explain the correct answer simply."
    }}
  ]
}}

Rules:
- Create exactly 5 questions.
- Each question must have exactly 4 options.
- The answer must be an integer from 0 to 3.
- The answer index must match the correct option.
- Explanations must be short and simple.

STUDY NOTES:
{notes}
"""

        response = ask_gemini(prompt)

        # Remove Markdown code fences if present
        cleaned = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            response.strip(),
            flags=re.IGNORECASE
        )

        data = json.loads(cleaned)
        questions = data.get("questions", [])

        if len(questions) != 5:
            raise ValueError("AI did not return exactly 5 questions.")

        for q in questions:
            if not isinstance(q.get("question"), str):
                raise ValueError("A question is missing.")

            if not isinstance(q.get("options"), list):
                raise ValueError("Question options are missing.")

            if len(q["options"]) != 4:
                raise ValueError("Each question must have 4 options.")

            if not isinstance(q.get("answer"), int):
                raise ValueError("The correct answer index is invalid.")

            if q["answer"] not in range(4):
                raise ValueError("The answer index must be 0, 1, 2, or 3.")

            if not q.get("explanation"):
                q["explanation"] = "Review the study notes."

        return questions, "Quiz generated successfully! Answer all 5 questions."

    except Exception as e:
        return [], f"Quiz generation failed: {type(e).__name__}: {e}"


# Display quiz questions
def display_quiz(questions):
    updates = []

    for i in range(5):
        if len(questions) == 5:
            q = questions[i]
            updates.append(
                gr.update(
                    label=f"Question {i + 1}: {q['question']}",
                    choices=q["options"],
                    value=None,
                    visible=True
                )
            )
        else:
            updates.append(
                gr.update(
                    label=f"Question {i + 1}",
                    choices=[],
                    value=None,
                    visible=False
                )
            )

    updates.append(gr.update(visible=(len(questions) == 5)))
    return tuple(updates)


# Check quiz answers
def grade_quiz(questions, *answers):
    if len(questions) != 5:
        return (
            "Quiz was not generated. Check the Quiz Error box above "
            "and try again."
        )

    if any(answer is None for answer in answers):
        return "Please answer all 5 questions before submitting."

    score = 0
    feedback = []

    for i, (q, answer) in enumerate(zip(questions, answers)):
        correct_index = q["answer"]
        correct_option = q["options"][correct_index]

        if answer == correct_option:
            score += 1
            feedback.append(
                f"**Q{i + 1}: Correct!**\n\n"
                f"{q.get('explanation', '')}"
            )
        else:
            feedback.append(
                f"**Q{i + 1}: Incorrect.** Correct answer: "
                f"{correct_option}\n\n{q.get('explanation', '')}"
            )

    result = f"# Your Score: {score}/5\n\n"
    result += "\n\n".join(feedback)

    return result


# User interface
with gr.Blocks(title="AI Student Study Assistant") as app:
    gr.Markdown("# AI Student Study Assistant")
    gr.Markdown(
        "Enter your study notes to generate a summary, "
        "important points, and a quiz."
    )

    notes = gr.Textbox(
        label="Enter Your Study Notes",
        placeholder="Paste your study notes here...",
        lines=10
    )

    with gr.Row():
        summary_btn = gr.Button("Generate Summary")
        quiz_btn = gr.Button("Generate Quiz")

    gr.Markdown("## Study Summary")
    summary_output = gr.Markdown()

    gr.Markdown("## Important Points")
    points_output = gr.Markdown()

    summary_btn.click(
        fn=study_assistant,
        inputs=notes,
        outputs=[summary_output, points_output]
    )

    gr.Markdown("## Quiz")

    # This box displays the actual error if quiz generation fails
    quiz_status = gr.Textbox(
        label="Quiz Error / Status",
        interactive=False
    )

    quiz_questions = gr.State([])

    q1 = gr.Radio(choices=[], label="Question 1", visible=False)
    q2 = gr.Radio(choices=[], label="Question 2", visible=False)
    q3 = gr.Radio(choices=[], label="Question 3", visible=False)
    q4 = gr.Radio(choices=[], label="Question 4", visible=False)
    q5 = gr.Radio(choices=[], label="Question 5", visible=False)

    submit_btn = gr.Button("Submit Quiz", visible=False)
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
    app.launch()