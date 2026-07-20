# regulatory_compliance_intelligence
RAG-based AI system for banking regulatory compliance that retrieves relevant clauses from RBI, SEBI, and Basel III documents and generates accurate, cited answers for compliance officers.


# Required packages 
langchain
langchain-openai
langchain-postgres
psycopg
python-dotenv
# sqlalchemy -- not needed it seems. will check 


# packages required for ingestion 

langchain_community
langchain_text_splitters
pypdf


# How to test ingestion part alone 
 uv run python test_ingestion.py



