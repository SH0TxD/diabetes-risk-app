import streamlit as st
import pandas as pd
import plotly.express as px

from lifestyle_chatbot import render_lifestyle_chatbot
from modules.risk_engine import calculate_bmi, calculate_diabetes_risk
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
        "Prevention Passport",
        "AI Lifestyle Advice",
        "Health Tracking",
        "Find Doctors",
        "About & Safety"
    ]
)


# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------

if "last_user" not in st.session_state:
    st.session_state.last_user = None

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "risk_score_result" not in st.session_state:
    st.session_state.risk_score_result = None

if "risk_inputs" not in st.session_state:
    st.session_state.risk_inputs = {
        "age_text": "",
        "sex": None,
        "height_cm_text": "",
        "weight_kg_text": "",
        "waist_cm_text": "",
        "family_history": [],
        "activity_level": None,
        "vegetables_fruits": None,
        "blood_pressure_medication": None,
        "high_blood_glucose_history": None,

        # Extra lifestyle fields, not part of FINDRISC scoring
        "sugar_drinks": None,
        "smoking": None,
        "sleep_quality": None,
        "blood_pressure": None,
        "gestational_diabetes": None,

        # Optional lab fields, not part of FINDRISC scoring
        "has_hba1c": False,
        "hba1c_text": "",
        "has_fasting_glucose": False,
        "fasting_glucose_text": "",
    }


# ------------------------------------------------------------
# INPUT HELPERS
# ------------------------------------------------------------

def number_text_input(label, default_value="", help_text="", key=None):
    """
    Text-based numeric input so users can type values directly with the keyboard/numpad.
    Accepts both decimal dots and decimal commas, for example: 75.5 or 75,5.
    Blank input returns None.
    """
    if default_value is None:
        default_value = ""

    value = st.text_input(label, value=str(default_value), help=help_text, key=key)

    if value is None or str(value).strip() == "":
        return None

    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        st.error(f"Please enter a valid number for {label}.")
        return None


def save_risk_inputs():
    """
    Copy widget values into a permanent dictionary.
    This prevents Risk Assessment inputs from resetting when the user opens another tab/page.
    """
    st.session_state.risk_inputs = {
        "age_text": st.session_state.get("risk_age_text", ""),
        "sex": st.session_state.get("risk_sex"),
        "height_cm_text": st.session_state.get("risk_height_cm_text", ""),
        "weight_kg_text": st.session_state.get("risk_weight_kg_text", ""),
        "waist_cm_text": st.session_state.get("risk_waist_cm_text", ""),
        "family_history": st.session_state.get("risk_family_history", []),
        "activity_level": st.session_state.get("risk_activity_level"),
        "vegetables_fruits": st.session_state.get("risk_vegetables_fruits"),
        "blood_pressure_medication": st.session_state.get("risk_blood_pressure_medication"),
        "high_blood_glucose_history": st.session_state.get("risk_high_blood_glucose_history"),

        # Extra lifestyle fields
        "sugar_drinks": st.session_state.get("risk_sugar_drinks"),
        "smoking": st.session_state.get("risk_smoking"),
        "sleep_quality": st.session_state.get("risk_sleep_quality"),
        "blood_pressure": st.session_state.get("risk_blood_pressure"),
        "gestational_diabetes": st.session_state.get("risk_gestational_diabetes"),

        # Optional lab fields
        "has_hba1c": st.session_state.get("risk_has_hba1c", False),
        "hba1c_text": st.session_state.get("risk_hba1c_text", ""),
        "has_fasting_glucose": st.session_state.get("risk_has_fasting_glucose", False),
        "fasting_glucose_text": st.session_state.get("risk_fasting_glucose_text", ""),
    }


def load_risk_inputs():
    """
    Restore saved values into widget keys before rendering the Risk Assessment page.
    """
    defaults = {
        "age_text": "",
        "sex": None,
        "height_cm_text": "",
        "weight_kg_text": "",
        "waist_cm_text": "",
        "family_history": [],
        "activity_level": None,
        "vegetables_fruits": None,
        "blood_pressure_medication": None,
        "high_blood_glucose_history": None,

        # Extra lifestyle fields
        "sugar_drinks": None,
        "smoking": None,
        "sleep_quality": None,
        "blood_pressure": None,
        "gestational_diabetes": None,

        # Optional lab fields
        "has_hba1c": False,
        "hba1c_text": "",
        "has_fasting_glucose": False,
        "fasting_glucose_text": "",
    }

    saved = st.session_state.get("risk_inputs", defaults)

    key_map = {
        "risk_age_text": "age_text",
        "risk_sex": "sex",
        "risk_height_cm_text": "height_cm_text",
        "risk_weight_kg_text": "weight_kg_text",
        "risk_waist_cm_text": "waist_cm_text",
        "risk_family_history": "family_history",
        "risk_activity_level": "activity_level",
        "risk_vegetables_fruits": "vegetables_fruits",
        "risk_blood_pressure_medication": "blood_pressure_medication",
        "risk_high_blood_glucose_history": "high_blood_glucose_history",

        # Extra lifestyle fields
        "risk_sugar_drinks": "sugar_drinks",
        "risk_smoking": "smoking",
        "risk_sleep_quality": "sleep_quality",
        "risk_blood_pressure": "blood_pressure",
        "risk_gestational_diabetes": "gestational_diabetes",

        # Optional lab fields
        "risk_has_hba1c": "has_hba1c",
        "risk_hba1c_text": "hba1c_text",
        "risk_has_fasting_glucose": "has_fasting_glucose",
        "risk_fasting_glucose_text": "fasting_glucose_text",
    }

    for widget_key, saved_key in key_map.items():
        if widget_key not in st.session_state:
            st.session_state[widget_key] = saved.get(saved_key, defaults[saved_key])


def optional_selectbox(label, options, key, help_text=None):
    """
    Selectbox with a placeholder instead of a default medical answer.
    Returns None until the user chooses a real option.
    """
    placeholder = "Select an option"
    full_options = [placeholder] + options

    current_value = st.session_state.get(key)
    index = full_options.index(current_value) if current_value in full_options else 0

    selected = st.selectbox(
        label,
        full_options,
        index=index,
        key=key,
        help=help_text,
        on_change=save_risk_inputs
    )

    if selected == placeholder:
        return None

    return selected


# ------------------------------------------------------------
# FINDRISC / CARE GUIDANCE HELPERS
# ------------------------------------------------------------

def get_findrisc_score(result):
    """
    Return the FINDRISC score. Falls back to 'score' for compatibility.
    """
    return result.get("findrisc_score", result.get("score", 0))


def render_findrisc_score_card(result):
    """
    Show the FINDRISC score and category with a clear safety note.
    """
    findrisc_score = get_findrisc_score(result)

    st.subheader("FINDRISC screening result")

    c1, c2 = st.columns(2)
    c1.metric("FINDRISC score", findrisc_score)
    c2.metric("Risk category", result.get("category", "Not available"))

    st.caption(
        "Note: FINDRISC is a questionnaire-based screening tool for estimating future type 2 diabetes risk. "
        "This prototype does not diagnose diabetes. HbA1c and fasting glucose are handled separately as lab safety information."
    )


def get_care_guidance(result):
    """
    Translate the FINDRISC category and lab flags into action-based care guidance.
    """
    if result.get("urgent_flags"):
        return {
            "title": "Book a doctor consultation",
            "message": (
                "Some entered lab values need professional review. "
                "This is not a diagnosis, but it would be safest to speak with a healthcare professional."
            )
        }

    category = result.get("category")

    if category in ["Very high", "High"]:
        return {
            "title": "Book a preventive consultation",
            "message": (
                "Your FINDRISC result suggests that a medical checkup would be a smart next step. "
                "A doctor can decide whether screening tests such as HbA1c or fasting glucose are needed."
            )
        }

    if category == "Moderate":
        return {
            "title": "Consider preventive screening",
            "message": (
                "Your FINDRISC result shows some prevention focus areas. "
                "It may be useful to ask your family doctor whether diabetes screening is appropriate."
            )
        }

    if category == "Slightly elevated":
        return {
            "title": "Strengthen prevention habits",
            "message": (
                "Your FINDRISC result suggests some early prevention opportunities. "
                "Small changes in movement, food habits, and follow-up screening can help."
            )
        }

    return {
        "title": "Continue healthy prevention",
        "message": (
            "No major warning pattern was detected from the information provided. "
            "Keep focusing on healthy habits and routine checkups."
        )
    }


def get_latest_assessment():
    """
    Return the latest saved assessment from session state.
    """
    saved = st.session_state.get("risk_score_result")

    if saved is None:
        return None, None, None

    return saved.get("user"), saved.get("result"), saved


# ------------------------------------------------------------
# PREVENTION PASSPORT HELPERS
# ------------------------------------------------------------

def build_prevention_map(user, result):
    """
    Convert the assessment into user-friendly prevention focus areas.
    """
    focus_areas = []

    if user.get("hba1c") is None and user.get("fasting_glucose") is None:
        focus_areas.append({
            "area": "Screening information",
            "status": "Missing",
            "meaning": "HbA1c and fasting glucose were not provided."
        })
    elif result.get("urgent_flags"):
        focus_areas.append({
            "area": "Screening information",
            "status": "Needs doctor review",
            "meaning": "One or more lab values should be discussed with a healthcare professional."
        })
    else:
        focus_areas.append({
            "area": "Screening information",
            "status": "Provided",
            "meaning": "Some lab information was included in the assessment."
        })

    family_history = user.get("family_history", [])
    if any(member in ["Parent", "Sibling"] for member in family_history):
        focus_areas.append({
            "area": "Family pattern",
            "status": "First-degree relative",
            "meaning": "FINDRISC gives more weight to diabetes in a parent or sibling."
        })
    elif family_history:
        focus_areas.append({
            "area": "Family pattern",
            "status": "Second-degree / other relative",
            "meaning": "Family history may still be useful to mention during a doctor visit."
        })
    else:
        focus_areas.append({
            "area": "Family pattern",
            "status": "Not reported",
            "meaning": "No family history was selected."
        })

    bmi = user.get("bmi")
    if bmi is not None and bmi > 30:
        weight_status = "FINDRISC focus"
        weight_meaning = "BMI above 30 adds points in FINDRISC."
    elif bmi is not None and bmi >= 25:
        weight_status = "Mild FINDRISC focus"
        weight_meaning = "BMI between 25 and 30 adds points in FINDRISC."
    else:
        weight_status = "Maintain"
        weight_meaning = "BMI did not add FINDRISC points."

    focus_areas.append({
        "area": "Weight / BMI",
        "status": weight_status,
        "meaning": weight_meaning
    })

    if user.get("waist_cm") is not None:
        focus_areas.append({
            "area": "Waist circumference",
            "status": "Included",
            "meaning": "Waist circumference is part of FINDRISC and was included in the score."
        })
    else:
        focus_areas.append({
            "area": "Waist circumference",
            "status": "Missing",
            "meaning": "Waist circumference is part of FINDRISC but was not provided."
        })

    if user.get("activity_level") == "No":
        focus_areas.append({
            "area": "Movement",
            "status": "Needs attention",
            "meaning": "Less than 30 minutes of daily activity adds points in FINDRISC."
        })
    else:
        focus_areas.append({
            "area": "Movement",
            "status": "Protective habit",
            "meaning": "Daily activity supports diabetes prevention."
        })

    if user.get("vegetables_fruits") == "No":
        focus_areas.append({
            "area": "Food pattern",
            "status": "FINDRISC focus",
            "meaning": "Not eating vegetables, fruits, or berries daily adds points in FINDRISC."
        })
    else:
        focus_areas.append({
            "area": "Food pattern",
            "status": "Protective habit",
            "meaning": "Daily vegetables/fruits/berries support prevention."
        })

    if user.get("sugar_drinks") in ["Sometimes", "Often"]:
        focus_areas.append({
            "area": "Sugary drinks / sweets",
            "status": "Lifestyle focus",
            "meaning": "This is not part of FINDRISC scoring, but it helps personalize the prevention plan."
        })

    if user.get("smoking") == "Yes":
        focus_areas.append({
            "area": "Smoking",
            "status": "Lifestyle focus",
            "meaning": "This is not part of FINDRISC scoring, but it matters for cardiometabolic health."
        })

    if user.get("sleep_quality") == "Poor":
        focus_areas.append({
            "area": "Sleep / recovery",
            "status": "Lifestyle focus",
            "meaning": "This is not part of FINDRISC scoring, but it can affect energy, appetite, and habits."
        })

    return focus_areas


def get_missing_screening_info(user):
    """
    Detect missing information that could make a future doctor visit more complete.
    """
    missing = []

    if user.get("hba1c") is None:
        missing.append("HbA1c result")
    if user.get("fasting_glucose") is None:
        missing.append("Fasting glucose result")
    if user.get("blood_pressure") == "Normal/unknown":
        missing.append("Recent blood pressure value")
    if user.get("waist_cm") is None:
        missing.append("Waist circumference")
    if not user.get("family_history"):
        missing.append("More detailed family history, including age of diagnosis if known")

    missing.append("Date of last preventive checkup")

    return missing


def get_doctor_questions(user, result):
    """
    Generate a doctor conversation card.
    """
    questions = [
        "Based on my FINDRISC result, should I do HbA1c or fasting glucose screening?",
        "How often should I repeat diabetes screening?",
        "Which prevention change would help me most first?"
    ]

    if user.get("family_history"):
        questions.append("Does my family history mean I should start screening earlier or screen more often?")

    if user.get("hba1c") is not None or user.get("fasting_glucose") is not None:
        questions.append("Can you help me interpret these lab values in the context of my overall health?")

    if user.get("blood_pressure_medication") == "Yes" or user.get("blood_pressure") == "High":
        questions.append("Should my blood pressure be monitored together with diabetes prevention?")

    if result.get("urgent_flags"):
        questions.insert(0, "Do any of my entered lab values require follow-up testing or confirmation?")

    return questions


def get_micro_plan(user):
    """
    Generate a simple 7-day prevention plan based on user habits.
    """
    plan = []

    if user.get("sugar_drinks") in ["Sometimes", "Often"]:
        day1 = "Replace one sugary drink or sweet snack with water, tea without sugar, or fruit."
    else:
        day1 = "Keep sugary drinks low and choose water as your default drink today."

    if user.get("activity_level") == "No":
        day2 = "Walk for 10 minutes after one meal."
        day5 = "Repeat the 10-minute walk and notice whether it feels easier."
    else:
        day2 = "Add one extra short walk or stretch break to your usual routine."
        day5 = "Keep your regular activity and add one extra movement break."

    if user.get("vegetables_fruits") == "No":
        day3 = "Add vegetables, fruit, berries, beans, or another fiber-rich food to one meal."
    else:
        day3 = "Keep your daily vegetables/fruits habit and add one fiber-rich option if possible."

    if user.get("sleep_quality") == "Poor":
        day4 = "Set a realistic bedtime target and avoid screens for 20 minutes before sleep."
    else:
        day4 = "Protect your sleep schedule and aim for a consistent bedtime."

    plan.append(("Day 1", day1))
    plan.append(("Day 2", day2))
    plan.append(("Day 3", day3))
    plan.append(("Day 4", day4))
    plan.append(("Day 5", day5))
    plan.append(("Day 6", "Prepare your doctor conversation card and write down any symptoms or concerns."))
    plan.append(("Day 7", "Log one health value if available: weight, waist circumference, blood pressure, fasting glucose, or activity."))

    return plan


def build_passport_text(user, result, guidance, prevention_map, missing_info, doctor_questions, micro_plan):
    """
    Build a downloadable text version of the Prevention Passport.
    """
    lines = []

    lines.append("DIABETES PREVENTION PASSPORT")
    lines.append("=" * 30)
    lines.append("")
    lines.append("Medical disclaimer: This is not a diagnosis and does not replace a doctor.")
    lines.append("")

    lines.append("FINDRISC SCREENING RESULT")
    lines.append(f"FINDRISC score: {get_findrisc_score(result)}")
    lines.append(f"Risk category: {result.get('category', 'Not available')}")
    lines.append("Note: FINDRISC is a questionnaire-based screening tool. This app does not diagnose diabetes.")
    lines.append("")

    lines.append("RECOMMENDED NEXT STEP")
    lines.append(guidance["title"])
    lines.append(guidance["message"])
    lines.append("")

    lines.append("HEALTH INFORMATION USED")
    lines.append(f"Age: {user.get('age')}")
    lines.append(f"Sex: {user.get('sex')}")
    lines.append(f"BMI: {user.get('bmi')}")
    lines.append(f"Waist circumference: {user.get('waist_cm')}")
    lines.append(f"Family history: {user.get('family_history')}")
    lines.append(f"Activity level: {user.get('activity_level')}")
    lines.append(f"Vegetables/fruits daily: {user.get('vegetables_fruits')}")
    lines.append(f"Blood pressure medication: {user.get('blood_pressure_medication')}")
    lines.append(f"History of high blood glucose: {user.get('high_blood_glucose_history')}")
    lines.append(f"Sugary drinks / sweets: {user.get('sugar_drinks')}")
    lines.append(f"Smoking: {user.get('smoking')}")
    lines.append(f"Sleep quality: {user.get('sleep_quality')}")
    lines.append(f"Blood pressure: {user.get('blood_pressure')}")
    lines.append(f"HbA1c: {user.get('hba1c') if user.get('hba1c') is not None else 'Not provided'}")
    lines.append(f"Fasting glucose: {user.get('fasting_glucose') if user.get('fasting_glucose') is not None else 'Not provided'}")
    lines.append("")

    lines.append("PREVENTION MAP")
    for item in prevention_map:
        lines.append(f"- {item['area']}: {item['status']} — {item['meaning']}")
    lines.append("")

    lines.append("SCREENING GAPS")
    for item in missing_info:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("DOCTOR CONVERSATION CARD")
    for question in doctor_questions:
        lines.append(f"- {question}")
    lines.append("")

    lines.append("7-DAY MICRO-PLAN")
    for day, action in micro_plan:
        lines.append(f"- {day}: {action}")

    return "\n".join(lines)


def render_prevention_passport():
    """
    Render the special feature: Diabetes Prevention Passport.
    """
    st.header("Diabetes Prevention Passport")
    st.write(
        "This page turns the FINDRISC assessment into a practical prevention plan. "
        "It does not diagnose. It helps the user become prepared, informed, and ready for the right next step."
    )

    user, result, saved = get_latest_assessment()

    if user is None or result is None:
        st.warning("Complete the Risk Assessment first to generate your Prevention Passport.")
        return

    guidance = get_care_guidance(result)
    prevention_map = build_prevention_map(user, result)
    missing_info = get_missing_screening_info(user)
    doctor_questions = get_doctor_questions(user, result)
    micro_plan = get_micro_plan(user)

    st.subheader("1. FINDRISC Screening Result")
    c1, c2 = st.columns(2)
    c1.metric("FINDRISC score", get_findrisc_score(result))
    c2.metric("Risk category", result.get("category", "Not available"))
    st.caption(
        "FINDRISC is a questionnaire-based screening tool. This prototype does not diagnose diabetes or replace clinical screening."
    )

    st.subheader("2. Care Guidance")
    st.metric("Recommended next step", guidance["title"])
    st.write(guidance["message"])

    st.subheader("3. Prevention Map")
    st.write("These are the main prevention areas found from the information entered.")

    map_df = pd.DataFrame(prevention_map)
    st.dataframe(
        map_df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("4. Screening Gap Detector")
    st.write(
        "These are useful pieces of information that could make a future doctor consultation more complete."
    )

    for item in missing_info:
        st.write(f"- {item}")

    st.subheader("5. Doctor Conversation Card")
    st.write("Suggested questions to bring to a family doctor or endocrinologist:")

    for question in doctor_questions:
        st.write(f"- {question}")

    st.subheader("6. 7-Day Micro-Plan")
    st.write("Small actions that are realistic enough to start before the appointment:")

    for day, action in micro_plan:
        st.write(f"**{day}:** {action}")

    st.download_button(
        label="Download Prevention Passport",
        data=build_passport_text(user, result, guidance, prevention_map, missing_info, doctor_questions, micro_plan),
        file_name="diabetes_prevention_passport.txt",
        mime="text/plain"
    )

    st.info(
        "This passport is not a diagnosis or medical record. "
        "It is a preparation tool to help users have a clearer, more useful healthcare conversation."
    )


# ------------------------------------------------------------
# PAGES
# ------------------------------------------------------------

if page == "Risk Assessment":
    load_risk_inputs()

    st.header("Type 2 Diabetes Risk Assessment")
    st.write(
        "This assessment uses FINDRISC-style questionnaire scoring, then adds optional lab safety information "
        "and lifestyle personalization for the Prevention Passport."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("FINDRISC core information")

        age = number_text_input(
            "Age",
            default_value=st.session_state.get("risk_age_text", ""),
            help_text="Type using your keyboard or numpad. Example: 45",
            key="risk_age_text"
        )
        save_risk_inputs()

        sex = optional_selectbox(
            "Sex",
            ["Female", "Male", "Other / prefer not to say"],
            key="risk_sex"
        )

        height_cm = number_text_input(
            "Height (cm)",
            default_value=st.session_state.get("risk_height_cm_text", ""),
            help_text="Type using your keyboard or numpad. Example: 170",
            key="risk_height_cm_text"
        )
        save_risk_inputs()

        weight_kg = number_text_input(
            "Weight (kg)",
            default_value=st.session_state.get("risk_weight_kg_text", ""),
            help_text="Type using your keyboard or numpad. Example: 75 or 75.5",
            key="risk_weight_kg_text"
        )
        save_risk_inputs()

        if height_cm is not None and weight_kg is not None and height_cm > 0:
            bmi_preview = calculate_bmi(height_cm, weight_kg)
            st.metric("Calculated BMI", bmi_preview)
        else:
            bmi_preview = None
            st.metric("Calculated BMI", "—")

        waist_cm = number_text_input(
            "Waist circumference (cm)",
            default_value=st.session_state.get("risk_waist_cm_text", ""),
            help_text="Measure around the waist, usually near the navel. Example: 85",
            key="risk_waist_cm_text"
        )
        save_risk_inputs()

        family_history = st.multiselect(
            "Which family members have type 2 diabetes?",
            ["Parent", "Sibling", "Grandparent", "Other relative"],
            key="risk_family_history",
            on_change=save_risk_inputs
        )

        activity_level = optional_selectbox(
            "Do you get at least 30 minutes of physical activity daily?",
            ["Yes", "No"],
            key="risk_activity_level",
            help_text="Choose Yes if yes. Choose No if less than 30 minutes per day."
        )

        vegetables_fruits = optional_selectbox(
            "Do you eat vegetables, fruits, or berries every day?",
            ["Yes", "No"],
            key="risk_vegetables_fruits"
        )

        blood_pressure_medication = optional_selectbox(
            "Do you take blood pressure medication?",
            ["Yes", "No"],
            key="risk_blood_pressure_medication"
        )

        high_blood_glucose_history = optional_selectbox(
            "Have you ever had high blood glucose?",
            ["Yes", "No"],
            key="risk_high_blood_glucose_history"
        )

    with col2:
        st.subheader("Extra lifestyle information")
        st.caption("These are not part of the FINDRISC score, but they personalize the Prevention Passport and AI advice.")

        sugar_drinks = optional_selectbox(
            "Sugary drinks / sweets intake",
            ["Never", "Rarely", "Sometimes", "Often"],
            key="risk_sugar_drinks"
        )

        smoking = optional_selectbox(
            "Smoking",
            ["No", "Yes"],
            key="risk_smoking"
        )

        sleep_quality = optional_selectbox(
            "Sleep quality",
            ["Good", "Average", "Poor"],
            key="risk_sleep_quality"
        )

        blood_pressure = optional_selectbox(
            "Current blood pressure status, if known",
            ["Low", "Normal/unknown", "High"],
            key="risk_blood_pressure"
        )

        gestational_diabetes = optional_selectbox(
            "History of gestational diabetes?",
            ["No/not applicable", "Yes"],
            key="risk_gestational_diabetes"
        )

        st.subheader("Optional lab information")
        st.caption("HbA1c and fasting glucose are not part of FINDRISC, but abnormal values trigger doctor-review guidance.")

        has_hba1c = st.checkbox("HbA1c (%) result", key="risk_has_hba1c", on_change=save_risk_inputs)
        if has_hba1c:
            hba1c = number_text_input(
                "HbA1c (%)",
                default_value=st.session_state.get("risk_hba1c_text", ""),
                help_text="Type using your keyboard or numpad. Example: 5.6",
                key="risk_hba1c_text"
            )
            save_risk_inputs()
        else:
            hba1c = None

        has_fasting_glucose = st.checkbox("Fasting glucose (mg/dL) result", key="risk_has_fasting_glucose", on_change=save_risk_inputs)
        if has_fasting_glucose:
            fasting_glucose = number_text_input(
                "Fasting glucose (mg/dL)",
                default_value=st.session_state.get("risk_fasting_glucose_text", ""),
                help_text="Type using your keyboard or numpad. Example: 95",
                key="risk_fasting_glucose_text"
            )
            save_risk_inputs()
        else:
            fasting_glucose = None

    submitted = st.button("Calculate FINDRISC result")

    if submitted:
        save_risk_inputs()

        if age is None:
            st.error("Please enter your age.")
            st.stop()

        if age < 10 or age > 120:
            st.error("Age should be between 10 and 120.")
            st.stop()

        if sex is None:
            st.error("Please select sex.")
            st.stop()

        if height_cm is None or weight_kg is None:
            st.error("Please enter valid height and weight values.")
            st.stop()

        if height_cm < 100 or height_cm > 230:
            st.error("Height should be between 100 and 230 cm.")
            st.stop()

        if weight_kg < 30 or weight_kg > 250:
            st.error("Weight should be between 30 and 250 kg.")
            st.stop()

        if waist_cm is None:
            st.error("Please enter waist circumference.")
            st.stop()

        if waist_cm < 40 or waist_cm > 200:
            st.error("Waist circumference should be between 40 and 200 cm.")
            st.stop()

        if activity_level is None:
            st.error("Please answer the daily physical activity question.")
            st.stop()

        if vegetables_fruits is None:
            st.error("Please answer the vegetables/fruits question.")
            st.stop()

        if blood_pressure_medication is None:
            st.error("Please answer the blood pressure medication question.")
            st.stop()

        if high_blood_glucose_history is None:
            st.error("Please answer the high blood glucose history question.")
            st.stop()

        if sugar_drinks is None:
            st.error("Please select your sugary drinks / sweets intake.")
            st.stop()

        if smoking is None:
            st.error("Please select smoking status.")
            st.stop()

        if sleep_quality is None:
            st.error("Please select sleep quality.")
            st.stop()

        if blood_pressure is None:
            st.error("Please select blood pressure status.")
            st.stop()

        if gestational_diabetes is None:
            st.error("Please answer the gestational diabetes question.")
            st.stop()

        if hba1c is not None and (hba1c < 3.0 or hba1c > 15.0):
            st.error("HbA1c should be between 3.0 and 15.0%.")
            st.stop()

        if fasting_glucose is not None and (fasting_glucose < 50 or fasting_glucose > 400):
            st.error("Fasting glucose should be between 50 and 400 mg/dL.")
            st.stop()

        bmi = calculate_bmi(height_cm, weight_kg)

        user = {
            "age": int(age),
            "sex": sex,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "waist_cm": waist_cm,
            "bmi": bmi,
            "family_history": family_history,
            "activity_level": activity_level,
            "vegetables_fruits": vegetables_fruits,
            "blood_pressure_medication": blood_pressure_medication,
            "high_blood_glucose_history": high_blood_glucose_history,

            # Extra lifestyle information
            "sugar_drinks": sugar_drinks,
            "smoking": smoking,
            "sleep_quality": sleep_quality,
            "blood_pressure": blood_pressure,
            "gestational_diabetes": gestational_diabetes,

            # Optional lab values
            "hba1c": hba1c,
            "fasting_glucose": fasting_glucose,
        }

        result = calculate_diabetes_risk(user)

        st.session_state.last_user = user
        st.session_state.last_result = result
        st.session_state.risk_score_result = {
            "user": user,
            "result": result,
            "bmi": bmi,
            "hba1c": hba1c,
            "fasting_glucose": fasting_glucose,
        }

        st.divider()
        render_findrisc_score_card(result)

        st.subheader("Recommended next step")
        guidance = get_care_guidance(result)
        st.metric("Care guidance", guidance["title"])
        st.write(guidance["message"])

        st.subheader("Health information used")
        st.write(f"BMI: **{bmi}**")
        st.write(f"Waist circumference: **{waist_cm} cm**")

        if hba1c is not None:
            st.write(f"HbA1c: **{hba1c}%**")
        else:
            st.write("HbA1c: not provided")

        if fasting_glucose is not None:
            st.write(f"Fasting glucose: **{fasting_glucose} mg/dL**")
        else:
            st.write("Fasting glucose: not provided")

        if result.get("lifestyle_flags"):
            st.subheader("Lifestyle notes")
            for flag in result["lifestyle_flags"]:
                st.write(f"- {flag}")

        if result["urgent_flags"]:
            st.subheader("Important lab-related warning")
            for flag in result["urgent_flags"]:
                st.error(flag)

        st.subheader("Why this result was shown")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

        st.info(
            "This is not a diagnosis. FINDRISC is a screening tool. "
            "Only a licensed healthcare professional can diagnose diabetes or recommend treatment."
        )

    elif st.session_state.risk_score_result is not None:
        saved = st.session_state.risk_score_result
        result = saved["result"]
        bmi = saved["bmi"]
        hba1c = saved["hba1c"]
        fasting_glucose = saved["fasting_glucose"]
        user = saved["user"]

        st.divider()
        render_findrisc_score_card(result)

        st.subheader("Previous Recommended Next Step")
        guidance = get_care_guidance(result)
        st.metric("Care guidance", guidance["title"])
        st.write(guidance["message"])

        st.subheader("Health information used")
        st.write(f"BMI: **{bmi}**")
        st.write(f"Waist circumference: **{user.get('waist_cm')} cm**")

        if hba1c is not None:
            st.write(f"HbA1c: **{hba1c}%**")
        else:
            st.write("HbA1c: not provided")

        if fasting_glucose is not None:
            st.write(f"Fasting glucose: **{fasting_glucose} mg/dL**")
        else:
            st.write("Fasting glucose: not provided")

        if result.get("lifestyle_flags"):
            st.subheader("Lifestyle notes")
            for flag in result["lifestyle_flags"]:
                st.write(f"- {flag}")

        if result["urgent_flags"]:
            st.subheader("Important lab-related warning")
            for flag in result["urgent_flags"]:
                st.error(flag)

        st.subheader("Why this result was shown")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

        st.info(
            "This is the latest saved FINDRISC result. Click 'Calculate FINDRISC result' again "
            "after changing inputs to update the recommendation."
        )


elif page == "Prevention Passport":
    render_prevention_passport()


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
        - Uses FINDRISC-style questionnaire scoring with a clear medical disclaimer
        - Shows FINDRISC score and risk category
        - Translates the result into action-based care guidance
        - Creates a Diabetes Prevention Passport
        - Detects missing screening information
        - Prepares a doctor conversation card
        - Gives a realistic 7-day prevention micro-plan
        - Helps users track health parameters over time

        **What it does not do:**
        - It does not diagnose diabetes
        - It does not prescribe medication
        - It does not replace a physician
        - It does not tell users to stop or change prescribed treatment

        **Important scoring note:**
        - FINDRISC score uses age, BMI, waist circumference, physical activity,
          vegetables/fruits intake, blood pressure medication, history of high blood glucose,
          and family history.
        - HbA1c and fasting glucose are handled separately as lab safety information.
        - Sugary drinks, smoking, sleep quality, and current blood pressure status personalize
          the Prevention Passport and AI advice, but they are not FINDRISC scoring items.

        **Future expansion:**
        - Secure integration with official health-card medical data
        - Full validation against official FINDRISC scoring and Bosnian clinical data
        - Structured lab report import
        - Verified specialist directory
        - Medication reminders connected to doctor-prescribed therapy
        """
    )
