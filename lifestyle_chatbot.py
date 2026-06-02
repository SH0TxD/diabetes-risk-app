import streamlit as st
from langchain_community.llms import Ollama


SYSTEM_RULES = """
You are a private lifestyle assistant for a type 2 diabetes risk-awareness app.

Your role:
- Give general lifestyle education.
- Help users understand healthy habits.
- Explain risk factors in simple language.
- Encourage users to consult a doctor when risk is moderate, high, or unclear.
- Help users prepare questions for their doctor.

You must not:
- Diagnose diabetes or any disease.
- Prescribe medication.
- Change medication instructions.
- Tell users to stop medication.
- Replace a doctor.
- Give emergency medical advice beyond telling the user to seek urgent care.

Keep answers practical, kind, and short.
Always remind the user that medical decisions should be discussed with a healthcare professional.
"""


def build_user_context(user, result):
    if user is None or result is None:
        return """
No risk assessment has been completed yet.
Tell the user they can still ask general lifestyle questions, but for personalized advice they should complete the risk assessment first.
"""

    return f"""
User risk assessment summary:
- Age: {user.get("age")}
- Sex: {user.get("sex")}
- BMI: {user.get("bmi")}
- Family history: {user.get("family_history")}
- Activity level: {user.get("activity_level")}
- Sugar intake: {user.get("sugar_drinks")}
- Smoking: {user.get("smoking")}
- Sleep quality: {user.get("sleep_quality")}
- Blood pressure: {user.get("blood_pressure")}
- HbA1c: {user.get("hba1c")}
- Fasting glucose: {user.get("fasting_glucose")}

Risk result:
- Category: {result.get("category")}
- Score: {result.get("score")}
- Reasons: {result.get("reasons")}
- Important flags: {result.get("urgent_flags")}
- Recommended next step: {result.get("next_step")}
"""


def render_lifestyle_chatbot():
    st.header("AI Lifestyle Advice")
    st.write(
        "Ask questions about healthy habits, diabetes prevention, exercise, diet, sleep, "
        "and what to discuss with your doctor."
    )

    st.warning(
        "This chatbot does not diagnose, prescribe, or replace a doctor. "
        "It gives general lifestyle guidance only."
    )

    if "lifestyle_messages" not in st.session_state:
        st.session_state.lifestyle_messages = []

    user_context = build_user_context(
        st.session_state.get("last_user"),
        st.session_state.get("last_result")
    )

    for message in st.session_state.lifestyle_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_question = st.chat_input("Ask about lifestyle, habits, diet, exercise, or prevention")

    if user_question:
        st.session_state.lifestyle_messages.append(
            {"role": "user", "content": user_question}
        )

        with st.chat_message("user"):
            st.write(user_question)

        with st.spinner("Thinking..."):
            llm = Ollama(model="mistral", temperature=0.2)

            previous_chat = ""
            for msg in st.session_state.lifestyle_messages[-8:]:
                previous_chat += f'{msg["role"]}: {msg["content"]}\n'

            prompt = f"""
{SYSTEM_RULES}

{user_context}

Recent conversation:
{previous_chat}

User question:
{user_question}

Assistant answer:
"""

            answer = llm.invoke(prompt)

        st.session_state.lifestyle_messages.append(
            {"role": "assistant", "content": answer}
        )

        with st.chat_message("assistant"):
            st.write(answer)
