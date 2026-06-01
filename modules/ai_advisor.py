"""
Safe AI-style advice generator.

For the hackathon MVP, this uses controlled template logic instead of a live LLM.
You can later replace generate_advice() with an OpenAI API call, but keep the
same safety rules: no diagnosis, no prescriptions, doctor-first guidance.
"""

def generate_advice(user: dict, risk_result: dict) -> str:
    category = risk_result["category"]
    reasons = risk_result["reasons"]
    urgent_flags = risk_result["urgent_flags"]

    lines = []

    lines.append("### First step")
    if category == "High" or urgent_flags:
        lines.append(
            "Your answers show elevated risk indicators. This does not mean you have diabetes, "
            "but it is important to consult a doctor for proper screening and interpretation."
        )
    elif category == "Moderate":
        lines.append(
            "Your answers show some risk indicators. A preventive checkup with a doctor would be a smart next step."
        )
    else:
        lines.append(
            "Your current risk indicators appear lower, but routine prevention and screening are still important."
        )

    if urgent_flags:
        lines.append("\n### Lab-related warning")
        for flag in urgent_flags:
            lines.append(f"- {flag}")

    lines.append("\n### Why the app gave this result")
    for reason in reasons:
        lines.append(f"- {reason}")

    lines.append("\n### Safe lifestyle steps to discuss with a healthcare professional")
    lines.append("- Aim for regular walking or moderate physical activity during the week.")
    lines.append("- Reduce sugary drinks and highly processed foods.")
    lines.append("- Focus on balanced meals with vegetables, fiber-rich foods, and lean protein.")
    lines.append("- Track weight, fasting glucose, HbA1c if available, and blood pressure over time.")
    lines.append("- Prioritize sleep and stress management.")

    lines.append("\n### What this app will not do")
    lines.append("- It will not diagnose diabetes.")
    lines.append("- It will not prescribe or change medication.")
    lines.append("- It will not replace medical consultation.")

    return "\n".join(lines)
