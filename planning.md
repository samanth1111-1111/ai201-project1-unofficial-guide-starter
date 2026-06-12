# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
I choose off campus housing experiences. This knowlege is valuable to someone who want to learn more than just basic information about rent as it can answer question about the enviroment.
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | r/FIU — Off-Campus Housing Guide Fall 2025 | Community-written guide ranking Terrazul, Mana, The One, Brickell House, Landmark, and UA by price, walkability, and amenities (9 pages, ~13,600 chars) | https://www.reddit.com/r/FIU/comments/1ly4sm5/offcampus_housing_guide_for_fall_2025/ |
| 2 | r/FIU — University Apartments thread | Student experiences at UA: mold, bugs, wifi, parking, squatters, mixed reviews (7 pages, ~8,300 chars) | https://www.reddit.com/r/FIU/comments/1imarrk/university_apartments/ |
| 3 | r/FIU — Housing and social concerns | Incoming student Q&A on housing availability and social life at FIU (6 pages, ~9,500 chars) | https://www.reddit.com/r/FIU/comments/1qm6vwg/housing_and_social_concerns/ |
| 4 | r/FIU — Don't rent at the One | Warning thread: management ignores issues, mail theft, car towing at The One at University City (6 pages, ~6,000 chars) | https://www.reddit.com/r/FIU/comments/12iug2w/dont_rent_at_the_one/ |
| 5 | r/FIU — Apartments near FIU for alumni | Discussion of walkable off-campus options for FIU alumni (5 pages, ~4,400 chars) | https://www.reddit.com/r/FIU/comments/1m1j3co/are_there_any_apartments_near_fiu_where_alumnis/ |
| 6 | r/FIU — Looking for housing | International student thread asking for affordable housing advice near FIU (6 pages, ~4,800 chars) | https://www.reddit.com/r/FIU/comments/1hb11ws/looking_for_housing/ |
| 7 | ApartmentRatings — Advenir at University Park | 305 resident reviews of Advenir at University Park (10495 SW 14th Terrace); rated 4.3/5 at $1,584–$2,484/mo (14 pages, ~25,700 chars) | https://www.apartmentratings.com/fl/miami/advenir-at-university-park_305220720233174/ |
| 8 | Apartments.com — FIU off-campus listings | Search results page for rentals near FIU Modesto Maidique (sparse, 1 page, ~1,400 chars) | https://www.apartments.com/off-campus-housing/fl/miami/florida-international-university-modesto-maidique-campus/ |
| 9 | College Pads — FIU off-campus housing | Listing aggregator for off-campus student housing near FIU (sparse, 1 page, ~700 chars) | https://www.rentcollegepads.com/off-campus-housing/fiu/search |
| 10 | r/FIU — FIU Housing | Thread about on-campus housing availability denial for fall admits (7 pages, ~6,700 chars) | https://www.reddit.com/r/FIU/comments/1br1c9m/fiu_housing/ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 800 characters (~200 tokens)

**Overlap:** 150 characters (~38 tokens)

**Reasoning:** The corpus is mostly Reddit threads and review snippets — individual comments range from one sentence to two short paragraphs. An 800-character chunk fits one to three comments, which preserves a complete opinion without merging unrelated voices. Two listing pages (Apartments.com, College Pads) extracted barely 700–1,400 characters total; smaller chunks let even those sparse documents contribute at least one retrievable unit. The 150-character overlap (~2 sentences) prevents splitting a single reviewer's key claim across a boundary (e.g., "management ignores issues" and the supporting example ending up in different chunks).

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Top-k:** 5

**Production tradeoff reflection:** `all-MiniLM-L6-v2` is fast and free but has a 256-token context window — chunks near that limit get truncated before embedding, which could lose the tail of a longer review. For production I would weigh `text-embedding-3-small` (OpenAI, 8,192-token window, stronger semantic accuracy) against the per-call cost. FIU's student body is majority Hispanic, so a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` could recover Spanish-language comments that plain `all-MiniLM` might rank lower. Latency matters too: a synchronous embedding step at query time adds ~50ms locally but could exceed 200ms on a cold Lambda function, pushing toward pre-warmed endpoints.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What specific problems do students report about The One at University City? | Management ignores pressing issues; packages and mail are stolen or lost by staff and can't be picked up for nearly a week; cars are towed exactly at curfew by trucks that sit waiting; dirty hallways with trash left by residents. Source: "Don't rent at the One" thread. |
| 2 | What is the monthly rent range at Advenir at University Park, and what do reviewers say about management? | $1,584–$2,484/month; 4.3/5 from 305 reviews. Source: Advenir ApartmentRatings page. Expected answer: the system surfaces the price range and a sentiment summary from the reviews page. |
| 3 | According to the Fall 2025 off-campus guide, what hidden fees does Terrazul charge on top of listed rent? | Up to $200+ in extra fees: parking, "premium floor" surcharges (~$30/mo), amenity premiums, liability fees, and utility fees. Source: OFF-Campus Housing Guide for Fall 2025. |
| 4 | What maintenance issues did students report at University Apartments (UA)? | Mold in air vents, mold and stains in shower/bathroom, bug/termite infestation in the kitchen, broken drawers, slow wifi. Source: University Apartments thread. |
| 5 | What advice do students give to international students looking for affordable housing near FIU for spring intake? | This question is intended to surface a failure: the corpus has limited direct advice targeted specifically at international students for spring; expected result is partial or vague. The system should cite "Looking for housing" and "Are there any apartments near FIU" threads but may hallucinate specific prices or complexes not mentioned in those threads. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Sparse listing pages pollute the vector store.** Two sources (Apartments.com, College Pads) extracted only 700–1,400 characters of usable text — mostly navigation UI, filter labels, and one or two property names. These will generate low-information chunks that may rank highly for generic queries like "apartments near FIU" and crowd out the richer Reddit content. Risk: the system returns a chunk that says "Terrazul — 4 Bed" with no useful detail.

2. **Comment-without-context chunks.** Reddit threads are exported as a flat stream of replies. A chunk that starts mid-thread — e.g., "Yeah, I had the same problem" or "It depends on which floor you're on" — has no subject and will embed ambiguously. It may retrieve on a surface word match (e.g., "floor") but deliver a confusing, source-less answer. This is compounded by the fact that the source filename becomes the only attribution, which doesn't tell the user which apartment the commenter was discussing.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```
Document Ingestion          Chunking                  Embedding + Vector Store
─────────────────           ──────────────────────    ──────────────────────────────
10 PDF files                plain Python              all-MiniLM-L6-v2
in documents/               string slicing            (sentence-transformers)
        │                   chunk=800 chars           stored in ChromaDB
        ▼                   overlap=150 chars         with source filename metadata
  pdfplumber                        │                          │
  (extract_text()                   ▼                          ▼
   per page)              List of (chunk, source)     Retrieval (top-k=5)
        │                           │                          │
        ▼                           └──────────────────────────┘
  raw text strings                                             │
                                                               ▼
                                                     Generation
                                                     Groq (llama-3.3-70b-versatile)
                                                     prompt includes retrieved chunks
                                                     + source filenames
                                                     answer cites sources by filename
                                                               │
                                                               ▼
                                                     Query Interface
                                                     Gradio or Streamlit
                                                     (Milestone 5)
```

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
- Tool: Claude
- Input: The Chunking Strategy section above. The documents table showing 10 PDFs with their character counts
- Ask it to implement `ingest.py` with a `load_documents(docs_dir)` function using pdfplumber and a `chunk_text(text, source, chunk_size=800, overlap=150)` function using plain Python string slicing that returns `(chunk_text, source_filename)` tuples
- Verify: run `python ingest.py` and print the first 5 chunks with their source labels; confirm chunk lengths are within ±50 chars of 800 and that the source filename is attached

**Milestone 4 — Embedding and retrieval:**
- Tool: Claude
- Input: The Retrieval Approach section + the output schema from Milestone 3 (`(chunk, source)` list)
- Ask it to implement `embed_and_store.py` that embeds all chunks with `all-MiniLM-L6-v2`, stores them in ChromaDB with source metadata, and exposes a `query(question, k=5)` function that returns `[(chunk, source), ...]`
- Verify: run the 5 evaluation questions from the Evaluation Plan; manually check that the returned chunks contain the expected keywords (e.g., "$1,584" for Q2, "mold" for Q4)

**Milestone 5 — Generation and interface:**
- Tool: Claude
- Input: The Architecture diagram. The `query()` function signature from Milestone 4. The requirement that answers must cite source filenames
- Ask it to implement `generate.py` with a Groq call that receives top-5 chunks + sources, formats them into a prompt, and appends a "Sources:" section to every answer
- Ask it to wrap this in a Gradio `gr.Interface` with a text input and markdown output
- Verify: run all 5 evaluation questions through the UI; confirm Q5 either returns a citation or explicitly states information is not in the documents (not a fabricated answer)
