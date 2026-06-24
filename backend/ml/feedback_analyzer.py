from textblob import TextBlob

def analyze_feedback(text: str) -> tuple[float, str]:
    blob = TextBlob(text)
    score = round(blob.sentiment.polarity, 4)

    if score > 0.2:
        category = "praise"
    elif score < -0.2:
        category = "concern"
    else:
        category = "improvement"

    return score, category