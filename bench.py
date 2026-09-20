from __future__ import annotations

import os
import re
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        pass

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.agent import KnowledgeBaseAgent
from src.chunking import SentenceChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

# 1. Khởi tạo chiến lược chunking của thành viên: SentenceChunker
CHUNKER_NAME = "SentenceChunker (max_sentences_per_chunk=3)"
chunker = SentenceChunker(max_sentences_per_chunk=3)

DATA_DIR = Path("data/ecommerce")

BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Người mua có thể gửi yêu cầu trả hàng/hoàn tiền trong thời hạn bao lâu đối với đơn hàng thông thường?",
        "filter": None,
        "gold": "Đối với sản phẩm mua tại Shop thông thường hoặc Shop Yêu thích: Trong vòng 3 ngày kể từ khi đơn hàng được cập nhật trạng thái 'Giao hàng thành công'.",
        "expected_doc": "return-refund-policy",
    },
    {
        "id": 2,
        "query": "Nếu thanh toán bằng thẻ tín dụng hoặc thẻ ghi nợ thì tiền hoàn được gửi về đâu và mất bao lâu?",
        "filter": None,
        "gold": "Tiền được hoàn về hạn mức thẻ tín dụng hoặc thẻ ghi nợ quốc tế trong vòng 7 đến 14 ngày làm việc.",
        "expected_doc": "buyer-refund-timeline",
    },
    {
        "id": 3,
        "query": "Khi đã nhận hàng nhưng hàng bị lỗi, video mở kiện hàng cần đáp ứng những yêu cầu nào?",
        "filter": None,
        "gold": "Video quay rõ 6 mặt kiện hàng và quá trình khui mở hộp, hình ảnh chụp cận cảnh chi tiết lỗi của sản phẩm, cùng hóa đơn hoặc phiếu giao hàng có mã vận đơn.",
        "expected_doc": "return-refund-policy",
    },
    {
        "id": 4,
        "query": "Nếu Người mua chọn hình thức Tự sắp xếp để trả hàng thì Shopee hỗ trợ phí trả hàng như thế nào?",
        "filter": None,
        "gold": "Người mua cần thanh toán trước phí trả hàng. Shopee sẽ hỗ trợ phí trả hàng tối đa 40.000 VNĐ trong vòng 3 - 5 ngày làm việc nếu khiếu nại được phán quyết là đúng.",
        "expected_doc": "return-refund-policy",
    },
    {
        "id": 5,
        "query": "Với tài liệu có audience=seller, Người bán nên làm gì khi nhận hàng hoàn nhưng sản phẩm bị hư hỏng hoặc không đúng sản phẩm của shop?",
        "filter": {"audience": "seller"},
        "gold": "Người bán bấm nút 'Khiếu nại sàn' trên Kênh Người Bán trong vòng 3 ngày (72 giờ) kể từ khi nhận hàng hoàn, cung cấp video quay 6 mặt kiện hàng hoàn và quá trình mở kiện kiểm tra sản phẩm.",
        "expected_doc": "seller-refund-dispute",
    },
]


def load_corpus() -> list[Document]:
    documents: list[Document] = []
    md_files = sorted(DATA_DIR.glob("*.md"))
    for p in md_files:
        raw_text = p.read_text(encoding="utf-8")
        parts = raw_text.split("---")
        if len(parts) < 3:
            continue
        fm_text = parts[1]
        body = "---".join(parts[2:]).strip()
        fm = dict(re.findall(r"^(\w+):\s*(.+)$", fm_text, re.M))

        chunks = chunker.chunk(body)
        for i, chunk in enumerate(chunks):
            doc_id = p.stem
            chunk_doc = Document(
                id=f"{doc_id}#{i}",
                content=chunk,
                metadata={
                    **fm,
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "source_file": p.name,
                },
            )
            documents.append(chunk_doc)
    return documents


def get_embedder():
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            return _mock_embed
    elif provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            return _mock_embed
    elif provider == "gemini":
        try:
            return GeminiEmbedder(model_name=os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL))
        except Exception:
            return _mock_embed
    return _mock_embed


def demo_llm(prompt: str) -> str:
    # Trích xuất đoạn context đầu tiên để mô phỏng câu trả lời bám sát ngữ cảnh
    lines = [line.strip() for line in prompt.split("\n") if line.strip() and not line.startswith("---") and not line.startswith("Bạn là")]
    snippet = lines[0] if lines else "Không có ngữ cảnh"
    return f"[RAG Agent Response dựa trên {snippet[:80]}...]"


def main() -> None:
    output_lines: list[str] = []

    def log(msg: str = "") -> None:
        try:
            print(msg)
        except UnicodeEncodeError:
            print(msg.encode("ascii", errors="backslashreplace").decode("ascii"))
        output_lines.append(msg)

    log(f"=== BENCHMARK RETRIEVAL — Chiến lược: {CHUNKER_NAME} ===")
    embedder = get_embedder()
    backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    log(f"Embedding backend: {backend_name}")

    docs = load_corpus()
    log(f"Tổng số chunks đã nạp vào Store: {len(docs)} chunks từ {len(list(DATA_DIR.glob('*.md')))} files\n")

    store = EmbeddingStore(collection_name="benchmark_store", embedding_fn=embedder)
    store.add_documents(docs)

    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)

    for item in BENCHMARK_QUERIES:
        qid = item["id"]
        query = item["query"]
        meta_filter = item["filter"]
        gold = item["gold"]
        expected_doc = item["expected_doc"]

        log(f"--------------------------------------------------------------------------------")
        log(f"Query #{qid}: {query}")
        log(f"Metadata filter: {meta_filter}")
        log(f"Gold Answer: {gold}")
        log(f"Tài liệu mong đợi: {expected_doc}")

        results = store.search_with_filter(query, top_k=3, metadata_filter=meta_filter)

        log(f"Top-{len(results)} chunks truy xuất được:")
        for idx, r in enumerate(results, start=1):
            doc_id = r["metadata"].get("doc_id", "N/A")
            score = r.get("score", 0.0)
            preview = r["content"].replace("\n", " ")[:120]
            log(f"  [{idx}] ID={r['id']} | doc_id={doc_id} | score={score:.4f}")
            log(f"      Nội dung: {preview}...")

        answer = agent.answer(query, top_k=3, metadata_filter=meta_filter)
        log(f"Agent Answer: {answer}\n")

    # Thử nghiệm A/B cho Query #5 (có filter vs không filter)
    log("================================================================================")
    log("=== KIỂM CHỨNG A/B CHO QUERY CẦN FILTER (Query #5) ===")
    q5 = BENCHMARK_QUERIES[4]["query"]
    log(f"Query: {q5}")

    log("\n--- [LẦN 1: CÓ FILTER audience='seller'] ---")
    res_with_filter = store.search_with_filter(q5, top_k=3, metadata_filter={"audience": "seller"})
    for idx, r in enumerate(res_with_filter, start=1):
        log(f"  [{idx}] ID={r['id']} | audience={r['metadata'].get('audience')} | score={r['score']:.4f}")

    log("\n--- [LẦN 2: KHÔNG CÓ FILTER (metadata_filter=None)] ---")
    res_no_filter = store.search_with_filter(q5, top_k=3, metadata_filter=None)
    for idx, r in enumerate(res_no_filter, start=1):
        log(f"  [{idx}] ID={r['id']} | audience={r['metadata'].get('audience')} | score={r['score']:.4f}")
    log("================================================================================")

    output_path = Path("ket_qua_benchmark.txt")
    output_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    print(f"\n[OK] Đã lưu toàn bộ kết quả benchmark vào file {output_path} với chuẩn mã hóa UTF-8.")


if __name__ == "__main__":
    main()
