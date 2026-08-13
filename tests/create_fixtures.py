"""Generate synthetic test fixtures for all provider exports."""

import json
import zipfile
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def create_openai_fixture():
    conversations = [
        {
            "id": "conv-001",
            "title": "Python Help",
            "create_time": 1700000000.0,
            "update_time": 1700001000.0,
            "current_node": "msg-3",
            "mapping": {
                "root": {
                    "id": "root",
                    "parent": None,
                    "children": ["msg-system"],
                    "message": None,
                },
                "msg-system": {
                    "id": "msg-system",
                    "parent": "root",
                    "children": ["msg-1"],
                    "message": {
                        "author": {"role": "system"},
                        "content": {"content_type": "text", "parts": ["You are a helpful assistant."]},
                    },
                },
                "msg-1": {
                    "id": "msg-1",
                    "parent": "msg-system",
                    "children": ["msg-2", "msg-2-branch"],
                    "message": {
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["How do I read a file in Python?"]},
                    },
                },
                "msg-2": {
                    "id": "msg-2",
                    "parent": "msg-1",
                    "children": ["msg-3"],
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["Use open() with a context manager."]},
                    },
                },
                "msg-2-branch": {
                    "id": "msg-2-branch",
                    "parent": "msg-1",
                    "children": [],
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["You can use pathlib.Path.read_text()."]},
                    },
                },
                "msg-3": {
                    "id": "msg-3",
                    "parent": "msg-2",
                    "children": [],
                    "message": {
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Thanks!"]},
                    },
                },
            },
        },
        {
            "id": "conv-002",
            "title": "Image Generation",
            "create_time": 1700010000.0,
            "update_time": 1700011000.0,
            "current_node": "msg-2",
            "mapping": {
                "root": {
                    "id": "root",
                    "parent": None,
                    "children": ["msg-1"],
                    "message": None,
                },
                "msg-1": {
                    "id": "msg-1",
                    "parent": "root",
                    "children": ["msg-2"],
                    "message": {
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Generate an image of a cat"]},
                    },
                },
                "msg-2": {
                    "id": "msg-2",
                    "parent": "msg-1",
                    "children": [],
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"content_type": "multimodal_text", "parts": [
                            "Here's the image:",
                            {"content_type": "image_asset_pointer", "asset_pointer": "file-abc123"}
                        ]},
                    },
                },
            },
        },
        {
            "id": "conv-003",
            "title": "Code Execution",
            "create_time": 1700020000.0,
            "update_time": 1700021000.0,
            "current_node": "msg-3",
            "mapping": {
                "root": {
                    "id": "root",
                    "parent": None,
                    "children": ["msg-1"],
                    "message": None,
                },
                "msg-1": {
                    "id": "msg-1",
                    "parent": "root",
                    "children": ["msg-2"],
                    "message": {
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["Run print(2+2)"]},
                    },
                },
                "msg-2": {
                    "id": "msg-2",
                    "parent": "msg-1",
                    "children": ["msg-3"],
                    "message": {
                        "author": {"role": "assistant"},
                        "content": None,
                        "content_type": "code",
                    },
                },
                "msg-3": {
                    "id": "msg-3",
                    "parent": "msg-2",
                    "children": [],
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["The result is 4."]},
                    },
                },
            },
        },
    ]

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = FIXTURES_DIR / "openai-sample.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("conversations.json", json.dumps(conversations, indent=2))

    print(f"Created {zip_path}")


def create_anthropic_fixture():
    conversations = [
        {
            "uuid": "conv-a001",
            "name": "Rust Basics",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "chat_messages": [
                {"sender": "human", "text": "What is ownership in Rust?"},
                {"sender": "assistant", "text": "Ownership is Rust's memory management system. Each value has a single owner."},
                {"sender": "human", "text": "Can you show an example?"},
                {"sender": "assistant", "text": "let s1 = String::from(\"hello\");\nlet s2 = s1; // s1 is moved to s2"},
            ],
        },
        {
            "uuid": "conv-a002",
            "name": "Tool Use Example",
            "created_at": "2024-01-16T14:00:00Z",
            "updated_at": "2024-01-16T14:15:00Z",
            "chat_messages": [
                {"sender": "human", "text": "Search for the weather"},
                {
                    "sender": "assistant",
                    "text": [
                        {"type": "text", "text": "Let me search for that."},
                        {"type": "tool_use", "name": "web_search", "input": {"query": "weather today"}},
                    ],
                },
                {"sender": "human", "text": "Thanks!"},
            ],
        },
        {
            "uuid": "conv-a003",
            "name": "Simple Chat",
            "created_at": "2024-01-17T09:00:00Z",
            "updated_at": "2024-01-17T09:05:00Z",
            "chat_messages": [
                {"sender": "human", "text": "Hello!"},
                {"sender": "assistant", "text": "Hello! How can I help you today?"},
            ],
        },
    ]

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = FIXTURES_DIR / "anthropic-sample.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("conversations.json", json.dumps(conversations, indent=2))

    print(f"Created {zip_path}")


def create_corrupt_fixture():
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = FIXTURES_DIR / "corrupt.zip"
    zip_path.write_bytes(b"this is not a zip file")
    print(f"Created {zip_path}")


def create_wrong_format_fixture():
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = FIXTURES_DIR / "wrong-format.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("random_file.txt", "This is not a conversations export")
    print(f"Created {zip_path}")


def create_xai_fixture():
    data = {
        "conversations": [
            {
                "conversation": {
                    "id": "grok-conv-001",
                    "title": "Python Basics",
                    "create_time": "2025-06-15T10:00:00Z",
                    "modify_time": "2025-06-15T10:30:00Z",
                },
                "responses": [
                    {"response": {"sender": "human", "message": "What is a list comprehension?"}},
                    {"response": {"sender": "assistant", "message": "A list comprehension is a concise way to create lists."}},
                    {"response": {"sender": "human", "message": "Show me an example."}},
                    {"response": {"sender": "assistant", "message": "[x**2 for x in range(10)]"}},
                ],
            },
            {
                "conversation": {
                    "id": "grok-conv-002",
                    "title": "Image Chat",
                    "create_time": "2025-06-16T14:00:00Z",
                    "modify_time": "2025-06-16T14:15:00Z",
                },
                "responses": [
                    {"response": {"sender": "human", "message": "Draw me a sunset"}},
                    {"response": {"sender": "ASSISTANT", "message": "Here is a beautiful sunset image."}},
                ],
            },
            {
                "conversation": {
                    "id": "grok-conv-003",
                    "title": "Quick Question",
                    "create_time": "2025-06-17T09:00:00Z",
                    "modify_time": "2025-06-17T09:05:00Z",
                },
                "responses": [
                    {"response": {"sender": "human", "message": "Hello Grok!"}},
                    {"response": {"sender": "grok-3", "message": "Hello! How can I help?"}},
                ],
            },
        ],
    }

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = FIXTURES_DIR / "xai-sample.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(
            "ttl/30d/export_data/user123/prod-grok-backend.json",
            json.dumps(data, indent=2),
        )

    print(f"Created {zip_path}")


def create_mistral_fixture():
    chat1 = [
        {
            "id": "msg-001",
            "chatId": "chat-aaa",
            "role": "user",
            "createdAt": "2025-06-15T10:00:00Z",
            "content": "Explain decorators in Python.",
            "contentChunks": None,
        },
        {
            "id": "msg-002",
            "chatId": "chat-aaa",
            "role": "assistant",
            "createdAt": "2025-06-15T10:00:30Z",
            "content": "Decorators are functions that modify other functions.",
            "contentChunks": None,
        },
        {
            "id": "msg-003",
            "chatId": "chat-aaa",
            "role": "user",
            "createdAt": "2025-06-15T10:01:00Z",
            "content": "Can you show an example?",
            "contentChunks": None,
        },
        {
            "id": "msg-004",
            "chatId": "chat-aaa",
            "role": "assistant",
            "createdAt": "2025-06-15T10:01:30Z",
            "content": "@decorator\ndef my_func(): pass",
            "contentChunks": None,
        },
    ]

    chat2 = [
        {
            "id": "msg-005",
            "chatId": "chat-bbb",
            "role": "user",
            "createdAt": "2025-06-16T14:00:00Z",
            "content": "Search the web for weather",
            "contentChunks": None,
        },
        {
            "id": "msg-006",
            "chatId": "chat-bbb",
            "role": "assistant",
            "createdAt": "2025-06-16T14:00:30Z",
            "content": "",
            "contentChunks": [
                {"type": "text", "content": "Let me search for that."},
                {"type": "tool_call", "name": "web_search"},
            ],
        },
    ]

    chat3 = [
        {
            "id": "msg-007",
            "chatId": "chat-ccc",
            "role": "user",
            "createdAt": "2025-06-17T09:00:00Z",
            "content": "Hello Le Chat!",
            "contentChunks": None,
        },
        {
            "id": "msg-008",
            "chatId": "chat-ccc",
            "role": "assistant",
            "createdAt": "2025-06-17T09:00:30Z",
            "content": "Hello! How can I assist you today?",
            "contentChunks": None,
        },
    ]

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = FIXTURES_DIR / "mistral-sample.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("chat-aaa.json", json.dumps(chat1, indent=2))
        zf.writestr("chat-bbb.json", json.dumps(chat2, indent=2))
        zf.writestr("chat-ccc.json", json.dumps(chat3, indent=2))

    print(f"Created {zip_path}")


def create_perplexity_fixture():
    threads = [
        {
            "slug": "pplx-thread-001",
            "title": "Python Async",
            "created_at": "2025-06-15T10:00:00Z",
            "updated_at": "2025-06-15T10:30:00Z",
            "steps": [
                {
                    "step_type": "INITIAL_QUERY",
                    "query_str": "How does async/await work in Python?",
                    "final_response": "Python uses asyncio for asynchronous programming.",
                },
                {
                    "step_type": "FOLLOW_UP",
                    "query_str": "Show me an example",
                    "final_response": "import asyncio\nasync def main(): ...",
                },
            ],
        },
        {
            "slug": "pplx-thread-002",
            "title": "Machine Learning",
            "created_at": "2025-06-16T14:00:00Z",
            "updated_at": "2025-06-16T14:15:00Z",
            "steps": [
                {
                    "step_type": "INITIAL_QUERY",
                    "query_str": "What is gradient descent?",
                    "final_response": "Gradient descent is an optimization algorithm.",
                },
            ],
        },
        {
            "slug": "pplx-thread-003",
            "title": "Quick Search",
            "created_at": "2025-06-17T09:00:00Z",
            "updated_at": "2025-06-17T09:05:00Z",
            "steps": [
                {
                    "step_type": "INITIAL_QUERY",
                    "query_str": "Weather in Berlin today",
                    "final_response": "Current weather in Berlin: 22C, partly cloudy.",
                },
            ],
        },
    ]

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = FIXTURES_DIR / "perplexity-sample.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("threads.json", json.dumps(threads, indent=2))

    print(f"Created {zip_path}")


if __name__ == "__main__":
    create_openai_fixture()
    create_anthropic_fixture()
    create_corrupt_fixture()
    create_wrong_format_fixture()
    create_xai_fixture()
    create_mistral_fixture()
    create_perplexity_fixture()
