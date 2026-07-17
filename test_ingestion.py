"""
Test program for ingestion process

"""

from ingestion.ingestion import ingest

chunks = ingest("data/Capstone_Project_1_Regulatory_Compliance_System_FAQ.pdf")


# print()

# print("First Chunk")

# print("-" * 50)

# print(chunks[0].page_content)

# print()

# print(chunks[0].metadata)

"""

metadata info 
{
    "producer": "Skia/PDF m148 Google Docs Renderer",
    "creator": "PyPDF",
    "creationdate": "",
    "title": "Regulatory Compliance Intelligence System - FAQ",
    "source": "data/Capstone_Project_1_Regulatory_Compliance_System_FAQ.pdf",
    "total_pages": 12,
    "page": 0,
    "page_label": "1",
    "document_name": "Capstone_Project_1_Regulatory_Compliance_System_FAQ.pdf",
    "chunk_id": 1,
    "section_number": "Unknown",
    "regulation_type": "General",
}
"""

# how to run test process 

# uv run python test_ingestion.py
