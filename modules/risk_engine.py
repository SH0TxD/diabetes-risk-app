"""
FINDRISC-based type 2 diabetes risk engine.

FINDRISC = Finnish Diabetes Risk Score.

This is a questionnaire-based screening tool used to estimate 10-year risk
of developing type 2 diabetes.

Important:
- This does NOT diagnose diabetes.
- This is a prototype implementation for a hackathon.
- A healthcare professional must confirm diabetes/prediabetes with proper testing.
- Optional HbA1c and fasting glucose are used as a safety layer, not as part
  of the FINDRISC questionnaire score.
"""


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    if height_cm <= 0:
        return 0.0

    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def get_bmi_points(bmi: float) -> tuple[int, str | None]:
    """
    FINDRISC BMI scoring:
    < 25 = 0 points
    25–30 = 1 point
    > 30 = 3 points
    """

    if bmi > 30:
        return 3, "BMI is above 30, which adds 3 points in FINDRISC."
    elif bmi >= 25:
        return 1, "BMI is between 25 and 30, which adds 1 point in FINDRISC."

    return 0, None


def get_waist_points(sex: str, waist_cm: float | None) -> tuple[int, str | None]:
    """
    FINDRISC waist circumference scoring:

    Men:
    < 94 cm = 0
    94–102 cm = 3
    > 102 cm = 4

    Women:
    < 80 cm = 0
    80–88 cm = 3
    > 88 cm = 4

    For 'Other / prefer not to say', we do not score waist circumference
    because FINDRISC thresholds are sex-specific.
    """

    if waist_cm is None:
        return 0, "Waist circumference was not provided, so this FINDRISC item was not scored."

    if sex == "Male":
        if waist_cm > 102:
            return 4, "Waist circumference is above 102 cm for men, which adds 4 points in FINDRISC."
        elif waist_cm >= 94:
            return 3, "Waist circumference is between 94 and 102 cm for men, which adds 3 points in FINDRISC."

    elif sex == "Female":
        if waist_cm > 88:
            return 4, "Waist circumference is above 88 cm for women, which adds 4 points in FINDRISC."
        elif waist_cm >= 80:
            return 3, "Waist circumference is between 80 and 88 cm for women, which adds 3 points in FINDRISC."

    else:
        return 0, "Waist circumference was not scored because FINDRISC uses sex-specific thresholds."

    return 0, None


def get_findrisc_category(score: int) -> tuple[str, str, str]:
    """
    Common FINDRISC category interpretation:
    < 7 = Low
    7–11 = Slightly elevated
    12–14 = Moderate
    15–20 = High
    > 20 = Very high
    """

    if score < 7:
        return (
            "Low",
            "green",
            "Continue healthy prevention habits and routine checkups."
        )

    if score <= 11:
        return (
            "Slightly elevated",
            "yellow",
            "Some prevention focus areas are present. Lifestyle improvements may help reduce future risk."
        )

    if score <= 14:
        return (
            "Moderate",
            "orange",
            "Consider preventive screening and discuss risk factors with a healthcare professional."
        )

    if score <= 20:
        return (
            "High",
            "red",
            "Book a preventive consultation and ask whether blood glucose testing is appropriate."
        )

    return (
        "Very high",
        "red",
        "Book a doctor consultation for proper screening and professional evaluation."
    )


def calculate_diabetes_risk(user: dict) -> dict:
    findrisc_score = 0
    reasons = []
    urgent_flags = []

    age = user.get("age", 0)
    sex = user.get("sex")
    bmi = user.get("bmi", 0)
    waist_cm = user.get("waist_cm")

    family_history = user.get("family_history", [])
    activity_level = user.get("activity_level")
    vegetables_fruits = user.get("vegetables_fruits")
    blood_pressure_medication = user.get("blood_pressure_medication")
    high_blood_glucose_history = user.get("high_blood_glucose_history")

    # Existing app fields kept for lifestyle/passport use
    sugar_drinks = user.get("sugar_drinks")
    smoking = user.get("smoking")
    sleep_quality = user.get("sleep_quality")

    # Optional lab values: safety layer only, not FINDRISC score
    hba1c = user.get("hba1c")
    fasting_glucose = user.get("fasting_glucose")

    lifestyle_flags = []

    # ------------------------------------------------------------
    # FINDRISC SCORE
    # ------------------------------------------------------------

    # 1. Age
    # <45 = 0, 45–54 = 2, 55–64 = 3, >64 = 4
    if age > 64:
        findrisc_score += 4
        reasons.append("Age above 64 adds 4 points in FINDRISC.")
    elif age >= 55:
        findrisc_score += 3
        reasons.append("Age between 55 and 64 adds 3 points in FINDRISC.")
    elif age >= 45:
        findrisc_score += 2
        reasons.append("Age between 45 and 54 adds 2 points in FINDRISC.")

    # 2. BMI
    bmi_points, bmi_reason = get_bmi_points(bmi)
    findrisc_score += bmi_points
    if bmi_reason:
        reasons.append(bmi_reason)

    # 3. Waist circumference
    waist_points, waist_reason = get_waist_points(sex, waist_cm)
    findrisc_score += waist_points
    if waist_reason:
        reasons.append(waist_reason)

    # 4. Daily physical activity
    # FINDRISC: less than 30 min/day = 2 points
    if activity_level == "No":
        findrisc_score += 2
        reasons.append("Less than 30 minutes of daily physical activity adds 2 points in FINDRISC.")

    # 5. Daily vegetables/fruits/berries
    # FINDRISC: not daily = 1 point
    if vegetables_fruits == "No":
        findrisc_score += 1
        reasons.append("Not eating vegetables, fruits, or berries daily adds 1 point in FINDRISC.")

    # 6. Blood pressure medication
    # FINDRISC: yes = 2 points
    if blood_pressure_medication == "Yes":
        findrisc_score += 2
        reasons.append("Use of blood pressure medication adds 2 points in FINDRISC.")

    # 7. History of high blood glucose
    # FINDRISC: yes = 5 points
    if high_blood_glucose_history == "Yes":
        findrisc_score += 5
        reasons.append("Previous high blood glucose adds 5 points in FINDRISC.")

    # 8. Family history
    # No = 0
    # Second-degree relative = 3
    # First-degree relative = 5
    close_relatives = {"Parent", "Sibling"}

    if any(member in close_relatives for member in family_history):
        findrisc_score += 5
        reasons.append("Diabetes in a parent or sibling adds 5 points in FINDRISC.")
    elif "Grandparent" in family_history or "Other relative" in family_history:
        findrisc_score += 3
        reasons.append("Diabetes in a grandparent or other relative adds 3 points in FINDRISC.")

    # ------------------------------------------------------------
    # EXTRA LIFESTYLE NOTES
    # These are not FINDRISC scoring items.
    # They personalize the Prevention Passport and AI advice.
    # ------------------------------------------------------------

    if sugar_drinks == "Often":
        lifestyle_flags.append(
            "Frequent sugary drinks or sweets may be a useful nutrition habit to target first."
        )
    elif sugar_drinks == "Sometimes":
        lifestyle_flags.append(
            "Reducing sugary drinks or sweets may support diabetes prevention."
        )

    if smoking == "Yes":
        lifestyle_flags.append(
            "Smoking is relevant to overall cardiometabolic health and should be discussed with a healthcare professional."
        )

    if sleep_quality == "Poor":
        lifestyle_flags.append(
            "Poor sleep can affect energy, appetite, and metabolic health."
        )

    # ------------------------------------------------------------
    # OPTIONAL LAB SAFETY LAYER
    # HbA1c and fasting glucose are NOT part of FINDRISC.
    # They can still trigger doctor-review guidance.
    # ------------------------------------------------------------

    if hba1c is not None:
        if hba1c >= 6.5:
            urgent_flags.append(
                "HbA1c is 6.5% or higher, which is commonly used as a diabetes-range result. "
                "This requires medical confirmation."
            )
        elif hba1c >= 5.7:
            urgent_flags.append(
                "HbA1c is between 5.7% and 6.4%, commonly considered a prediabetes-range result. "
                "This should be discussed with a doctor."
            )
        else:
            reasons.append("HbA1c was provided and is below 5.7%.")

    if fasting_glucose is not None:
        if fasting_glucose >= 126:
            urgent_flags.append(
                "Fasting glucose is 126 mg/dL or higher, which is commonly used as a diabetes-range result. "
                "This requires medical confirmation."
            )
        elif fasting_glucose >= 100:
            urgent_flags.append(
                "Fasting glucose is between 100 and 125 mg/dL, commonly considered a prediabetes-range result. "
                "This should be discussed with a doctor."
            )
        else:
            reasons.append("Fasting glucose was provided and is below 100 mg/dL.")

    category, color, next_step = get_findrisc_category(findrisc_score)

    if urgent_flags and category in ["Low", "Slightly elevated", "Moderate"]:
        category = "Needs lab review"
        color = "red"
        next_step = "Book a doctor consultation to review the entered lab values."

    if not reasons and not urgent_flags:
        reasons.append("No major FINDRISC risk indicators were selected in this prototype assessment.")

    return {
        # Keep score for compatibility with your existing app.
        "score": findrisc_score,
        "findrisc_score": findrisc_score,
        "category": category,
        "color": color,
        "reasons": reasons,
        "lifestyle_flags": lifestyle_flags,
        "urgent_flags": urgent_flags,
        "next_step": next_step,
    }