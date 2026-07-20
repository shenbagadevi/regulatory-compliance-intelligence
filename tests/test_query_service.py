from src.services.query_service import query_service

# question = "What are RBI Gold Loan Guidelines?"
# question = "What are the current RBI guidelines for Gold Loan?"
# question = "What is the minimum core capital(Tier 1 ) ratio required under basel |||?"
question = "What are the KYC requirements for high-risk customer as per SEBI?"
# question = "when is the branch manager approval enough vs. regional credit head approval required?"

answer = query_service(question)

print("\nAnswer:\n")
print(answer)


# how to test

# uv run python -m tests.test_query_service
