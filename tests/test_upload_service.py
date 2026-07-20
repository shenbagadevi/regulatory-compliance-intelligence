from pathlib import Path

from src.services.upload_service import upload_service


class MockUploadFile:
    def __init__(self, file_path):
        self.filename = Path(file_path).name
        self.file = open(file_path, "rb")


# pdf_path = "data/RBI_Gold_Loan_Guidelines.pdf"
pdf_path = "sample_files/Capstone_Project_1_Regulatory_Compliance_System_FAQ.pdf"

mock_file = MockUploadFile(pdf_path)

result = upload_service(mock_file)

# print(result)

mock_file.file.close()

# Run this
# uv run python -m tests.test_upload_service
