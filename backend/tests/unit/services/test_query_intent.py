from talkingcode.domain.models import QueryIntent
from talkingcode.services.tools.query_intent import QueryIntentExtractor


def test_intent_to_filters_empty():
    extractor = QueryIntentExtractor()
    intent = QueryIntent(refined_query="test")
    filters = extractor.intent_to_filters(intent)
    assert filters == {}


def test_query_intent_repo_filter():
    intent = QueryIntent(refined_query="test", repo_filter="org/repo")
    assert intent.repo_filter == "org/repo"
