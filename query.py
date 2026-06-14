import os
from groq import Groq
from dotenv import load_dotenv
from embed_and_store import query as retrieve

load_dotenv()

_client = Groq(api_key=os.environ["GROQ_API_KEY"])

_SYSTEM_PROMPT = """\
You are an assistant that answers questions about off-campus housing near Florida International University (FIU).

STRICT GROUNDING RULE: Answer ONLY using the information found in the documents provided below. Do not use any knowledge from your training data. If the provided documents do not contain enough information to answer the question, respond with exactly: "I don't have enough information on that in the provided documents."

Do not speculate, infer, or fill in gaps with general knowledge. Every factual claim in your answer must be directly traceable to the provided documents.
"""

_USER_TEMPLATE = """\
Documents:
{context}

Question: {question}

Answer based strictly on the documents above. If you use information from a document, it will be attributed using the source list — focus on answering accurately from the text given."""


def ask(question: str, k: int = 5) -> dict:
    """Retrieve top-k chunks, generate a grounded answer, and return sources.

    Returns:
        {"answer": str, "sources": list[str]}
    """
    chunks = retrieve(question, k=k)

    # Build numbered context block; sources tracked programmatically (not left to LLM)
    context_parts = []
    unique_sources: list[str] = []
    seen: set[str] = set()
    for i, (text, source) in enumerate(chunks, 1):
        context_parts.append(f"[{i}] (source: {source})\n{text}")
        if source not in seen:
            unique_sources.append(source)
            seen.add(source)

    context = "\n\n---\n\n".join(context_parts)
    user_msg = _USER_TEMPLATE.format(context=context, question=question)

    response = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
        max_tokens=512,
    )

    answer = response.choices[0].message.content.strip()
    return {"answer": answer, "sources": unique_sources}


if __name__ == "__main__":
    test_questions = [
        "What specific problems do students report about The One at University City?",
        "What is the monthly rent range at Advenir at University Park, and what do reviewers say about management?",
        "According to the Fall 2025 off-campus guide, what hidden fees does Terrazul charge on top of listed rent?",
        "What maintenance issues did students report at University Apartments (UA)?",
        "What advice do students give to international students looking for affordable housing near FIU for spring intake?",
    ]

    for i, q in enumerate(test_questions, 1):
        print(f"\n{'='*70}")
        print(f"Q{i}: {q}")
        print("-" * 70)
        result = ask(q)
        print(f"Answer:\n{result['answer']}")
        print(f"\nSources:")
        for s in result["sources"]:
            print(f"  * {s}")
