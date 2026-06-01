import streamlit as st
import pandas as pd
import plotly.express as px
from lifestyle_chatbot import render_lifestyle_chatbot

from modules.risk_engine import calculate_bmi, calculate_diabetes_risk
from modules.ai_advisor import generate_advice
from modules.storage import add_health_log, load_health_logs

st.set_page_config(
    page_title="DiaRisk Bosnia",
    page_icon="🩺",
    layout="wide"
)

st.title("DiaRisk Bosnia")
st.caption("Type 2 diabetes risk awareness prototype — preventive support, not diagnosis.")

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Risk Assessment",
        "AI Lifestyle Advice",
        "Health Tracking",
        "Find Doctors",
        "About & Safety"
    ]
)

if "last_user" not in st.session_state:
    st.session_state.last_user = None

if "last_result" not in st.session_state:
    st.session_state.last_result = None


def optional_number(label, min_value, max_value, step, help_text):
    enabled = st.checkbox(f"Add {label}", value=False)
    if enabled:
        return st.number_input(label, min_value=min_value, max_value=max_value, step=step, help=help_text)
    return None


if page == "Risk Assessment":
    st.header("Type 2 Diabetes Risk Assessment")
    st.write(
        "Enter basic personal, family, lifestyle, and optional lab information. "
        "The app estimates risk indicators and explains the main contributing factors."
    )

    with st.form("risk_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Personal information")
            age = st.number_input("Age", min_value=10, max_value=100, value=35)
            sex = st.selectbox("Sex", ["Female", "Male", "Other / prefer not to say"])
            height_cm = st.number_input("Height (cm)", min_value=100.0, max_value=230.0, value=170.0, step=1.0)
            weight_kg = st.number_input("Weight (kg)", min_value=30.0, max_value=250.0, value=75.0, step=0.5)

            bmi = calculate_bmi(height_cm, weight_kg)
            st.metric("Calculated BMI", bmi)

            family_history = st.multiselect(
                "Which family members have type 2 diabetes?",
                ["Parent", "Sibling", "Grandparent", "Other relative"]
            )

            gestational_diabetes = st.selectbox(
                "History of gestational diabetes?",
                ["No/not applicable", "Yes"]
            )

        with col2:
            st.subheader("Lifestyle and medical indicators")
            activity_level = st.selectbox(
                "Physical activity level",
                ["Low", "Moderate", "High"],
                help="Low = mostly sedentary. High = regular weekly exercise."
            )
            sugar_drinks = st.selectbox(
                "Sugary drinks / sweets intake",
                ["Rarely", "Sometimes", "Often"]
            )
            smoking = st.selectbox("Smoking", ["No", "Yes"])
            sleep_quality = st.selectbox("Sleep quality", ["Good", "Average", "Poor"])
            blood_pressure = st.selectbox("Blood pressure", ["Normal/unknown", "High"])

            st.subheader("Optional lab values")
            hba1c = optional_number(
                "HbA1c (%)",
                min_value=3.0,
                max_value=15.0,
                step=0.1,
                help_text="Example: 5.6, 6.1, 7.0"
            )
            fasting_glucose = optional_number(
                "fasting glucose (mg/dL)",
                min_value=50,
                max_value=400,
                step=1,
                help_text="Use mg/dL for this prototype."
            )

        submitted = st.form_submit_button("Calculate risk indicators")

    if submitted:
        user = {
            "age": age,
            "sex": sex,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "bmi": bmi,
            "family_history": family_history,
            "gestational_diabetes": gestational_diabetes,
            "activity_level": activity_level,
            "sugar_drinks": sugar_drinks,
            "smoking": smoking,
            "sleep_quality": sleep_quality,
            "blood_pressure": blood_pressure,
            "hba1c": hba1c,
            "fasting_glucose": fasting_glucose,
        }

        result = calculate_diabetes_risk(user)

        st.session_state.last_user = user
        st.session_state.last_result = result

        st.divider()
        st.subheader("Result")

        c1, c2, c3 = st.columns(3)
        c1.metric("Risk category", result["category"])
        c2.metric("Risk score", result["score"])
        c3.metric("BMI", bmi)

        if result["category"] == "High":
            st.error(result["next_step"])
        elif result["category"] == "Moderate":
            st.warning(result["next_step"])
        else:
            st.success(result["next_step"])

        if result["urgent_flags"]:
            st.subheader("Important lab-related warning")
            for flag in result["urgent_flags"]:
                st.error(flag)

        st.subheader("Main contributing factors")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

        st.info(
            "This is not a diagnosis. It is a preventive support tool. "
            "Only a licensed healthcare professional can diagnose diabetes or recommend treatment."
        )


elif page == "AI Lifestyle Advice":
    render_lifestyle_chatbot()


elif page == "Health Tracking":
    st.header("Health Tracking")
    st.write("Log simple health parameters over time. This helps users notice trends before problems become advanced.")

    with st.form("tracking_form"):
        col1, col2 = st.columns(2)

        with col1:
            weight_log = st.number_input("Weight today (kg)", min_value=30.0, max_value=250.0, value=75.0, step=0.5)
            fasting_log = st.number_input("Fasting glucose (mg/dL)", min_value=0, max_value=400, value=0)
            hba1c_log = st.number_input("HbA1c (%)", min_value=0.0, max_value=15.0, value=0.0, step=0.1)

        with col2:
            bp_log = st.text_input("Blood pressure", placeholder="Example: 120/80")
            notes = st.text_area("Notes", placeholder="Symptoms, diet, exercise, medication reminder, etc.")

        save_log = st.form_submit_button("Save log")

    if save_log:
        add_health_log(
            weight_kg=weight_log if weight_log else None,
            fasting_glucose=fasting_log if fasting_log > 0 else None,
            hba1c=hba1c_log if hba1c_log > 0 else None,
            blood_pressure=bp_log,
            notes=notes,
        )
        st.success("Health log saved.")

    logs = load_health_logs()

    if logs.empty:
        st.info("No health logs yet.")
    else:
        st.subheader("Previous logs")
        st.dataframe(logs, use_container_width=True)

        numeric_cols = ["weight_kg", "fasting_glucose_mg_dl", "hba1c_percent"]
        for col in numeric_cols:
            cleaned = logs.dropna(subset=[col])
            cleaned = cleaned[cleaned[col] != 0]
            if not cleaned.empty:
                fig = px.line(cleaned, x="date", y=col, markers=True, title=f"{col} over time")
                st.plotly_chart(fig, use_container_width=True)


elif page == "Find Doctors":
    st.header("Find Nearby Doctors")
    st.write(
        "For the prototype, this page shows how the app could guide users toward professional care."
    )

    city = st.text_input("Enter city", value="Sarajevo")
    specialty = st.selectbox("Specialty", ["Family medicine doctor", "Endocrinologist", "Diabetologist"])

    query = f"{specialty} near {city}"
    maps_url = "https://www.google.com/maps/search/" + query.replace(" ", "+")

    st.link_button("Open doctor search in Google Maps", maps_url)

    st.info(
        "Future version: integrate verified clinic databases, availability, insurance/health-card eligibility, "
        "and referral pathways."
    )


elif page == "About & Safety":
    st.header("About & Safety")
    st.markdown(
        """
        **Purpose:** DiaRisk Bosnia is a preventive support tool for early type 2 diabetes risk awareness.

        **What it does:**
        - Collects personal, family, lifestyle, and optional lab information
        - Shows an explainable risk category
        - Encourages timely consultation with doctors
        - Helps users track health parameters over time

        **What it does not do:**
        - It does not diagnose diabetes
        - It does not prescribe medication
        - It does not replace a physician
        - It does not tell users to stop or change prescribed treatment

        **Future expansion:**
        - Secure integration with official health-card medical data
        - Validated local risk model using Bosnian clinical data
        - Structured lab report import
        - Verified specialist directory
        - Medication reminders connected to doctor-prescribed therapy
        """
    )
