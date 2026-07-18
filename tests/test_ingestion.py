"""
Test program for ingestion process

"""

from ingestion.ingestion import ingest

chunks = ingest("data/Capstone_Project_1_Regulatory_Compliance_System_FAQ.pdf")


# how to run test process

# uv run python -m tests.test_ingestion
