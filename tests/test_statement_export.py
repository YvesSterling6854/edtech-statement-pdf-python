from datetime import date

from src.statement_export import CourseDelivery, statement_lines


def test_statement_marks_deadlines_and_completed_work():
    records = [
        CourseDelivery("Storyboarding", "Mina", 3, date(2026, 10, 20)),
        CourseDelivery("Storyboarding", "Jo", 3, date(2026, 10, 30)),
        CourseDelivery("Storyboarding", "Lee", 3, date(2026, 10, 20), date(2026, 10, 19)),
    ]

    result = statement_lines(records, date(2026, 10, 25))

    assert [line.status for line in result] == ["overdue", "due", "complete"]
