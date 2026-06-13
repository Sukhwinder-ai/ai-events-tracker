from aiscraper.relevance import is_relevant


# Real AI/ML events — must be kept.
KEEP_AI = [
    "AI & Society | AI in Healthcare",
    "Brisbane AI Builders — RAG & Agents Night",
    "NLP Practitioner 2024",
    "Measuring AI Quality: Real world case study",
    "Global AI Community Day: Graph Powered Agents",
    "Artificial Intelligence in Project Management",
    "Curious Minds: Machine Learning for Professionals",
    "Intro to LLMs and GPT prompting",
    "Generative AI for designers",
]

# Adjacent tech communities the filter should keep.
KEEP_TECH = [
    "Claude Workshop",
    "Google Gemini Workshop",
    "Copilot - Workshop",
    "Perplexity Workshop",
    "Brisbane Databricks Community Meetup July 2026",
    "AWS Brisbane User Group - 18th Jun 2026",
    "GDG Brisbane Monthly Meetup - June 22, 2026",
    "[In-Person ONLY] Microsoft Fabric CAT Team",
]

# Tech/startup/science/professional events that carry NO explicit AI keyword
# but which the user manually verified as useful — these must be KEPT. The
# filter is keep-by-default (recall over precision): we'd rather show an
# off-topic event than silently miss a real one.
KEEP_NO_KEYWORD = [
    "You're not stuck. Your identity is just outdated.",
    "Brisbane Founders, Freelancers & Creators Networking Night",
    "If you build it, they will come",
    "Sunday (mad) Science - Bring a problem seek an answer",
    '"Water Meets Metal" — Realtime GPU Fountain Rendering',
    "Phantom Proof Attacks via Weaponized Censorship Resistance in Polygon CDK zkEVM",
    "JDP Unpacked",
    "Entrepreneurship & Digital Skills Series – Workshop 3",
]

# Only clear lifestyle/wellness/social-language spam is dropped.
DROP_NOISE = [
    "🔥Asian Background Social: Lounge Asia Meetup (Easy English) @ Brisbane",
    "🧘Guided Meditation 🧘‍♂️@ New Farm Library",
    "Stop Attracting Emotionally Unavailable Partners: Speak Up for Your Needs",
    "AIBconnect: Brisbane",
]


def test_keeps_real_ai_events():
    for title in KEEP_AI:
        assert is_relevant(title), f"should keep: {title}"


def test_keeps_adjacent_tech_events():
    for title in KEEP_TECH:
        assert is_relevant(title), f"should keep: {title}"


def test_keeps_useful_events_without_an_ai_keyword():
    for title in KEEP_NO_KEYWORD:
        assert is_relevant(title), f"should keep: {title}"


def test_drops_clear_noise():
    for title in DROP_NOISE:
        assert not is_relevant(title), f"should drop: {title}"


def test_drops_wellness_spam_even_with_stuffed_ai_token():
    # Organisers keyword-stuff "AI" into wellness titles; the denylist catches it.
    assert not is_relevant(
        "Stop Leaking Energy: Breathwork Reset for Stress and the AI Overwhelm"
    )


def test_handles_empty_or_none_title():
    assert not is_relevant("")
    assert not is_relevant(None)
