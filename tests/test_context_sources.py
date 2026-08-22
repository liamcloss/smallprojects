from app.services.context import make_context


def test_context_distinguishes_calendar_and_manual_hints():
    context = make_context("United Kingdom", ["Sunday evening"])
    types = [source.source_type for source in context.sources]
    assert "calendar" in types
    assert "manual_hint" in types
    manual = next(source for source in context.sources if source.source_type == "manual_hint")
    assert manual.title == "Sunday evening"
