# The Unofficial Guide — Project 1

---

## Domain

This system covers off-campus housing experiences near Florida International University (FIU) in Miami. The knowledge is valuable because prospective students searching for housing near FIU can only find sanitized marketing copy on official apartment websites and generic listing aggregators like Apartments.com. The real signal — mold in air vents, cars towed at midnight by trucks already waiting, management ignoring maintenance tickets for weeks — lives in Reddit threads and resident review platforms that are scattered, hard to search, and that disappear when threads get buried. This RAG system aggregates that ground-truth peer experience into a single queryable interface that answers questions official channels cannot.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | r/FIU — Off-Campus Housing Guide Fall 2025 | Reddit thread (PDF) | documents/OFF-Campus Housing Guide for Fall 2025 _ r_FIU.pdf |
| 2 | r/FIU — University Apartments thread | Reddit thread (PDF) | documents/University Apartments _ r_FIU.pdf |
| 3 | r/FIU — Housing and social concerns | Reddit thread (PDF) | documents/housing and social concerns _ r_FIU.pdf |
| 4 | r/FIU — Don't rent at the One | Reddit thread (PDF) | documents/Don't rent at the One _ r_FIU.pdf |
| 5 | r/FIU — Apartments near FIU for alumni | Reddit thread (PDF) | documents/Are there any apartments near FIU where alumni's can live at_ _ r_FIU.pdf |
| 6 | r/FIU — Looking for housing | Reddit thread (PDF) | documents/Looking for housing _ r_FIU.pdf |
| 7 | ApartmentRatings — Advenir at University Park | Resident reviews (PDF) | documents/Advenir at University Park Reviews - Miami, FL _ 10495 SW 14th Terrace _ 305 Apartment Reviews.pdf |
| 8 | Apartments.com — FIU off-campus listings | Listing aggregator (PDF) | documents/Apartments For Rent Near Florida International University Modesto Maidique Campus - Miami, FL.pdf |
| 9 | College Pads — FIU off-campus housing | Listing aggregator (PDF) | documents/FIU Off-Campus Housing _ College Pads.pdf |
| 10 | r/FIU — FIU Housing | Reddit thread (PDF) | documents/FIU Housing _ r_FIU.pdf |

---

## Chunking Strategy

**Chunk size:** 800 characters (~200 tokens)

**Overlap:** 150 characters (~38 tokens)

**Why these choices fit your documents:** The corpus is mostly Reddit threads and resident review snippets — individual comments range from one sentence to two short paragraphs. An 800-character chunk fits one to three comments, which preserves a complete opinion without merging unrelated voices into one chunk. The two sparse listing pages (Apartments.com, College Pads) extracted only 700–1,400 characters total after cleaning, so smaller chunks ensure even those thin sources contribute at least one retrievable unit. The 150-character overlap (~2 sentences) prevents a single reviewer's key claim from being split across a boundary — for example, "management ignores issues" and the supporting example ending up in different, disconnected chunks.

Before chunking, each document goes through a `clean_text()` step that strips PDF boilerplate: navigation bars, Reddit upvote/comment counts, sidebar noise, bare URLs, page-header timestamps, promoted-post ad copy, and private-use-area Unicode artifacts left by the PDF renderer. This ensures chunks contain only substantive review content, not UI chrome.

**Final chunk count:** 93 chunks across 10 documents (Advenir: 33, Off-Campus Guide: 17, housing and social concerns: 11, University Apartments: 9, FIU Housing: 7, Don't rent at the One: 6, Looking for housing: 4, Are there any apartments for alumni: 3, Apartments.com: 2, College Pads: 1)

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (local, no API cost)

**Production tradeoff reflection:** `all-MiniLM-L6-v2` is fast, free, and runs entirely locally, which made it the right choice for a development project. But it has a 256-token context window — chunks near that limit get silently truncated before embedding, which can lose the tail of a longer review and degrade retrieval accuracy on detail-heavy chunks. For production I would weigh `text-embedding-3-small` from OpenAI (8,192-token window, stronger semantic accuracy on domain-specific text) against its per-call cost.

---

## Grounded Generation

**System prompt grounding instruction:** The system prompt instructs the model with a grounding rule: "Answer ONLY using the information found in the documents provided below. Do not use any knowledge from your training data. If the provided documents do not contain enough information to answer the question, respond with exactly: 'I don't have enough information on that in the provided documents.'" The temperature is set to 0.0 to minimize creative deviation. The user message prefixes each retrieved chunk with a numbered label and its source filename — `[1] (source: filename.pdf)\n<chunk text>` — so the model can cite by number. The instruction tells the model that every factual claim must be directly traceable to the provided documents, not inferred or gap-filled.

**How source attribution is surfaced in the response:** Source attribution is handled programmatically, not left to the language model. After retrieval, `query.py` tracks the unique filenames from the top-5 chunks in a deduplicated list. These filenames are displayed in a separate "Retrieved from" panel in the Gradio UI, independent of whatever the model writes. This means even if the model fails to cite a source inline, the user can see exactly which documents were consulted. The model is given numbered chunk labels and encouraged to reference them in-text, but the source list in the UI is always authoritative.

---

## Evaluation Report

All five questions were run through the live system (Groq llama-3.3-70b-versatile, top-k=5, temperature=0.0). Responses below are summarized from the full output.

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What specific problems do students report about The One at University City? | Management ignores issues; mail/packages stolen; cars towed at curfew; dirty hallways | Got management ignoring issues and mail/package theft. Missed car towing and dirty hallways entirely. The relevant source ranked 4th out of 5 retrieved chunks, behind Advenir and University Apartments sources. | Partially relevant | Partially accurate |
| 2 | What is the monthly rent range at Advenir at University Park, and what do reviewers say about management? | $1,584–$2,484/mo; 4.3/5 from 305 reviews; management characterized from reviews | Reported $1,299–$2,019 (incorrect upper bound). Did not mention 4.3/5 overall rating. Described management as "very friendly" and responsive. Retrieved "Don't rent at the One" as an off-topic source due to shared "management" vocabulary. | Partially relevant | Partially accurate |
| 3 | According to the Fall 2025 off-campus guide, what hidden fees does Terrazul charge on top of listed rent? | $200+ in extra fees: parking, premium floor (~$30/mo), amenity premiums, liability fees, utility fees | Correctly listed all five fee categories including the $30/month premium floor surcharge. Retrieved the correct source (Off-Campus Housing Guide) and FIU Housing thread. | Relevant | Accurate |
| 4 | What maintenance issues did students report at University Apartments (UA)? | Mold in air vents, mold/stains in bathroom, bug/termite infestation in kitchen, broken drawers, slow WiFi | Reported slow WiFi, stained mattress, broken drawers, and parking issues. Missed mold and bug/termite infestation — the two most serious reported problems. Retrieved FIU Housing thread as an off-target second source. | Partially relevant | Partially accurate |
| 5 | What advice do students give to international students looking for affordable housing near FIU for spring intake? | Intended failure: limited direct advice; expected partial/vague answer without hallucination | Correctly stated no direct advice exists in the documents. Mentioned one speculative comment about international students possibly having housing priority. Did not hallucinate specific prices or complexes. Retrieved FIU Housing and Off-Campus Guide rather than the more relevant "Looking for housing" thread. | Off-target | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** Q2 — "What is the monthly rent range at Advenir at University Park, and what do reviewers say about management?"

**What the system returned:** The system reported the rent range as "$1,299–$2,019" and mentioned $1,584 as a single apartment's price — both wrong. The expected range is $1,584–$2,484. The overall 4.3/5 rating from 305 reviews was never mentioned. The source list also included "Don't rent at the One _ r_FIU.pdf," a document about a completely different apartment complex.

**Root cause (tied to a specific pipeline stage):** Two pipeline failures combined to produce this result.

Chunking by fixed character count fragmented the Advenir price summary from the individual price mentions. The Advenir document has 33 chunks. The aggregate price range summary ("$1,584–$2,484/month") likely appeared on the overview page alongside the overall rating, but that particular chunk was not retrieved in the top-5. Instead, chunks containing individual unit-level prices (a 1-bed at $1,299, a 2-bed at $2,019) were retrieved. When the model synthesized these individual prices into a "range," it constructed a range that was factually incorrect. The chunk boundary split the high-level summary from the granular pricing details.

The embedding model's representation of "management" pulled a chunk from an unrelated source**. The word "management" is a semantically strong term in `all-MiniLM-L6-v2`'s embedding space. The "Don't rent at the One" thread is dense with management-complaint vocabulary. When the query asked about management at Advenir, one of the top-5 slots was taken by a high-similarity chunk from the wrong apartment's management thread. This consumed a retrieval slot that could have held the Advenir price-range summary chunk.

**What you would change to fix it:** To fix the chunking issue, I would use a metadata-aware chunking strategy: for a review platform like ApartmentRatings, extract the structured header fields (price range, overall rating, review count) as a dedicated chunk with high-priority metadata, rather than letting them fall wherever they land in a fixed-size split. To fix the off-target retrieval, I would add a re-ranking step — after retrieving top-20 by embedding similarity, a cross-encoder re-ranker that scores each chunk against the full query would demote chunks that share vocabulary but discuss different subjects. Alternatively, filtering retrieved chunks to only those whose source document name contains "Advenir" when the query explicitly names that complex would prevent cross-complex contamination.

---

## Spec Reflection

**One way the spec helped during implementation:** The Chunking Strategy section in planning.md specified the 800-character chunk size and 150-character overlap before any code was written. This gave a concrete target to test against: after running `ingest.py`, the first verification step was to print chunk lengths and confirm they fell within ±50 characters of 800. Because the spec included the reasoning (preserving a complete reviewer comment, preventing key claims from splitting across boundaries), it also made it obvious *why* the overlap needed to be character-based rather than token-based — the PDF extractor returns raw strings, not pre-tokenized text. Having both the number and the reasoning in the spec prevented second-guessing during implementation.

**One way the implementation diverged from the spec, and why:** The spec described a single `embed_and_store.py` with a `query()` function that returns `[(chunk, source), ...]`. In the actual implementation, `ingest.py` was separated out as its own module with `load_documents()`, `clean_text()`, and `chunk_text()` functions, while `embed_and_store.py` imports from it. This divergence happened because the `clean_text()` step turned out to be far more complex than anticipated — the PDF-extracted text required stripping navigation bars, Reddit upvote/comment metadata, ad copy, ligature artifacts, and page-header timestamps before the chunks contained only substantive content. Putting all of that in a single file would have made `embed_and_store.py` difficult to read and test. The two-file structure was adopted to keep concerns separated, even though the spec did not call for it.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Chunking Strategy and Retrieval Approach sections from planning.md, plus the requirement that the output schema from ingestion must be `(chunk_text, source_filename)` tuples. I asked Claude to implement `embed_and_store.py` with a `build_vector_store()` function and a `query(question, k=5)` function using `all-MiniLM-L6-v2` and ChromaDB with cosine similarity.
- *What it produced:* A working `embed_and_store.py` that embedded all chunks, stored them in a persistent ChromaDB collection with source filename metadata, and returned the correct tuple format. It also generated a test block at the bottom that ran all 5 evaluation queries and printed distances alongside chunk previews, which turned out to be useful for debugging retrieval quality.
- *What I changed or overrode:* The initial version used L2 (Euclidean) distance, which ChromaDB defaults to. I overrode this to cosine distance (`{"hnsw:space": "cosine"}`) because cosine similarity is more appropriate for sentence embeddings — it measures directional similarity, not magnitude, so a longer review chunk and a shorter one expressing the same opinion get similar scores. I also added the `try/except` block around `client.delete_collection()` so reruns always rebuild from scratch rather than appending duplicate chunks.

**Instance 2**

- *What I gave the AI:* The Architecture diagram from planning.md, the `query()` function signature from `embed_and_store.py`, and the requirement that the generation step must cite sources by filename and must refuse to answer questions not covered by the documents. I asked Claude to implement `query.py` with a Groq call and `app.py` with a Gradio interface.
- *What it produced:* A `query.py` with a system prompt enforcing strict grounding and a user message template that numbered each retrieved chunk with its source filename. The Gradio UI displayed the answer in one text box and the source filenames in a separate "Retrieved from" panel.
- *What I changed or overrode:* The original system prompt said "try to use only the provided documents" — a soft instruction that left room for the model to supplement with training knowledge. I hardened this to a grounding rule with a specific fallback phrase ("I don't have enough information on that in the provided documents") and set temperature to 0.0, which the initial version had left at the default of 1.0. I also overrode the source attribution mechanism: the first version asked the model to list sources at the end of its answer, which meant sources could be hallucinated or omitted. The final version tracks unique source filenames programmatically from the retrieved chunks and displays them in the UI independently of the model's output.
