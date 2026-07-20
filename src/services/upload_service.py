from pathlib import Path
from src.ingestion.ingestion import ingest
from src.core.config import DATA_DIR

# DATA_DIR = Path("data")
DATA_DIR = Path(DATA_DIR)
DATA_DIR.mkdir(exist_ok=True)


def validate_pdf(file):
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are allowed.")

    except Exception as e:
        print(f"services.validate_pdf failed :{e}")
        raise


def save_uploaded_file(file) -> Path:

    try:
        file_path = DATA_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        return file_path

    except Exception as e:
        print(f"services.save_uploaded_file failed :{e}")
        raise


def upload_service(file) -> dict:

    try:
        validate_pdf(file)

        file_path = save_uploaded_file(file)
        ingest(str(file_path))
        return {
            "status": "success",
            "filename": file.filename,
            "message": "PDF uploaded and indexed successfully.",
        }
    except Exception as e:
        print(f"services.upload_service failed :{e}")
        raise
