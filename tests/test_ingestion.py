"""
Test program for ingestion process

"""

from src.ingestion.ingestion import ingest

chunks = ingest(
    "Capstone_Project_1_Regulatory_Compliance_System_FAQ.pdf",
    "data/regulatory_documents/Capstone_Project_1_Regulatory_Compliance_System_FAQ.pdf",
)


# how to run test process

# uv run python -m tests.test_ingestion
