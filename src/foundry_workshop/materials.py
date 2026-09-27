from typing import Any


def policy_document_text(document: dict[str, Any]) -> str:
    return (
        "SYNTHETIC WORKSHOP POLICY - NOT A REAL COMPANY POLICY\n\n"
        f"Document ID: {document['id']}\n"
        f"Title: {document['title']}\n"
        f"Effective: {document['effective_from']} through {document['effective_to']}\n\n"
        f"{document['content']}\n"
    )
