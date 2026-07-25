"""
Handles simple conversational queries without invoking the LLM.
"""

GREETINGS = {
    "hi",
    "hello",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
}

THANKS = {
    "thanks",
    "thank you",
    "thankyou",
}

BYE = {
    "bye",
    "goodbye",
    "see you",
}


def route_query(query: str):
    q = query.strip().lower()

    if q in GREETINGS:
        return (
            True,
            "Hello! 👋\n\n"
            "I can answer questions from the uploaded regulatory documents.\n"
            "Please ask a compliance-related question.",
        )

    if q in THANKS:
        return (True, "You're welcome! 😊")

    if q in BYE:
        return (True, "Goodbye! Have a great day.")

    return False, None
