from book_agents import safe_slug


def test_safe_slug():
    assert safe_slug("Practical Guide: Agentic AI!") == "practical-guide-agentic-ai"
    assert safe_slug("   ") == "new-book"
