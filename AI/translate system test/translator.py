from deep_translator import GoogleTranslator


def translate(text: str):

    if not text.strip():
        return ""

    try:
        return GoogleTranslator(
            source="ko",
            target="en"
        ).translate(text)

    except Exception as e:
        return f"ERROR: {e}"
