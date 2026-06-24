def predict_student(student: dict) -> dict:
    percentage = float(student.get("percentage") or 0)

    if percentage >= 85:
        predicted = round(min(percentage + 2, 100), 2)
        recommendation = "Excellent performance! Maintain consistency."
    elif percentage >= 60:
        predicted = round(percentage + 5, 2)
        recommendation = "Good performance. Focus on weak subjects to improve further."
    elif percentage >= 40:
        predicted = round(percentage + 8, 2)
        recommendation = "Needs improvement. Regular practice and revision recommended."
    else:
        predicted = round(percentage + 10, 2)
        recommendation = "Critical: Immediate attention and extra coaching required."

    return {
        "predicted_percentage": predicted,
        "recommendation": recommendation
    }