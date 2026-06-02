import streamlit as st
from langchain_community.llms import Ollama


SYSTEM_RULES = """
You are a private lifestyle assistant for DiaRisk Bosnia, a type 2 diabetes risk-awareness app.

Your role:
- Give short, practical lifestyle advice.
- Help users understand prevention habits.
- Use the user's risk assessment context when available.
- Encourage medical consultation when risk is elevated, labs are abnormal, or symptoms are concerning.

You must not:
- Diagnose diabetes or any disease.
- Prescribe medication.
- Change medication instructions.
- Tell users to stop medication.
- Replace a doctor.

Keep answers practical and not too long.

At the end of every response, ask exactly one short follow-up question that helps guide the user to the next useful step.

The question should be specific and practical, for example:
- Would you like help making a 7-day walking plan?
- Would you like help preparing questions for your doctor?
- Would you like help choosing one habit to start with this week?
- Would you like help understanding your Prevention Passport?
- Would you like help deciding what to track next?

Do not ask more than one question.
Do not offer to diagnose, prescribe, or replace a doctor.
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
            llm = Ollama(model="llama3.2:3b", temperature=0.2)

            previous_chat = ""
            for msg in st.session_state.lifestyle_messages[-8:]:
                previous_chat += f'{msg["role"]}: {msg["content"]}\n'

            prompt = f"""
            {SYSTEM_RULES}

            User context:
            {user_context}

            Recent conversation:
            {previous_chat}

            User question:
            {user_question}

            Answer briefly and end with exactly one helpful follow-up question:
            """

            answer = llm.invoke(prompt)

        st.session_state.lifestyle_messages.append(
            {"role": "assistant", "content": answer}
        )

        with st.chat_message("assistant"):
            st.write(answer)