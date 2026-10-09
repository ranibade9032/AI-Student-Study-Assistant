Nee current code lo `with gr.Blocks(title="AI Student Study Assistant") as app:` daggara nunchi `app.launch(...)` varaku unna part ni maatrame replace cheyyi. Paina functions ni delete cheyyaku.

```python
with gr.Blocks(
    title="AI Student Study Assistant",
    theme=gr.themes.Soft(
        primary_hue="violet",
        secondary_hue="blue",
        neutral_hue="slate"
    ),
    css="""
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
        font-size: 34px !important;
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
            summary_btn = gr.Button(
                "✨ Generate Summary",
                variant="primary"
            )
            quiz_btn = gr.Button(
                "🧠 Generate Quiz",
                variant="secondary"
            )

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
```
