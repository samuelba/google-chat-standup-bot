QUESTION_RETROSPECT = "What did you do yesterday?"
QUESTION_OUTLOOK = "What will you do today?"
QUESTION_BLOCKING = "What (if anything) is blocking your progress?"
QUESTION_WHERE_WORKING = "Are you in the office today?"


def get_standup_question(name: str, question_type: str):
    if question_type == '0_na':
        return f"*Hi {name}!*\nIt is standup time.\n\n" \
               f"_{QUESTION_RETROSPECT}_"
    if question_type == '1_retrospect':
        return f"_{QUESTION_OUTLOOK}_"
    if question_type == '2_outlook':
        return f"_{QUESTION_BLOCKING}_"
    if question_type == '3_blocking':
        return f"_{QUESTION_WHERE_WORKING}_"
    if question_type == '4_where':
        return f"Something went wrong. Contact your admin."
