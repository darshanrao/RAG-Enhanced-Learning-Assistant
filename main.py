import streamlit as st
import random
from fpdf import FPDF
from io import BytesIO
import os
import requests
import json

# Set up the landing page title
st.title("QuizzIt!")

# Session state to manage quiz state
if "quiz_state" not in st.session_state:
    st.session_state.quiz_state = "landing"
    st.session_state.questions = []
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.feedback = ""
    st.session_state.short_ans = None
    st.session_state.selected_option = None
    st.session_state.handout_generated = False
    st.session_state.incorrect_answers = []

def handle_submit(filepath, slider_val, question_type, user_prompt):
    """Handle submit button click on landing page."""
    data = {"file_name": filepath,
        "type_of_question": question_type,
        "number_of_questions": slider_val,
        "user_prompt_text": user_prompt}
    st.session_state.questions = requests.post(url="http://127.0.0.1:5000/upload-embedding", json=data)
    st.session_state.quiz_state = "quiz"
    st.session_state.current_question = 0
    st.session_state.feedback = ""

def handle_handout_gen():
    """Handle handout generation."""
    st.session_state.quiz_state = "handout"
    st.session_state.handout_generated = True

def handle_submit_answer(question_type):
    """Handle submit answer button click on quiz page."""
    current_index = st.session_state.current_question
    questions = st.session_state.questions.json()
    question = questions[current_index]

    if question_type == "mcq":
        if st.session_state.selected_option is not None:
            if st.session_state.selected_option == question["options"][question["correct_answer"]]:
                st.session_state.feedback = "<span style='color: green; font-weight: bold;'>Correct answer!</span>"
                st.session_state.score += 1
            else:
                st.session_state.feedback = f"<span style='color: red; font-weight: bold;'>Incorrect answer. The correct answer is {question['correct_answer']}.</span>"
                st.session_state.incorrect_answers.append({
                    "question": question["question"],
                    "correct_answer": question["correct_answer"],
                    "selected_answer": st.session_state.selected_option
                })
        else:
            st.warning("Please select an answer before submitting.")
    else:
        if st.session_state.short_ans is not None:
            data = {"question": question['question'],
                    "llm_answer": question['llm_answer'],
                    "answer": st.session_state.short_ans}
            results = requests.post(url="http://127.0.0.1:5000/verify-short", json=data).json()
            # results = results.json()
            print(results)
            if results['correct_answer'] == -1:
                st.session_state.feedback = f"<span style='color: red; font-weight: bold;'>Incorrect answer. Explanation: {results['explanation']}.</span>"
                st.session_state.incorrect_answers.append({
                    "question": question["question"],
                    "correct_answer": question["llm_answer"],
                    "selected_answer": st.session_state.short_ans
                })

def handle_next_question():
    """Handle next question button click."""
    if st.session_state.selected_option is not None or st.session_state.short_ans is not None:
        st.session_state.current_question += 1
        st.session_state.feedback = ""
        st.session_state.short_ans = None
        st.session_state.selected_option = None
    else:
        st.warning("Please select/type an answer before proceeding.")

def handle_end_quiz():
    """Handle end quiz button click."""

    if "uploaded_file_path" in st.session_state and os.path.exists(st.session_state.uploaded_file_path):
        os.remove(st.session_state.uploaded_file_path)
        st.session_state.uploaded_file_path = None

    st.session_state.quiz_state = "landing"
    st.session_state.questions = []
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.feedback = ""
    st.session_state.short_ans = None
    st.session_state.selected_option = None
    st.session_state.incorrect_answers = []

def handle_review_mistakes():
    """Handle the Review Mistakes button click."""
    st.session_state.quiz_state = "review_mistakes"

def handle_end_review():
    """Handle the end review button click."""
    st.session_state.quiz_state = "landing"
    st.session_state.questions = []
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.feedback = ""
    st.session_state.short_ans = None
    st.session_state.selected_option = None
    st.session_state.incorrect_answers = []

def generate_pdf_handout():
    """Generate a sample handout PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, "Generated Handout", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(0, 10, "Thank you for using QuizzIt!", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 10, "This is a sample handout generated by the application. Add your custom content here.")

    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest="S").encode("latin1"))
    pdf_output.seek(0)
    return pdf_output

# Landing page logic
if st.session_state.quiz_state == "landing":
    file_path = None
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    if uploaded_file is not None:
        filename = uploaded_file.name[:-4]
        file_path = f"{filename}_{random.randint(1000, 9999)}.pdf"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        st.success(f"PDF uploaded successfully!")
        st.session_state.uploaded_file_path = file_path 

    st.session_state.slider_value = st.slider("Choose the number of questions (1-5)", min_value=1, max_value=5, value=3)

    st.session_state.question_type = st.radio(
        "Select question type:",
        ("MCQ", "Short Answer")
    )

    if st.session_state.question_type == "MCQ":
        st.session_state.question_type = "mcq"
    else:
        st.session_state.question_type = "short"

    text_input = st.text_input("Enter your text here")

    col1, col2, col3 = st.columns([3, 5, 14])
    with col1:
        st.button("Submit", on_click=handle_submit, args=(file_path, st.session_state.slider_value, st.session_state.question_type, text_input))
    with col2:
        st.button("Generate Handout", on_click=handle_handout_gen)

# Quiz page logic
elif st.session_state.quiz_state == "quiz":
    questions = st.session_state.questions.json()
    current_index = st.session_state.current_question
    print(questions)
    tot_ques = len(questions)
    if current_index < tot_ques:
        question = questions[current_index]
        st.write(f"Question {current_index + 1}/{tot_ques}: {question['question']}")

        if st.session_state.question_type == "mcq":
            st.session_state.selected_option = st.radio(
                "Choose an option:",
                question["options"],
                index=0,
                key=f"q{current_index}"
            )
        else:
            st.session_state.short_ans = st.text_area("Enter your answer", placeholder="Your answer here ...")

        st.button("Submit Answer", key=f"submit_{current_index}", on_click=handle_submit_answer, args=(st.session_state.question_type, ))

        if st.session_state.feedback:
            st.markdown(st.session_state.feedback, unsafe_allow_html=True)

        st.button("Next Question", key=f"next_{current_index}", on_click=handle_next_question)
    else:
        st.write(f"Quiz completed! Your score: {st.session_state.score}/{len(questions)}")
        col1, col2 = st.columns(2)
        with col1:
            st.button("End Quiz", on_click=handle_end_quiz)
        with col2:
            st.button("Review Mistakes", on_click=handle_review_mistakes)

# Review mistakes page logic
elif st.session_state.quiz_state == "review_mistakes":
    st.header("Review Your Mistakes")
    if st.session_state.incorrect_answers:
        for idx, mistake in enumerate(st.session_state.incorrect_answers, start=1):
            st.write(f"**Question {idx}:** {mistake['question']}")
            st.write(f"**Your Answer:** {mistake['selected_answer']}")
            st.write(f"**Correct Answer:** {mistake['correct_answer']}")
            st.write("---")
    else:
        st.write("Great job! You got all the answers correct.")

    st.button("Go Back to Home", on_click=handle_end_review)

# Handout page logic
elif st.session_state.quiz_state == "handout":
    st.header("Generated Handout")
    if st.session_state.handout_generated:
        pdf_file = generate_pdf_handout()
        st.download_button(
            label="Download Handout",
            data=pdf_file,
            file_name="handout.pdf",
            mime="application/pdf"
        )
        st.button("Go Back", on_click=handle_end_quiz)
