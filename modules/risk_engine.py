"""
Explainable type 2 diabetes risk engine.

This is intentionally rule-based for the hackathon prototype.
It does NOT diagnose diabetes. It estimates risk indicators based on
common risk factors and optional lab values.
"""

def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    if height_cm <= 0:
        return 0.0
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def calculate_diabetes_risk(user: dict) -> dict:
    score = 0
    reasons = []
    urgent_flags = []

    age = user.get("age", 0)
    bmi = user.get("bmi", 0)
    family_history = user.get("family_history", [])
    activity_level = user.get("activity_level", "Moderate")
    sugar_drinks = user.get("sugar_drinks", "Rarely")
    smoking = user.get("smoking", "No")
    sleep_quality = user.get("sleep_quality", "Good")
    blood_pressure = user.get("blood_pressure", "Normal/unknown")
    gestational_diabetes = user.get("gestational_diabetes", "No/not applicable")
    hba1c = user.get("hba1c")
    fasting_glucose = user.get("fasting_glucose")

    # Age
    if age >= 45:
        score += 2
        reasons.append("Age 45 or above is associated with higher type 2 diabetes risk.")
    elif age >= 35:
        score += 1
        reasons.append("Age above 35 can slightly increase risk, especially with other factors.")

    # BMI
    if bmi >= 30:
        score += 3
        reasons.append("BMI is in the obesity range, which is a major risk factor.")
    elif bmi >= 25:
        score += 2
        reasons.append("BMI is in the overweight range, which increases risk.")

    # Family history
    close_relatives = {"Parent", "Sibling"}
    if any(member in close_relatives for member in family_history):
        score += 3
        reasons.append("A parent or sibling with type 2 diabetes increases personal risk.")
    elif "Grandparent" in family_history:
        score += 1
        reasons.append("Family history in grandparents may indicate increased risk.")

    # Lifestyle
    if activity_level == "Low":
        score += 2
        reasons.append("Low physical activity can increase insulin resistance.")
    elif activity_level == "Moderate":
        score += 1
        reasons.append("Moderate activity is helpful, but more consistent activity may reduce risk.")

    if sugar_drinks == "Often":
        score += 2
        reasons.append("Frequent sugary drinks or sweets can contribute to weight gain and glucose problems.")
    elif sugar_drinks == "Sometimes":
        score += 1
        reasons.append("Occasional high sugar intake may contribute to risk when combined with other factors.")

    if smoking == "Yes":
        score += 1
        reasons.append("Smoking is associated with worse cardiometabolic health.")

    if sleep_quality == "Poor":
        score += 1
        reasons.append("Poor sleep can negatively affect metabolism and appetite regulation.")

    if blood_pressure == "High":
        score += 1
        reasons.append("High blood pressure often appears together with metabolic risk factors.")

    if gestational_diabetes == "Yes":
        score += 3
        reasons.append("Previous gestational diabetes significantly increases future type 2 diabetes risk.")

    # Optional lab values
    if hba1c is not None:
        if hba1c >= 6.5:
            score += 5
            urgent_flags.append("HbA1c is in a range commonly used to diagnose diabetes. This requires medical confirmation.")
        elif hba1c >= 5.7:
            score += 3
            reasons.append("HbA1c is above the normal range and should be discussed with a doctor.")

    if fasting_glucose is not None:
        if fasting_glucose >= 126:
            score += 5
            urgent_flags.append("Fasting glucose is in a range commonly used to diagnose diabetes. This requires medical confirmation.")
        elif fasting_glucose >= 100:
            score += 3
            reasons.append("Fasting glucose is above the normal range and should be discussed with a doctor.")

    if score <= 3:
        category = "Low"
        color = "green"
        next_step = "Maintain healthy habits and consider routine screening based on your doctor's advice."
    elif score <= 8:
        category = "Moderate"
        color = "orange"
        next_step = "Consider booking a preventive checkup and asking about fasting glucose or HbA1c screening."
    else:
        category = "High"
        color = "red"
        next_step = "Please consult a family doctor or endocrinologist for proper evaluation and screening."

    if not reasons and not urgent_flags:
        reasons.append("No major risk indicators were selected in this prototype assessment.")

    return {
        "score": score,
        "category": category,
        "color": color,
        "reasons": reasons,
        "urgent_flags": urgent_flags,
        "next_step": next_step,
    }
