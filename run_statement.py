from datetime import date

from src.statement_export import CourseDelivery, export_statement, usage_snapshot


records = [
    CourseDelivery("Sound design", "Mina", 4, date(2026, 10, 20)),
    CourseDelivery("Editing lab", "Jo", 6, date(2026, 10, 30), date(2026, 10, 22)),
]
print(export_statement("Avery Chen", records, date(2026, 10, 25)))
print(usage_snapshot())
