import os
import re
import random
import sys
import pdfplumber


def load_documents(docs_dir: str) -> list[tuple[str, str]]:
    """Return (raw_text, source_filename) for every PDF in docs_dir."""
    results = []
    for filename in sorted(os.listdir(docs_dir)):
        if not filename.lower().endswith(".pdf"):
            continue
        filepath = os.path.join(docs_dir, filename)
        pages = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
        raw_text = "\n".join(pages)
        results.append((raw_text, filename))
    return results


_NAV_PATTERNS = [
    r"skip\s+to\s+main\s+content",
    r"^find anything$",                     # Reddit search bar line on its own
    r"find anything\s+ask\s+log in",
    r"search apartments,?\s*cities",
    r"what is epiq\?",
    r"home\s+florida\s+miami",
    r"overview reviews pricing epiq",
    r"contact property",
    r"leave a review",
    r"award winner",
    r"city rank",
    r"trending topics in reviews",
    r"summarized by generative ai",
    r"nearby cities",
    r"apartments (with|by|near|for)\b",   # Advenir footer link lines
    r"^\d+\s*/\s*\d+$",                   # page-number fragments like "1/14"
    r"^sort:\s+newest",
    r"^search review content",
    r"^\d+ upvotes\s*[^\n]*\d+ comments$",  # "6 upvotes · 4 comments"
    r"^\d+ upvotes$",                       # lone "2 upvotes" sidebar lines
    r"^r/[a-zA-Z0-9_]+\s*[^\w]",           # sidebar source lines: "r/FIU · 2y ago"
    r"^ask log in$",
    r"^log in$",
    r"^\d+\s+\d+$",                         # bare number pairs like "21 1"
    r"^Reviews$",                           # Advenir UI label
    r"^\d+\.\d+\s+rating$",                 # "4.3 rating" UI label
    r"^\d+ total reviews",                  # "305 total reviews" UI label
    r"^Community\(\d+\)",                   # "Community(79) Location(27)..." filter bar
    r"reviews with the veri",               # "Reviews with the Verified Badge" boilerplate
    r"satisfacts",                          # SatisFacts boilerplate explanation
    r"·\s*promoted",                        # Reddit ad label ("u/Starbucks · Promoted")
    r"^home\s+internet\s+from\b",          # AT&T promoted-post ad copy
    r"^learn more\b",                       # "Learn More" ad button (line starts)
    r"learn\s+more$",                       # ad CTA at end of line ("domain.com Learn More")
    r"^[a-z0-9\-]+\.(?:com|org|net)\b",    # bare ad domain lines
    r"^view post in$",                      # Reddit translation prompt
    r"^see more$",                          # Reddit "See more" link
    r"home\s+popular\s+news\s+explore",     # Reddit site-wide nav footer
    r"user agreement.+privacy",             # Reddit legal footer
    r"reddit\s*rules.+privacy\s*policy",    # Reddit footer variant
    r"^top\s+posts$",                       # Reddit "TOP POSTS" sidebar header
    r"^rereddit\b",                         # "reReddit: Top posts of …" footer lines
    r"^\d+\s+upvotes?\s*[·•]\s*\d+\s+comments?$",  # "13 upvotes • 1 comment" (singular or plural)
    r"^shop\s+now\b",                       # Reddit promoted-post "Shop Now" CTA
    r"\bhomedepot\.com\b",                  # ad domain that survives URL strip (no https://)
    r"^the expertise a pro can\b",          # ad body fragment for promoted posts
]

_NAV_RE = re.compile("|".join(_NAV_PATTERNS), re.IGNORECASE)

# Strip Unicode private-use-area characters (PDF icon/glyph artifacts, U+E000–U+F8FF)
_PUA_RE = re.compile("[-]")


def clean_text(text: str) -> str:
    """Strip boilerplate and artifacts from PDF-extracted text."""
    # Some PDFs encode the fi ligature as a null byte rather than U+FB01
    text = text.replace("\x00", "fi")
    # Fix common PDF ligature artifacts before stripping PUA
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")   # ﬁ ﬂ standard ligatures
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")            # literal forms
    # Normalize smart quotes and non-breaking spaces
    text = (
        text.replace("’", "'").replace("‘", "'")
            .replace("“", '"').replace("”", '"')
            .replace(" ", " ")
    )
    # Strip private-use-area characters after handling known ligatures
    text = _PUA_RE.sub("", text)
    # Remove residual HTML entities (e.g. &amp; &nbsp;)
    text = re.sub(r"&[a-zA-Z#0-9]+;", " ", text)
    # Remove bare URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove PDF page-header timestamps like "6/11/26, 5:17 PM Site Name"
    text = re.sub(r"\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*[AP]M[^\n]*", "", text)
    # Strip inline boilerplate that appears mid-sentence rather than on its own line
    text = re.sub(r"\[Show More\]", "", text, flags=re.IGNORECASE)
    # Strip "Ask Log In" CTA; also consume a dangling leading word fragment (e.g. "f Log In")
    text = re.sub(r"\b\w{0,4}\s+Log\s+In\b", "", text, flags=re.IGNORECASE)

    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if len(stripped) <= 3:
            continue
        if _NAV_RE.search(stripped):
            continue
        lines.append(stripped)
    return "\n".join(lines)


def chunk_text(
    text: str,
    source: str,
    chunk_size: int = 800,
    overlap: int = 150,
) -> list[tuple[str, str]]:
    """Split text into overlapping fixed-size chunks.

    Returns a list of (chunk_text, source_filename) tuples.
    """
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append((chunk, source))
        if end >= length:
            break
        start = end - overlap
    return chunks


def _safe_print(text: str) -> None:
    """Print text, replacing unencodable characters for the Windows console."""
    encoded = text.encode(sys.stdout.encoding or "utf-8", errors="replace")
    sys.stdout.buffer.write(encoded + b"\n")
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documents")
    _safe_print(f"Loading PDFs from: {docs_dir}\n")

    documents = load_documents(docs_dir)
    _safe_print(f"Loaded {len(documents)} documents\n")

    all_chunks: list[tuple[str, str]] = []
    for raw_text, source in documents:
        cleaned = clean_text(raw_text)
        chunks = chunk_text(cleaned, source)
        all_chunks.extend(chunks)
        _safe_print(
            f"  {source}\n"
            f"    raw={len(raw_text):,} chars  "
            f"clean={len(cleaned):,} chars  "
            f"chunks={len(chunks)}"
        )

    _safe_print(f"\nTotal chunks: {len(all_chunks)}\n")

    _safe_print("=" * 60)
    _safe_print("FIRST 5 CHUNKS")
    _safe_print("=" * 60)
    for i, (chunk, source) in enumerate(all_chunks[:5], 1):
        _safe_print(f"\n[{i}] source : {source}")
        _safe_print(f"    length : {len(chunk)} chars")
        _safe_print(f"    text   : {chunk[:400]}{'...' if len(chunk) > 400 else ''}")

    _safe_print("\n" + "=" * 60)
    _safe_print("5 RANDOM CHUNKS")
    _safe_print("=" * 60)
    for i, (chunk, source) in enumerate(random.sample(all_chunks, min(5, len(all_chunks))), 1):
        _safe_print(f"\n[{i}] source : {source}")
        _safe_print(f"    length : {len(chunk)} chars")
        _safe_print(f"    text   : {chunk[:400]}{'...' if len(chunk) > 400 else ''}")
