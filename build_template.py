from __future__ import annotations

from pathlib import Path


def build_template(output_path: str = "handles_template.xlsx") -> None:
    import openpyxl
    from openpyxl.worksheet.datavalidation import DataValidation

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Handles"

    headers = [
        "handle",
        "platform",
        "url",
        "source_name",
        "linked_domain",
        "manual_identity_clear",
        "manual_verified",
        "manual_impersonation_flag",
        "manual_parody_labeled",
        "manual_account_age_bucket",
        "manual_bio_text",
    ]

    for i, header in enumerate(headers, start=1):
        sheet.cell(row=1, column=i, value=header)

    def add_dropdown(column: str, values: list[str]) -> None:
        validation = DataValidation(type="list", formula1=f'"{",".join(values)}"', allow_blank=True)
        sheet.add_data_validation(validation)
        validation.add(f"{column}2:{column}1000")

    add_dropdown("B", ["x", "instagram", "facebook", "youtube", "news_website", "other"])
    add_dropdown("F", ["yes", "no", "unknown"])
    add_dropdown("G", ["yes", "no", "unknown"])
    add_dropdown("H", ["yes", "no", "unknown"])
    add_dropdown("I", ["yes", "no", "unknown", "not_applicable"])
    add_dropdown("J", ["under_3_months", "3mo_2yr", "2yr_plus", "unknown"])

    workbook.save(Path(output_path))


if __name__ == "__main__":
    build_template()
