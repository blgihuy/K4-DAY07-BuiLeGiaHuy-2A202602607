from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3, metadata_filter: dict | None = None) -> str:
        if self.store.get_collection_size() == 0:
            return "Cơ sở tri thức hiện chưa có tài liệu nào để trả lời câu hỏi."

        if metadata_filter:
            results = self.store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = self.store.search(question, top_k=top_k)

        if not results:
            return "Không tìm thấy thông tin liên quan trong cơ sở tri thức để trả lời câu hỏi."

        context_parts = []
        for i, r in enumerate(results, start=1):
            source = (
                r["metadata"].get("title")
                or r["metadata"].get("source")
                or r["metadata"].get("doc_id")
                or r.get("id")
                or "Nguồn không xác định"
            )
            context_parts.append(f"[{i}] (Nguồn: {source})\n{r['content']}")

        context = "\n\n".join(context_parts)

        prompt = (
            "Bạn là một trợ lý AI thông minh hỗ trợ trả lời câu hỏi dựa trên cơ sở tri thức được cung cấp.\n"
            "Chỉ sử dụng các thông tin trong phần Ngữ cảnh dưới đây để trả lời câu hỏi. "
            "Không tự suy đoán hoặc bịa đặt thông tin ngoài ngữ cảnh. "
            "Nếu thông tin không có trong ngữ cảnh, hãy nói rõ 'Tôi không tìm thấy thông tin này trong tài liệu'.\n"
            "Khi trả lời, hãy trích dẫn số thứ tự của tài liệu [1], [2] tương ứng với thông tin bạn sử dụng.\n\n"
            f"--- NGỮ CẢNH ---\n{context}\n\n"
            f"--- CÂU HỎI ---\n{question}\n\n"
            "--- CÂU TRẢ LỜI ---"
        )

        return self.llm_fn(prompt)
