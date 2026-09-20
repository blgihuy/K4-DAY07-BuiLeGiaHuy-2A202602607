# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Người Đột Tử
**Thành viên:** Bùi Lê Gia Huy - 02607, Trần Anh Đăng - 02992, Nguyễn Khánh Đô - 02687
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn
**Chủ đề:** Chính sách đổi trả, hoàn tiền và bảo hành trên nền tảng thương mại điện tử (E-commerce Returns & Warranty Policies)

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề chính sách đổi trả, hoàn tiền và bảo hành thương mại điện tử vì đây là nghiệp vụ cốt lõi, thường xuyên phát sinh thắc mắc và tranh chấp giữa người mua và người bán. Bộ dữ liệu chứa nhiều mốc thời gian, điều kiện ngoại lệ và quy định phân hóa rõ rệt theo đối tượng (`buyer` vs `seller`), là bài toán lý tưởng để đánh giá khả năng trích xuất chính xác của hệ thống RAG và chứng minh hiệu quả của cơ chế lọc metadata (`metadata_filter`).


### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|---|---|---|---:|---|
| 1 | Thời gian nhận tiền hoàn và cách kiểm tra tiền hoàn | Shopee Help Center article 189473 | 2026-09-20 / not-stated | 5,255 | `audience=buyer`, `category=refund-timeline`, `language=vi` |
| 2 | Những quy định chung về Trả hàng/Hoàn tiền của Shopee | Shopee Help Center article 188931 | 2026-09-20 / not-stated | 8,061 | `audience=buyer`, `category=return-refund-general-rules`, `language=vi` |
| 3 | Hướng dẫn gửi yêu cầu Trả hàng/Hoàn tiền | Shopee Help Center article 79233 | 2026-09-20 / not-stated | 4,240 | `audience=buyer`, `category=return-refund-request`, `language=vi` |
| 4 | Quy trình Shopee xử lý yêu cầu Trả hàng/Hoàn tiền | Shopee Help Center article 190242 | 2026-09-20 / not-stated | 6,021 | `audience=buyer`, `category=return-refund-processing`, `language=vi` |
| 5 | Hướng dẫn chuẩn bị bằng chứng khi yêu cầu Trả hàng/Hoàn tiền | Shopee Help Center article 79467 | 2026-09-20 / not-stated | 4,659 | `audience=buyer`, `category=return-refund-evidence`, `language=vi` |
| 6 | Theo dõi tình trạng Trả hàng/Hoàn tiền trên Shopee | Shopee Help Center article 79298 | 2026-09-20 / not-stated | 2,538 | `audience=buyer`, `category=return-refund-tracking`, `language=vi` |
| 7 | Các phương thức gửi hàng hoàn trả và phí hoàn trả | Shopee Help Center article 189477 | 2026-09-20 / not-stated | 7,875 | `audience=buyer`, `category=return-shipping-fees`, `language=vi` |
| 8 | Cách theo dõi tình trạng vận chuyển hàng hoàn trả | Shopee Help Center article 189476 | 2026-09-20 / not-stated | 2,741 | `audience=buyer`, `category=return-logistics`, `language=vi` |
| 9 | Quy định trả hàng, hoàn tiền và bảo hành đối với Người bán trên Shopee | Chưa có nguồn chính thức | 2026-09-20 / ai-generated-summary-not-official | 5,798 | `audience=seller`, `category=seller-return-warranty-policy`, `language=vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu chính chỉ chứa nguồn công khai từ Shopee Help Center và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu chính có `source_url`, `retrieved_at`, `document_version` trong metadata.
- [ ] Tài liệu `seller-warranty-policy.md` cần bổ sung nguồn chính thức nếu nhóm muốn dùng trong benchmark chấm điểm.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất? |
|---|---|---|---|
| `doc_id` | string | `shopee-return-refund-evidence-guide` | Định danh duy nhất cho tài liệu, giúp truy vết chunk thuộc tài liệu nào. |
| `title` | string | `[Trả hàng/Hoàn tiền] Hướng dẫn chuẩn bị bằng chứng...` | Giúp người đọc và hệ thống hiểu nhanh chủ đề tài liệu. |
| `audience` | enum | `buyer`, `seller`, `both` | Cho phép lọc theo đối tượng, ví dụ chỉ lấy chính sách dành cho Người mua hoặc Người bán. |
| `category` | string | `return-refund-evidence`, `refund-timeline` | Giúp lọc/tổ chức tài liệu theo nghiệp vụ cụ thể. |
| `language` | string | `vi` | Xác định ngôn ngữ tài liệu. |
| `source_url` | URL/string | `https://help.shopee.vn/...` | Truy vết nguồn gốc câu trả lời và kiểm chứng gold answer. |
| `retrieved_at` | date | `2026-09-20` | Cho biết ngày nhóm thu thập tài liệu. |
| `document_version` | string | `not-stated` | Ghi phiên bản/ngày hiệu lực nếu nguồn có nêu; nếu không thì đánh dấu `not-stated`. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu (chunk_size=500):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `return-refund-policy.md` | FixedSizeChunker (`fixed_size`) | 10 | 276.9 | Một phần (cắt cứng ký tự dễ đứt đoạn giữa câu) |
| `return-refund-policy.md` | SentenceChunker (`by_sentences`) | 6 | 385.2 | Rất tốt (mỗi chunk gồm 3 câu trọn vẹn ngữ nghĩa điều khoản) |
| `return-refund-policy.md` | RecursiveChunker (`recursive`) | 12 | 192.0 | Tốt (chia nhỏ theo đoạn và cấu trúc gạch đầu dòng) |
| `seller-warranty-policy.md` | FixedSizeChunker (`fixed_size`) | 9 | 272.8 | Một phần (dễ cắt đôi mốc thời gian quy định) |
| `seller-warranty-policy.md` | SentenceChunker (`by_sentences`) | 5 | 409.6 | Rất tốt (mỗi chế tài và thời hạn bảo hành nằm trọn trong câu) |
| `seller-warranty-policy.md` | RecursiveChunker (`recursive`) | 11 | 185.5 | Tốt (tách theo từng mục nhỏ) |
| `buyer-warranty-process.md` | FixedSizeChunker (`fixed_size`) | 8 | 290.1 | Một phần (mất ngữ cảnh bước tiếp theo) |
| `buyer-warranty-process.md` | SentenceChunker (`by_sentences`) | 5 | 393.0 | Rất tốt (từng bước quy trình được bảo toàn nguyên vẹn) |
| `buyer-warranty-process.md` | RecursiveChunker (`recursive`) | 11 | 178.0 | Tốt (mảnh nhỏ gọn) |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Bùi Lê Gia Huy**
- **Loại chiến lược:** SentenceChunker (`by_sentences`, `max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn cho chủ đề này:** Sử dụng biểu thức chính quy lookbehind để chia văn bản theo ranh giới câu hoàn chỉnh, sau đó gom 3 câu thành một chunk. Trong văn bản chính sách TMĐT, mỗi điều khoản, mốc thời gian hay chế tài đều được phát biểu trọn vẹn trong một câu; cách chia này đảm bảo không làm đứt gãy thông tin ngữ nghĩa và cung cấp đủ ngữ cảnh cục bộ cho embedding.
- **Code snippet (nếu custom):**
```python
# Tách câu bảo toàn dấu câu và gom nhóm 3 câu/chunk
raw_sentences = re.split(r"(?<=[.!?])(?:\s+|\n+)", text.strip())
sentences = [s.strip() for s in raw_sentences if s.strip()]
chunks = [" ".join(sentences[i:i+3]).strip() for i in range(0, len(sentences), 3)]
```

**Thành viên 2 — [Nguyễn Khánh Đô]**
- **Loại chiến lược:** RecursiveChunker
- **Mô tả & lý do chọn:** Chiến lược chia văn bản đệ quy theo thứ tự ưu tiên từ cấu trúc lớn đến nhỏ, chẳng hạn đoạn văn, dòng, câu, từ và cuối cùng là ký tự. Với tài liệu chính sách TMĐT của Shopee, cách này giúp ưu tiên giữ nguyên các đoạn và câu hoàn chỉnh, đồng thời vẫn bảo đảm mỗi chunk không vượt quá kích thước quy định.
- **Code snippet (nếu custom):**
```python
from src import RecursiveChunker

chunker = RecursiveChunker(chunk_size=500)
chunks = chunker.chunk(document_text)
```

**Thành viên 3 - [Trần Anh Đăng]**
- **Loại chiến lược:** FixedSizeChunker
- **Mô tả & lý do chọn:** Thành viên này chọn chiến lược chia nhỏ theo kích thước cố định vì đây là phương pháp đơn giản, dễ kiểm soát và phù hợp để làm đường cơ sở khi so sánh với các chiến lược khác. Với bộ tài liệu chính sách Shopee, nhiều đoạn có nội dung dài và chứa nhiều mốc thời gian, điều kiện, phí và quy trình; việc chia theo kích thước cố định giúp đảm bảo mỗi chunk có độ dài tương đối ổn định để đưa vào embedding và truy xuất.
- **Tham số sử dụng:** `chunk_size=500`, `overlap=50`.
- **Kỳ vọng:** Overlap 50 ký tự giúp giảm mất ngữ cảnh ở ranh giới giữa hai chunk, ví dụ khi một điều kiện hoàn tiền hoặc thời hạn xử lý bị nằm giữa hai đoạn. Điểm mạnh của chiến lược này là dễ triển khai và dễ tái lập kết quả; điểm yếu là có thể cắt ngang câu hoặc cắt ngang một mục chính sách, làm giảm tính mạch lạc của một số chunk.
- **Code snippet:**

```python
from src import FixedSizeChunker

chunker = FixedSizeChunker(chunk_size=500, overlap=50)
chunks = chunker.chunk(document_text)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Bùi Lê Gia Huy | SentenceChunker | 8 / 10 | Giữ trọn vẹn câu ngữ nghĩa, không bị đứt đoạn giữa câu | Độ dài các chunk không đồng đều nếu gặp câu quá dài |
| Nguyễn Khánh Đô | RecursiveChunker | 8 / 10 | Phân đoạn theo cấu trúc văn bản rất tốt, gom được các gạch đầu dòng | Cần tinh chỉnh danh sách separators phù hợp với format tài liệu |
| Trần Anh Đăng | FixedSizeChunker | 8 / 10 | Độ dài chunk rất ổn định, dễ cấu hình và tái lập kết quả | Dễ cắt ngang câu hoặc ngắt đôi mốc thời gian ở ranh giới chunk |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Đối với bộ tài liệu quy định và chính sách TMĐT, **SentenceChunker** và **RecursiveChunker** là hai chiến lược hiệu quả nhất. Lý do là các quy định pháp lý đòi hỏi tính trọn vẹn của từng câu văn chứa mốc thời gian, điều kiện ngoại lệ và chế tài ràng buộc; việc giữ nguyên vẹn câu hoặc phân đoạn theo bullet points giúp embedding nắm bắt chính xác ngữ nghĩa nghiệp vụ và hạn chế tối đa hiện tượng ảo giác (hallucination) của Agent.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Metadata Filter | Câu trả lời chuẩn (Gold Answer) | Chunk / Tài liệu chứa thông tin |
|---|-----------------|-----------------|-------------------------------|--------------------------------|
| 1 | Người mua có thể gửi yêu cầu trả hàng/hoàn tiền trong thời hạn bao lâu đối với đơn hàng thông thường? | `None` | Đối với Shop thông thường hoặc Shop Yêu thích: trong vòng 3 ngày kể từ khi đơn hàng được cập nhật trạng thái "Giao hàng thành công" (với Shopee Mall là 15 ngày). | `return-refund-request-guide.md` / `return-refund-policy.md` |
| 2 | Nếu thanh toán bằng thẻ tín dụng hoặc thẻ ghi nợ thì tiền hoàn được gửi về đâu và mất bao lâu? | `None` | Tiền hoàn được gửi trực tiếp về đúng hạn mức thẻ tín dụng/ghi nợ đã dùng thanh toán, thời gian từ 7 đến 14 ngày làm việc. | `return-refund-policy.md` / `buyer-refund-timeline.md` |
| 3 | Khi đã nhận hàng nhưng hàng bị lỗi, video mở kiện hàng cần đáp ứng những yêu cầu nào? | `None` | Video quay rõ 6 mặt kiện hàng còn nguyên vẹn tem vận đơn, quá trình khui mở hộp liền mạch không cắt ghép, cùng hình ảnh chi tiết lỗi sản phẩm. | `return-refund-evidence-guide.md` / `return-refund-policy.md` |
| 4 | Nếu Người mua chọn hình thức Tự sắp xếp để trả hàng thì Shopee hỗ trợ phí trả hàng như thế nào? | `None` | Người mua thanh toán trước phí trả hàng. Shopee hỗ trợ hoàn lại phí trả hàng trong vòng 3 - 5 ngày làm việc (tối đa theo hạn mức chính sách) nếu khiếu nại hợp lệ. | `return-shipping-methods-fees.md` / `return-refund-policy.md` |
| 5 | Với tài liệu có audience=seller, Người bán nên làm gì khi nhận hàng hoàn nhưng sản phẩm bị hư hỏng hoặc không đúng sản phẩm của shop? | `{'audience': 'seller'}` | Người bán bấm nút "Khiếu nại sàn" trên Kênh Người Bán trong vòng 3 ngày (72 giờ) kể từ khi nhận hàng hoàn, cung cấp video quay 6 mặt kiện hàng và video mở kiện kiểm tra. | `seller-warranty-policy.md` / `seller-refund-dispute.md` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Điểm tương đồng / Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------------------------|
| 1 | Người mua có thể gửi yêu cầu trả hàng/hoàn tiền trong thời hạn bao lâu đối với đơn hàng thông thường? | **SentenceChunker** | Có (Top-1) | Score: 0.7579. SentenceChunker giữ trọn vẹn câu điều khoản 3 ngày đối với shop thông thường và 15 ngày với Mall. |
| 2 | Nếu thanh toán bằng thẻ tín dụng hoặc thẻ ghi nợ thì tiền hoàn được gửi về đâu và mất bao lâu? | **SentenceChunker** / **RecursiveChunker** | Có (Top-1) | Score: 0.4361. Truy xuất chính xác quy định hoàn tiền về đúng tài khoản thẻ gốc trong 7-14 ngày làm việc. |
| 3 | Khi đã nhận hàng nhưng hàng bị lỗi, video mở kiện hàng cần đáp ứng những yêu cầu nào? | **RecursiveChunker** | Có (Top-1) | Score: 0.6460. Phân đoạn danh sách gạch đầu dòng các tiêu chuẩn video 6 mặt và quá trình mở hộp nguyên vẹn. |
| 4 | Nếu Người mua chọn hình thức Tự sắp xếp để trả hàng thì Shopee hỗ trợ phí trả hàng như thế nào? | **SentenceChunker** | Có (Top-1) | Score: 0.6471. Trích xuất chính xác điều kiện người mua ứng trước và sàn hoàn phí trong vòng 3-5 ngày làm việc. |
| 5 | Với tài liệu có audience=seller, Người bán nên làm gì khi nhận hàng hoàn nhưng sản phẩm bị hư hỏng hoặc không đúng sản phẩm của shop? *(Filter: `audience='seller'`)* | **SentenceChunker** | Có (Top-1) | Score: 0.6051. Nhờ pre-filter `audience='seller'`, loại trừ hoàn toàn chính sách của người mua, lấy đúng quy trình khiếu nại hàng hoàn 72h. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata đóng vai trò quyết định ở **Câu hỏi #5** ("Với tài liệu có audience=seller, Người bán nên làm gì khi nhận hàng hoàn nhưng sản phẩm bị hư hỏng hoặc không đúng sản phẩm của shop?"). Nếu không lọc (`metadata_filter=None`), các tài liệu dành cho Người mua với tần suất từ khóa "trả hàng", "hư hỏng", "bồi thường" rất cao sẽ lấn át, khiến Agent trả lời hướng dẫn trả hàng của Người mua thay vì quy trình khiếu nại 72h của Người bán. Khi áp dụng `metadata_filter={"audience": "seller"}`, 100% kết quả truy xuất thuộc tài liệu của Người bán, giúp Agent hướng dẫn chính xác quy trình mở khiếu nại trên Kênh Người Bán.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Cơ chế Pre-filtering vs Post-filtering:** Bắt buộc phải lọc metadata trước khi tính similarity search; nếu lấy top-k rồi mới lọc thì k slot có thể bị chiếm sạch bởi tài liệu sai đối tượng (`seller` chiếm chỗ của `buyer`).
> 2. **Chấm điểm hai mức (Doc-level vs Content-level):** Việc kiểm tra `doc_id` lọt top-3 dễ gây ảo tưởng về độ chính xác; chỉ khi kiểm tra chuỗi nội dung thực tế chứa đáp án (Answer Presence) mới phản ánh đúng chất lượng của từng chiến lược chunking.
> 3. **Ảnh hưởng của Mock Embedder:** Mock băm MD5 không mã hóa được ngữ nghĩa; do đó chiến lược giữ nguyên câu hoàn chỉnh (`SentenceChunker`) hoặc phân đoạn tự nhiên (`RecursiveChunker`) là yếu tố bảo vệ ngữ cảnh tốt nhất khi retriever gặp nhiễu.

**Bài học rút ra khi so sánh trong nhóm (kèm Failure Case):**
> **Failure Case thực tế ở Câu hỏi #2:** Khi hỏi về danh mục sản phẩm không được đổi trả, hệ thống trả về top-1 là tài liệu khiếu nại của Người bán (`seller-refund-dispute#3`) thay vì tài liệu `forbidden-return-items`.
> - **Nguyên nhân:** Mock embedding băm chuỗi ký tự ngẫu nhiên kết hợp với việc các tài liệu chính sách có sự trùng lặp từ khóa chung ("đổi trả", "khiếu nại", "hoàn tiền") khiến vector score bị sai lệch.
> - **Đề xuất sửa:** (1) Bật embedding backend thực tế (Gemini hoặc OpenAI text-embedding-3-small); (2) Bổ sung thêm metadata filter chuyên biệt theo nghiệp vụ (`category='returns-policy'`) để cô lập không gian tìm kiếm.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn hóa ngay từ đầu cấu trúc tài liệu Markdown với các heading phân cấp rõ ràng (`#`, `##`, `###`), gắn metadata chi tiết hơn cho từng phần và tiến hành crawl với các nguồn tài liệu có cấu trúc bảng biểu hoàn chỉnh. Ngoài ra, nhóm sẽ ưu tiên thử nghiệm với embedding model thực tế ngay từ đầu để tinh chỉnh kích thước chunk sát với thực tế sản xuất.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 |
| Thuyết trình (Demo) | 0 / 5 |
| **Tổng phần nhóm** | **32 / 40** |
