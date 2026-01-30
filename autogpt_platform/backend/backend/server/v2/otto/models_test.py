import pydantic
import pytest

import backend.server.v2.otto.models


def test_document_model() -> None:
    doc = backend.server.v2.otto.models.Document(
        url="https://example.com/doc",
        relevance_score=0.95,
    )
    assert doc.url == "https://example.com/doc"
    assert doc.relevance_score == 0.95


def test_api_response_model() -> None:
    doc = backend.server.v2.otto.models.Document(
        url="https://example.com/result",
        relevance_score=0.87,
    )
    response = backend.server.v2.otto.models.ApiResponse(
        answer="The answer is 42.",
        documents=[doc],
        success=True,
    )
    assert response.answer == "The answer is 42."
    assert len(response.documents) == 1
    assert response.documents[0].url == "https://example.com/result"
    assert response.success is True


def test_api_response_empty_documents() -> None:
    response = backend.server.v2.otto.models.ApiResponse(
        answer="No documents found.",
        documents=[],
        success=False,
    )
    assert response.documents == []
    assert response.success is False


def test_graph_data_model() -> None:
    graph = backend.server.v2.otto.models.GraphData(
        nodes=[{"id": "node-1", "type": "input"}, {"id": "node-2", "type": "output"}],
        edges=[{"source": "node-1", "target": "node-2"}],
        graph_name="My Graph",
        graph_description="A test graph with two nodes",
    )
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.graph_name == "My Graph"
    assert graph.graph_description == "A test graph with two nodes"


def test_graph_data_model_optional_fields() -> None:
    graph = backend.server.v2.otto.models.GraphData(
        nodes=[{"id": "node-1"}],
        edges=[],
    )
    assert graph.graph_name is None
    assert graph.graph_description is None


def test_message_model() -> None:
    message = backend.server.v2.otto.models.Message(
        query="What is the weather?",
        response="It is sunny today.",
    )
    assert message.query == "What is the weather?"
    assert message.response == "It is sunny today."


def test_chat_request_model() -> None:
    history_msg = backend.server.v2.otto.models.Message(
        query="Hello",
        response="Hi there!",
    )
    request = backend.server.v2.otto.models.ChatRequest(
        query="How are you?",
        conversation_history=[history_msg],
        message_id="msg-123",
        include_graph_data=True,
        graph_id="graph-456",
    )
    assert request.query == "How are you?"
    assert len(request.conversation_history) == 1
    assert request.conversation_history[0].query == "Hello"
    assert request.message_id == "msg-123"
    assert request.include_graph_data is True
    assert request.graph_id == "graph-456"


def test_chat_request_defaults() -> None:
    request = backend.server.v2.otto.models.ChatRequest(
        query="Test query",
        conversation_history=[],
        message_id="msg-789",
    )
    assert request.include_graph_data is False
    assert request.graph_id is None
