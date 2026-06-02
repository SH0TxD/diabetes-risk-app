import streamlit as st
import pandas as pd
import plotly.express as px

from lifestyle_chatbot import render_lifestyle_chatbot
from modules.risk_engine import calculate_bmi, calculate_diabetes_risk
from modules.storage import add_health_log, load_health_logs

from modules.database import init_db, get_family_by_insurer, insert_card, get_db_connection

# ------------------------------------------------------------
# LOGIN SYSTEM (Demo version - single user)
# ------------------------------------------------------------

# Demo user credentials
DEMO_USER = {
    "username": "demo_user",
    "password": "demo123",
    "display_name": "Demo Patient"
}

# Demo user health data (pre-filled values)
DEMO_HEALTH_DATA = {
    "risk_age_text": "45",
    "risk_sex": "Female",
    "risk_height_cm_text": "165",
    "risk_weight_kg_text": "72",
    "risk_waist_cm_text": "88",
    "risk_family_history": ["Parent"],
    "risk_activity_level": "No",
    "risk_vegetables_fruits": "Yes",
    "risk_blood_pressure_medication": "Yes",
    "risk_high_blood_glucose_history": "No",
    "risk_sugar_drinks": "Sometimes",
    "risk_smoking": "No",
    "risk_sleep_quality": "Average",
    "risk_blood_pressure": "High",
    "risk_gestational_diabetes": "No/not applicable",
    "risk_has_hba1c": True,
    "risk_hba1c_text": "5.8",
    "risk_has_fasting_glucose": True,
    "risk_fasting_glucose_text": "105",
}


def init_login_state():
    """Initialize login session state"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None


def check_login(username, password):
    """Check credentials against demo user"""
    if username == DEMO_USER["username"] and password == DEMO_USER["password"]:
        st.session_state.logged_in = True
        st.session_state.current_user = DEMO_USER["display_name"]

        # Auto-load demo data into session state on login
        for key, value in DEMO_HEALTH_DATA.items():
            st.session_state[key] = value

        # Also initialize risk_inputs with demo data
        st.session_state.risk_inputs = {
            "age_text": DEMO_HEALTH_DATA["risk_age_text"],
            "sex": DEMO_HEALTH_DATA["risk_sex"],
            "height_cm_text": DEMO_HEALTH_DATA["risk_height_cm_text"],
            "weight_kg_text": DEMO_HEALTH_DATA["risk_weight_kg_text"],
            "waist_cm_text": DEMO_HEALTH_DATA["risk_waist_cm_text"],
            "family_history": DEMO_HEALTH_DATA["risk_family_history"],
            "activity_level": DEMO_HEALTH_DATA["risk_activity_level"],
            "vegetables_fruits": DEMO_HEALTH_DATA["risk_vegetables_fruits"],
            "blood_pressure_medication": DEMO_HEALTH_DATA["risk_blood_pressure_medication"],
            "high_blood_glucose_history": DEMO_HEALTH_DATA["risk_high_blood_glucose_history"],
            "sugar_drinks": DEMO_HEALTH_DATA["risk_sugar_drinks"],
            "smoking": DEMO_HEALTH_DATA["risk_smoking"],
            "sleep_quality": DEMO_HEALTH_DATA["risk_sleep_quality"],
            "blood_pressure": DEMO_HEALTH_DATA["risk_blood_pressure"],
            "gestational_diabetes": DEMO_HEALTH_DATA["risk_gestational_diabetes"],
            "has_hba1c": DEMO_HEALTH_DATA["risk_has_hba1c"],
            "hba1c_text": DEMO_HEALTH_DATA["risk_hba1c_text"],
            "has_fasting_glucose": DEMO_HEALTH_DATA["risk_has_fasting_glucose"],
            "fasting_glucose_text": DEMO_HEALTH_DATA["risk_fasting_glucose_text"],
        }

        return True
    return False


def logout():
    """Logout function"""
    st.session_state.logged_in = False
    st.session_state.current_user = None
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
        "sugar_drinks": None,
        "smoking": None,
        "sleep_quality": None,
        "blood_pressure": None,
        "gestational_diabetes": None,
        "has_hba1c": False,
        "hba1c_text": "",
        "has_fasting_glucose": False,
        "fasting_glucose_text": "",
    }
    st.rerun()


def login_page():
    """Render login page"""
    st.title("🩺 GlucoGuard Bosnia")
    st.subheader("Type 2 Diabetes Risk Awareness Prototype")

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 🔐 Demo Login")
        st.markdown("Use the demo credentials below to try the application:")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        col_left, col_right = st.columns(2)
        with col_left:
            login_btn = st.button("Login", type="primary", use_container_width=True)
        with col_right:
            st.markdown("")

        if login_btn:
            if check_login(username, password):
                st.success(f"✅ Welcome, {DEMO_USER['display_name']}!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Use demo_user / demo123")

        st.markdown("---")
        st.markdown("### 📋 Demo Credentials")
        st.code("Username: demo_user\nPassword: demo123", language="text")

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown(
            """
            This is a **preventive support prototype** for type 2 diabetes risk awareness.

            **What you can do:**
            - Complete risk assessment with pre-filled demo data
            - Get a FINDRISC score and personalized recommendations
            - Generate a Prevention Passport
            - Chat with AI Lifestyle Advisor
            - Track health metrics over time

            *This is a demo version with a single test user.*
            """
        )


def load_demo_data():
    """Load demo health data into session state"""
    for key, value in DEMO_HEALTH_DATA.items():
        st.session_state[key] = value

    # Also update risk_inputs
    def load_demo_data():
        """Load demo health data into session state"""
        # Clear existing risk-related session state first
        for key in list(st.session_state.keys()):
            if key.startswith("risk_"):
                if key in ["risk_family_history"]:
                    st.session_state[key] = []
                elif key in ["risk_has_hba1c", "risk_has_fasting_glucose"]:
                    st.session_state[key] = False
                elif key in ["risk_sex", "risk_activity_level", "risk_vegetables_fruits",
                             "risk_blood_pressure_medication", "risk_high_blood_glucose_history",
                             "risk_sugar_drinks", "risk_smoking", "risk_sleep_quality",
                             "risk_blood_pressure", "risk_gestational_diabetes"]:
                    st.session_state[key] = None
                else:
                    st.session_state[key] = ""

        # Load demo data
        for key, value in DEMO_HEALTH_DATA.items():
            st.session_state[key] = value

        # Also update risk_inputs with demo data
        st.session_state.risk_inputs = {
            "age_text": DEMO_HEALTH_DATA["risk_age_text"],
            "sex": DEMO_HEALTH_DATA["risk_sex"],
            "height_cm_text": DEMO_HEALTH_DATA["risk_height_cm_text"],
            "weight_kg_text": DEMO_HEALTH_DATA["risk_weight_kg_text"],
            "waist_cm_text": DEMO_HEALTH_DATA["risk_waist_cm_text"],
            "family_history": DEMO_HEALTH_DATA["risk_family_history"],
            "activity_level": DEMO_HEALTH_DATA["risk_activity_level"],
            "vegetables_fruits": DEMO_HEALTH_DATA["risk_vegetables_fruits"],
            "blood_pressure_medication": DEMO_HEALTH_DATA["risk_blood_pressure_medication"],
            "high_blood_glucose_history": DEMO_HEALTH_DATA["risk_high_blood_glucose_history"],
            "sugar_drinks": DEMO_HEALTH_DATA["risk_sugar_drinks"],
            "smoking": DEMO_HEALTH_DATA["risk_smoking"],
            "sleep_quality": DEMO_HEALTH_DATA["risk_sleep_quality"],
            "blood_pressure": DEMO_HEALTH_DATA["risk_blood_pressure"],
            "gestational_diabetes": DEMO_HEALTH_DATA["risk_gestational_diabetes"],
            "has_hba1c": DEMO_HEALTH_DATA["risk_has_hba1c"],
            "hba1c_text": DEMO_HEALTH_DATA["risk_hba1c_text"],
            "has_fasting_glucose": DEMO_HEALTH_DATA["risk_has_fasting_glucose"],
            "fasting_glucose_text": DEMO_HEALTH_DATA["risk_fasting_glucose_text"],
        }

        # Clear previous assessment results when loading new demo data
        st.session_state.last_user = None
        st.session_state.last_result = None
        st.session_state.risk_score_result = None

        st.rerun()


# Initialize login state
init_login_state()

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

# Show login page if not logged in
if not st.session_state.logged_in:
    login_page()
    st.stop()

# ------------------------------------------------------------
# MAIN APP (shown only after login)
# ------------------------------------------------------------

st.set_page_config(
    page_title="GlucoGuard Bosnia",
    page_icon="🩺",
    layout="wide"
)

st.title("GlucoGuard Bosnia")
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
        "About & Safety",
        "Family Tree",
        "ZZO KS Card"
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
# PDF AUTOFILL HELPERS
# ------------------------------------------------------------

def _clean_pdf_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _to_float(value):
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _first_number_after_labels(text, labels, max_chars=45):
    for label in labels:
        pattern = rf"{label}\s*[:=\-]?\s*.{{0,{max_chars}}}?(\d{{1,3}}(?:[.,]\d+)?)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _to_float(match.group(1))
    return None


def _parse_date_to_age(date_text):
    if not date_text:
        return None

    date_text = date_text.strip()
    formats = ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]

    for fmt in formats:
        try:
            dob = datetime.strptime(date_text, fmt)
            today = datetime.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except ValueError:
            pass

    return None


def extract_text_from_pdf(uploaded_pdf):
    """
    Extract text from a text-based PDF.
    Scanned image PDFs may need OCR, which is intentionally not used in this prototype.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        st.error("Missing dependency: install pypdf with `python -m pip install pypdf`.")
        return ""

    try:
        uploaded_pdf.seek(0)
        reader = PdfReader(uploaded_pdf)
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        return _clean_pdf_text(text)
    except Exception as e:
        st.error(f"Could not read this PDF: {e}")
        return ""


def parse_pdf_for_risk_data(text):
    """
    Extract any risk-assessment fields found in the PDF text.
    If a field is not found, it is skipped and the user can enter it manually.
    """
    original_text = text or ""
    lower_text = original_text.lower()
    extracted = {}

    # Age or date of birth
    age = _first_number_after_labels(original_text, [r"age", r"patient age", r"starost", r"godine"], max_chars=25)

    if age is None:
        dob_match = re.search(
            r"(?:date of birth|dob|birth date|datum rođenja|datum rodjenja|rođen|rodjen)\s*[:=\-]?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4})",
            original_text,
            flags=re.IGNORECASE
        )
        if dob_match:
            age = _parse_date_to_age(dob_match.group(1))

    if age is not None and 0 < age < 130:
        extracted["risk_age_text"] = str(int(age))

    # Sex / gender
    sex_match = re.search(
        r"(?:sex|gender|spol)\s*[:=\-]?\s*(female|male|f|m|ženski|zenski|muški|muski)",
        original_text,
        flags=re.IGNORECASE
    )
    if sex_match:
        value = sex_match.group(1).strip().lower()
        if value in ["female", "f", "ženski", "zenski"]:
            extracted["risk_sex"] = "Female"
        elif value in ["male", "m", "muški", "muski"]:
            extracted["risk_sex"] = "Male"

    # FINDRISC body measurements
    height = _first_number_after_labels(original_text, [r"height", r"visina"], max_chars=25)
    if height is not None and 80 <= height <= 250:
        extracted["risk_height_cm_text"] = str(int(height) if height.is_integer() else height)

    weight = _first_number_after_labels(original_text, [r"weight", r"težina", r"tezina"], max_chars=25)
    if weight is not None and 20 <= weight <= 300:
        extracted["risk_weight_kg_text"] = str(int(weight) if weight.is_integer() else weight)

    waist = _first_number_after_labels(original_text, [r"waist circumference", r"waist", r"obim struka", r"struk"], max_chars=35)
    if waist is not None and 40 <= waist <= 220:
        extracted["risk_waist_cm_text"] = str(int(waist) if waist.is_integer() else waist)

    # Lab results
    hba1c_match = re.search(
        r"(?:hba1c|a1c|hemoglobin a1c|glycated hemoglobin|glikirani hemoglobin)\s*[:=\-]?\s*(\d{1,2}(?:[.,]\d+)?)\s*%?",
        original_text,
        flags=re.IGNORECASE
    )
    if hba1c_match:
        hba1c = _to_float(hba1c_match.group(1))
        if hba1c is not None and 3 <= hba1c <= 15:
            extracted["risk_has_hba1c"] = True
            extracted["risk_hba1c_text"] = str(hba1c)

    glucose_match = re.search(
        r"(?:fasting glucose|fasting plasma glucose|glucose fasting|fpg|glukoza natašte|glukoza nataste|šećer natašte|secer nataste)\s*[:=\-]?\s*(\d{2,3}(?:[.,]\d+)?)",
        original_text,
        flags=re.IGNORECASE
    )
    if glucose_match:
        fasting_glucose = _to_float(glucose_match.group(1))
        if fasting_glucose is not None and 40 <= fasting_glucose <= 500:
            extracted["risk_has_fasting_glucose"] = True
            extracted["risk_fasting_glucose_text"] = str(fasting_glucose)

    # Family history
    family = []
    if re.search(r"(mother|father|parent|majka|otac|roditelj).{0,40}(diabetes|dijabetes|diabetes mellitus)", lower_text):
        family.append("Parent")
    if re.search(r"(brother|sister|sibling|brat|sestra).{0,40}(diabetes|dijabetes|diabetes mellitus)", lower_text):
        family.append("Sibling")
    if re.search(r"(grandmother|grandfather|grandparent|nana|djed|dedo|baka).{0,40}(diabetes|dijabetes|diabetes mellitus)", lower_text):
        family.append("Grandparent")
    if re.search(r"(family history|porodična anamneza|porodicna anamneza).{0,60}(diabetes|dijabetes|diabetes mellitus)", lower_text):
        if "Other relative" not in family:
            family.append("Other relative")
    if family:
        extracted["risk_family_history"] = family

    # FINDRISC yes/no fields
    if re.search(r"(30 minutes|30 min|physical activity|fizička aktivnost|fizicka aktivnost).{0,50}\b(yes|da)\b", lower_text):
        extracted["risk_activity_level"] = "Yes"
    elif re.search(r"(30 minutes|30 min|physical activity|fizička aktivnost|fizicka aktivnost).{0,50}\b(no|ne)\b", lower_text):
        extracted["risk_activity_level"] = "No"

    if re.search(r"(vegetables|fruit|berries|povrće|povrce|voće|voce).{0,50}\b(daily|every day|yes|da)\b", lower_text):
        extracted["risk_vegetables_fruits"] = "Yes"
    elif re.search(r"(vegetables|fruit|berries|povrće|povrce|voće|voce).{0,50}\b(not daily|no|ne)\b", lower_text):
        extracted["risk_vegetables_fruits"] = "No"

    if re.search(r"(blood pressure medication|antihypertensive|therapy for blood pressure|terapija za pritisak|lijek.*pritisak).{0,50}\b(yes|da)\b", lower_text):
        extracted["risk_blood_pressure_medication"] = "Yes"
    elif re.search(r"(blood pressure medication|antihypertensive|therapy for blood pressure|terapija za pritisak|lijek.*pritisak).{0,50}\b(no|ne)\b", lower_text):
        extracted["risk_blood_pressure_medication"] = "No"

    if re.search(r"(high blood glucose|elevated glucose|previous high glucose|povišena glukoza|povisena glukoza|povišen šećer|povisen secer).{0,50}\b(yes|da)\b", lower_text):
        extracted["risk_high_blood_glucose_history"] = "Yes"
    elif re.search(r"(high blood glucose|elevated glucose|previous high glucose|povišena glukoza|povisena glukoza|povišen šećer|povisen secer).{0,50}\b(no|ne)\b", lower_text):
        extracted["risk_high_blood_glucose_history"] = "No"

    # Extra lifestyle fields
    if re.search(r"(smoking|smoker|pušenje|pusenje)\s*[:=\-]?\s*(yes|da|current)", lower_text):
        extracted["risk_smoking"] = "Yes"
    elif re.search(r"(smoking|smoker|pušenje|pusenje)\s*[:=\-]?\s*(no|ne|non-smoker|nonsmoker)", lower_text):
        extracted["risk_smoking"] = "No"

    if re.search(r"(sleep quality|san|sleep)\s*[:=\-]?\s*(poor|loš|los)", lower_text):
        extracted["risk_sleep_quality"] = "Poor"
    elif re.search(r"(sleep quality|san|sleep)\s*[:=\-]?\s*(average|prosječan|prosjecan)", lower_text):
        extracted["risk_sleep_quality"] = "Average"
    elif re.search(r"(sleep quality|san|sleep)\s*[:=\-]?\s*(good|dobar)", lower_text):
        extracted["risk_sleep_quality"] = "Good"

    if re.search(r"(sugary drinks|sweets|slatkiši|slatkisi|zaslađena pića|zasladjena pica)\s*[:=\-]?\s*(often|frequent|često|cesto)", lower_text):
        extracted["risk_sugar_drinks"] = "Often"
    elif re.search(r"(sugary drinks|sweets|slatkiši|slatkisi|zaslađena pića|zasladjena pica)\s*[:=\-]?\s*(sometimes|ponekad)", lower_text):
        extracted["risk_sugar_drinks"] = "Sometimes"
    elif re.search(r"(sugary drinks|sweets|slatkiši|slatkisi|zaslađena pića|zasladjena pica)\s*[:=\-]?\s*(rarely|rijetko)", lower_text):
        extracted["risk_sugar_drinks"] = "Rarely"
    elif re.search(r"(sugary drinks|sweets|slatkiši|slatkisi|zaslađena pića|zasladjena pica)\s*[:=\-]?\s*(never|nikad)", lower_text):
        extracted["risk_sugar_drinks"] = "Never"

    if re.search(r"(gestational diabetes|gestacijski dijabetes|trudnički dijabetes|trudnicki dijabetes)\s*[:=\-]?\s*(yes|da)", lower_text):
        extracted["risk_gestational_diabetes"] = "Yes"
    elif re.search(r"(gestational diabetes|gestacijski dijabetes|trudnički dijabetes|trudnicki dijabetes)\s*[:=\-]?\s*(no|ne)", lower_text):
        extracted["risk_gestational_diabetes"] = "No/not applicable"

    # Blood pressure status
    bp_match = re.search(r"(?:blood pressure|bp|krvni pritisak|pritisak)\s*[:=\-]?\s*(\d{2,3})\s*/\s*(\d{2,3})", original_text, flags=re.IGNORECASE)
    if bp_match:
        systolic = int(bp_match.group(1))
        diastolic = int(bp_match.group(2))
        if systolic >= 140 or diastolic >= 90:
            extracted["risk_blood_pressure"] = "High"
        elif systolic < 90 or diastolic < 60:
            extracted["risk_blood_pressure"] = "Low"
        else:
            extracted["risk_blood_pressure"] = "Normal/unknown"
    elif re.search(r"(blood pressure|bp|krvni pritisak|pritisak)\s*[:=\-]?\s*(high|povišen|povisen)", lower_text):
        extracted["risk_blood_pressure"] = "High"
    elif re.search(r"(blood pressure|bp|krvni pritisak|pritisak)\s*[:=\-]?\s*(low|nizak)", lower_text):
        extracted["risk_blood_pressure"] = "Low"
    elif re.search(r"(blood pressure|bp|krvni pritisak|pritisak)\s*[:=\-]?\s*(normal|uredan)", lower_text):
        extracted["risk_blood_pressure"] = "Normal/unknown"

    return extracted


def _field_is_empty(session_key):
    value = st.session_state.get(session_key)
    return value is None or value == "" or value == [] or value is False


def apply_pdf_autofill(extracted, overwrite_existing=False):
    """
    Apply extracted PDF values to Streamlit widget session_state.
    If overwrite_existing is False, filled fields are preserved.
    """
    applied = {}

    for key, value in extracted.items():
        if overwrite_existing or _field_is_empty(key):
            if key == "risk_family_history" and not overwrite_existing:
                current = st.session_state.get(key, [])
                merged = list(dict.fromkeys((current or []) + value))
                st.session_state[key] = merged
                applied[key] = merged
            else:
                st.session_state[key] = value
                applied[key] = value

    save_risk_inputs()

    # Clear old assessment because newly imported data may change the result.
    st.session_state.last_result = None
    st.session_state.risk_score_result = None

    return applied


def render_pdf_autofill_box():
    """
    UI box for uploading a PDF and autofilling any detected risk-assessment fields.
    """
    with st.expander("📄 Autofill from patient PDF", expanded=False):
        st.write(
            "Upload a text-based PDF containing patient information or lab results. "
            "The app will fill only the fields it can detect. Anything missing can still be entered manually."
        )

        uploaded_pdf = st.file_uploader("Upload patient PDF", type=["pdf"], key="risk_pdf_upload")

        overwrite_existing = st.checkbox(
            "Overwrite fields that are already filled",
            value=False,
            key="risk_pdf_overwrite"
        )

        if uploaded_pdf is not None and st.button("Extract data from PDF", key="extract_pdf_button"):
            text = extract_text_from_pdf(uploaded_pdf)

            if not text:
                st.warning("No readable text was found. This may be a scanned PDF. Manual entry may be needed.")
                return

            extracted = parse_pdf_for_risk_data(text)
            applied = apply_pdf_autofill(extracted, overwrite_existing=overwrite_existing)

            if applied:
                readable_names = {
                    "risk_age_text": "Age",
                    "risk_sex": "Sex",
                    "risk_height_cm_text": "Height",
                    "risk_weight_kg_text": "Weight",
                    "risk_waist_cm_text": "Waist circumference",
                    "risk_family_history": "Family history",
                    "risk_activity_level": "Daily physical activity",
                    "risk_vegetables_fruits": "Daily vegetables/fruits",
                    "risk_blood_pressure_medication": "Blood pressure medication",
                    "risk_high_blood_glucose_history": "History of high blood glucose",
                    "risk_sugar_drinks": "Sugary drinks / sweets",
                    "risk_smoking": "Smoking",
                    "risk_sleep_quality": "Sleep quality",
                    "risk_blood_pressure": "Blood pressure status",
                    "risk_gestational_diabetes": "Gestational diabetes",
                    "risk_has_hba1c": "HbA1c checkbox",
                    "risk_hba1c_text": "HbA1c",
                    "risk_has_fasting_glucose": "Fasting glucose checkbox",
                    "risk_fasting_glucose_text": "Fasting glucose",
                }

                st.success(f"Autofilled {len(applied)} field(s) from the PDF.")
                with st.container(border=True):
                    st.write("Detected and applied:")
                    for key, value in applied.items():
                        st.write(f"- **{readable_names.get(key, key)}:** {value}")

                st.info("The page will refresh so the detected values appear in the assessment fields.")
                st.rerun()
            else:
                st.warning(
                    "The PDF was readable, but no matching assessment fields were detected "
                    "or all detected fields were already filled."
                )



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

#imad changes begin
from datetime import datetime


def sync_card_to_risk_inputs():
    loaded_card = st.session_state.get("loaded_card")

    if loaded_card:
        card_id = loaded_card.get("card_id")

        if st.session_state.get("last_user") != card_id:
            dob_str = loaded_card.get("dob", "")
            calculated_age = ""
            if dob_str:
                try:
                    dob_date = datetime.strptime(dob_str.split()[0], "%Y-%m-%d")
                    calculated_age = 2026 - dob_date.year
                    if (6, 2) < (dob_date.month, dob_date.day):
                        calculated_age -= 1
                except Exception:
                    pass

            gender_db = str(loaded_card.get("gender", "")).strip().lower()
            mapped_sex = None
            if gender_db in ["male", "m", "muški", "muski"]:
                mapped_sex = "Male"
            elif gender_db in ["female", "f", "ženski", "zenski"]:
                mapped_sex = "Female"
            else:
                mapped_sex = "Other / prefer not to say"

            db_height = loaded_card.get("height") or loaded_card.get("height_cm", "")

            st.session_state.risk_inputs["age_text"] = str(calculated_age) if calculated_age else ""
            st.session_state.risk_inputs["sex"] = mapped_sex
            st.session_state.risk_inputs["height_cm_text"] = str(db_height) if db_height else ""

            st.session_state["risk_age_text"] = st.session_state.risk_inputs["age_text"]
            st.session_state["risk_sex"] = st.session_state.risk_inputs["sex"]
            st.session_state["risk_height_cm_text"] = st.session_state.risk_inputs["height_cm_text"]

            st.session_state.last_user = card_id

# imad changes end


# ------------------------------------------------------------
# PAGES
# ------------------------------------------------------------

#imad change begin
if page == "Risk Assessment":
    # Run card sync checks right before loading inputs into widgets
    sync_card_to_risk_inputs()
    load_risk_inputs()

    render_pdf_autofill_box()

    # Visual confirmation banner that profile data was injected
    if st.session_state.get("loaded_card"):
        card = st.session_state.loaded_card
        st.success(f"⚡ **Profile Connected: Automatically loaded details for  {card['last_name']}**.")

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
#imad change end

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


elif page == "GlucoGuard AI":
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
        **Purpose:** GlucoGuard Bosnia is a preventive support tool for early type 2 diabetes risk awareness.

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

elif page == "Family Tree":
    import os
    import json
    import uuid
    import graphviz

    st.header("Family Tree")
    st.write("Build your tree. Adding 'Parent' will always place that block above the selected relative.")

    # --- DATA PERSISTENCE CONFIGURATION ---
    DATA_FILE = "family_tree.json"


    def load_family_tree():
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        # Default starting state if no file exists
        return {
            "1": {"name": "Me", "relation": "Self", "condition": "None", "connects_to": None, "gen": 2}
        }


    def save_family_tree(data):
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)


    # Initialize data from file instead of hardcoded reset
    if "family_tree" not in st.session_state:
        st.session_state.family_tree = load_family_tree()


    @st.dialog("Family Member Details")
    def family_menu(target_id, is_edit=False):
        data = st.session_state.family_tree.get(target_id, {}) if is_edit else {}
        name = st.text_input("Name", value=data.get("name", ""))
        rel = st.selectbox("Relation", ["Parent", "Sibling", "Child", "Other"],
                           index=["Parent", "Sibling", "Child", "Other"].index(
                               data.get("relation", "Other")) if is_edit else 0)
        cond = st.selectbox("Status", ["None", "Type 1", "Type 2", "Pre-diabetes"],
                            index=["None", "Type 1", "Type 2", "Pre-diabetes"].index(
                                data.get("condition", "None")) if is_edit else 0)

        if st.button("Save"):
            if name:
                target_gen = st.session_state.family_tree[target_id].get("gen", 2)
                gen_map = {"Parent": -1, "Sibling": 0, "Child": 1, "Other": 0}
                new_gen = target_gen + gen_map.get(rel, 0)

                if not is_edit:
                    new_id = str(uuid.uuid4())[:8]
                    st.session_state.family_tree[new_id] = {"name": name, "relation": rel, "condition": cond,
                                                            "connects_to": target_id, "gen": new_gen}
                else:
                    st.session_state.family_tree[target_id].update(
                        {"name": name, "relation": rel, "condition": cond, "gen": new_gen})

                # Save changes locally
                save_family_tree(st.session_state.family_tree)
                st.rerun()


    # Configuration with natural lines ('splines': 'ortho' has been removed)
    tree_graph = graphviz.Digraph(graph_attr={'bgcolor': 'transparent', 'rankdir': 'TB'},
                                  node_attr={'shape': 'box', 'style': 'filled,rounded', 'fontname': 'Helvetica',
                                             'fontcolor': '#ffffff', 'fillcolor': '#2d3748', 'penwidth': '3',
                                             'margin': '0.3,0.15'},
                                  edge_attr={'color': '#718096', 'penwidth': '2', 'dir': 'none'})

    gens = {}
    parents_of = {nid: [] for nid in st.session_state.family_tree}
    couples = []

    for nid, d in st.session_state.family_tree.items():
        g = d.get("gen", 2)
        if g not in gens:
            gens[g] = []
        gens[g].append((nid, d))

        if d["condition"] == "Type 2":
            border_color = "#e53e3e"  # Crimson Red
        elif d["condition"] == "Type 1":
            border_color = "#9f7aea"  # Purple
        elif d["condition"] == "Pre-diabetes":
            border_color = "#ed8936"  # Orange
        else:
            border_color = "#a0aec0"  # Slate Gray

        # Label changed to only display the member's name (Relation parenthesis removed)
        tree_graph.node(nid, label=d['name'], color=border_color)

        tid = d["connects_to"]
        if tid:
            gen_n = d.get("gen", 2)
            gen_t = st.session_state.family_tree[tid].get("gen", 2)

            if gen_n < gen_t:
                parents_of[tid].append(nid)
            elif gen_t < gen_n:
                parents_of[nid].append(tid)
            else:
                couples.append((nid, tid))

    for g in sorted(gens.keys()):
        with tree_graph.subgraph() as s:
            s.attr(rank='same')
            for nid, _ in gens[g]:
                s.node(nid)

    for child_id, parents in parents_of.items():
        for parent_id in parents:
            tree_graph.edge(parent_id, child_id)

    for nid, tid in couples:
        tree_graph.edge(nid, tid)

    # --- UNDERSTANDABLE FAMILY RISK BANNER ---
    has_high_risk_relative = any(
        m["condition"] in ["Type 2", "Pre-diabetes"] and m["relation"] in ["Parent", "Sibling"]
        for m in st.session_state.family_tree.values()
    )
    has_any_relative = any(
        m["condition"] in ["Type 1", "Type 2", "Pre-diabetes"]
        for m in st.session_state.family_tree.values()
    )

    if has_high_risk_relative:
        st.error(
            "🧬 **Family Risk Check:** It looks like you have a **higher genetic risk** of developing diabetes "
            "because it runs in your immediate family (parents or siblings). Don't stress out, though! "
            "This just means it's super smart to keep an eye on your sugar levels, watch your sweets, and stay moving."
        )
    elif has_any_relative:
        st.warning(
            "🧬 **Family Risk Check:** You have a **medium genetic risk** of developing diabetes. "
            "While it shows up somewhere in your family history, remember: genetics load the gun, but lifestyle pulls the trigger. "
            "Your daily choices can completely rewrite the story!"
        )
    else:
        st.success(
            "🧬 **Family Risk Check:** Great news! Genetically, you have a **low risk** of getting diabetes "
            "based on your family tree history. Keep up those healthy everyday habits to keep it that way!"
        )

    st.graphviz_chart(tree_graph)

    st.divider()
    for m_id, data in st.session_state.family_tree.items():
        with st.container(border=True):
            cols = st.columns([3, 1, 1, 1])
            cols[0].markdown(f"**{data['name']}** — *{data['relation']}* (Status: `{data['condition']}`)")
            if cols[1].button("✏️", key=f"e_{m_id}"):
                family_menu(m_id, is_edit=True)
            if cols[2].button("➕", key=f"a_{m_id}"):
                family_menu(m_id)
            if m_id != "1" and cols[3].button("🗑️", key=f"d_{m_id}"):
                del st.session_state.family_tree[m_id]
                # Update local file storage on removal
                save_family_tree(st.session_state.family_tree)
                st.rerun()

elif page == "ZZO KS Card":
    st.header("🩺 ZZO KS Card Lookup")

    if "card_id" not in st.query_params:
        st.query_params["card_id"] = ""

    card_id_input = st.text_input("Enter your Card ID", value=st.query_params["card_id"])

    if st.button("Search Card"):
        st.query_params["card_id"] = card_id_input
        st.rerun()

    if st.button("Clear Search"):
        st.query_params["card_id"] = ""
        st.session_state.family_df = None
        st.session_state.loaded_card = None  # Clear loaded card data
        st.session_state.last_user = None    # Clear user sync tracking
        st.rerun()

    current_id = st.query_params["card_id"]

    if current_id:
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM cards WHERE card_id = ?", (current_id,)).fetchone()
        conn.close()

        if row:
            data = dict(row)
            # 🌟 SAVE CARD DATA GLOBALLY FOR OTHER PAGES 🌟
            st.session_state.loaded_card = data

            with st.container(border=True):
                st.subheader(f"👤 {data['first_name']} {data['last_name']}")

                c1, c2 = st.columns(2)
                c1.metric("JMBG", data['jmbg'])
                c2.metric("Gender", data['gender'])

                c3, c4 = st.columns(2)
                c3.write(f"**Date of Birth:** {data['dob']}")
                c4.write(f"**Deactivation Date:** {data['deactivation_date']}")

                st.info(f"**Insurer Number:** {data['insurer_number']}")

                if st.button("Display Family Members"):
                    st.session_state.family_df = get_family_by_insurer(data['insurer_number'])

            if "family_df" in st.session_state and st.session_state.family_df is not None:
                st.divider()
                if not st.session_state.family_df.empty:
                    st.subheader("👥 Family Members")
                    st.dataframe(
                        st.session_state.family_df,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("No other family members found for this insurer number.")
        else:
            st.error("Card ID not found.")
            st.query_params["card_id"] = ""
            st.session_state.loaded_card = None