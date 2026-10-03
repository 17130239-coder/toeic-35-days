# 📚 Kho Luyện Từ Vựng 35 Ngày & Đấu Trường Wayground (Quizizz Clone)

Dự án này đã trích xuất toàn bộ dữ liệu từ tệp `data.html` của khóa học TOEIC 35 Ngày, xây dựng 2 ứng dụng web hiện đại phục vụ việc học tập từ vựng và ôn tập qua game đấu Quizizz:

---

## 🚀 Trải Nghiệm Trực Tiếp (Live Deployment)

- 📚 **Website 1 (Học từ vựng 35 Ngày):**  
  👉 **[https://17130239-coder.github.io/toeic-35-days/](https://17130239-coder.github.io/toeic-35-days/)**

- 🎮 **Website 2 (Đấu trường ôn tập Wayground):**  
  👉 **[https://17130239-coder.github.io/toeic-35-days/wayground.html](https://17130239-coder.github.io/toeic-35-days/wayground.html)**

---

## 💻 Chạy Tại Máy Cục Bộ (Localhost)
Nếu muốn chạy trực tiếp trên máy:
```bash
python3 server.py 3000
```
Truy cập: `http://localhost:3000/` hoặc `http://localhost:3000/wayground.html`

---

## 📦 Dữ Liệu Đã Trích Xuất (Extracted Data)

1. **`days_data.json`**:
   - Bao gồm toàn bộ **36 ngày học (Day 0 đến Day 35)**.
   - Mỗi Day gồm:
     - Tiêu đề, hạn nộp (`Due date`), ngày đăng bài.
     - Lời dặn dò, lịch trả bài (`[DẶN DÒ]`).
     - Danh sách từ vựng chi tiết: Từ tiếng Anh, phiên âm IPA, từ loại, định nghĩa tiếng Việt, các từ đồng nghĩa (synonyms), mẫu câu ngữ cảnh/collocations, câu ví dụ song ngữ Anh - Việt.
     - Bài tập A: Viết câu hoàn chỉnh / điền từ vào chỗ trống (`___[1]`, `___[2]`) kèm bản dịch tiếng Việt và ngân hàng từ (`word bank`).
     - Thông tin Wayground: Link `https://wayground.com/join?gc=...`, mã PIN game, danh sách các Day được ôn tập trong game đó, hạn chót và cơ cấu giải thưởng (`30k top 3`).
     - Tệp đính kèm Google Drive: các file audio MP3, hình ảnh infographic PNG, video bài giảng MP4.
     - Nội dung HTML gốc của bài đăng lớp học.

2. **`all_vocabulary.json`**:
   - Danh bạ phẳng gồm **193 từ vựng cốt lõi** xuyên suốt 35 ngày để phục vụ tìm kiếm nhanh (Ctrl+K) và tra cứu tức thì.

3. **`wayground_quizzes.json`**:
   - Trọn bộ **26 trận đấu Wayground chính thức** với **520 câu hỏi trắc nghiệm** đa dạng:
     - Nghĩa của từ (Tiếng Anh -> Tiếng Việt)
     - Chọn từ tiếng Anh (Tiếng Việt -> Tiếng Anh)
     - Nhận diện từ đồng nghĩa (Synonyms)
     - Điền từ vào câu ngữ cảnh (Sentence Context)
     - Thử thách nghe phát âm (🎧 Audio Listening Challenge)

---

## 🌟 Tính Năng Chi Tiết Của Từng Website

### 1. Website 1: 35-Days Vocab Master (`index.html`)
- **Lộ trình học theo tuần**: Bộ lọc thông minh theo Tuần 1 (Day 0-7), Tuần 2 (Day 8-14), ..., Tuần 5 (Day 29-35).
- **Phát âm chuẩn bản xứ**: Tích hợp Web Speech API, bấm loa để nghe phát âm ngay từng từ vựng và câu ví dụ mà không cần tải file ngoài.
- **Thẻ ghi nhớ Flashcards 3D**: Lật thẻ 3D mượt mà, hỗ trợ phím tắt bàn phím (Phím `Cách` để lật, phím mũi tên `Trái`/`Phải` để chuyển từ).
- **Luyện tập Điền câu (Bài tập A)**: Hiển thị câu hỏi điền từ với đầy đủ ngân hàng từ và gợi ý dịch câu tiếng Việt.
- **Tra cứu từ điển toàn khóa (Ctrl+K)**: Tìm kiếm tức thì theo từ tiếng Anh, phiên âm hoặc nghĩa tiếng Việt.
- **Giao diện Dark/Light mode**: Tự động nhận diện hoặc chuyển đổi dễ dàng bằng nút bấm.
- **Nút chuyển đổi một chạm sang Wayground**: Trên mỗi Day đều có nút mở thẳng trận đấu Wayground tương ứng.

### 2. Website 2: Wayground Quiz Arena (`wayground.html`)
- **Giao diện chuẩn phong cách Quizizz / Wayground**: Tông màu tím vũ trụ (cosmic purple), âm thanh 8-bit sống động tự tổng hợp bằng Web Audio API (không phụ thuộc file ngoài).
- **Nhập mã PIN Game Code hoặc chọn nhanh**: Hỗ trợ nhập mã PIN 8 số hoặc mở ngăn kéo danh sách 26 mã game chính thức để chơi ngay.
- **Tùy biến người chơi**: Nhập biệt danh, chọn 12 avatar ngộ nghĩnh (👾, 🤖, 🐱, 🦊, 🐼, 🦄,...).
- **Đếm ngược kịch tính**: 3... 2... 1... Bắt đầu!
- **Cơ chế thi đấu thời gian thực**:
  - Đồng hồ đếm ngược từng câu (20s - 30s) với thanh thời gian đổi màu sinh động.
  - Chuỗi liên tiếp (Streak Flame Multiplier): `STREAK x2 🔥`, `STREAK x3 🔥🔥`, `ON FIRE! x4 ⚡`.
  - Pháo hoa giấy (Confetti) khi đạt streak cao và khi chiến thắng.
- **Vật phẩm trợ giúp (Power-ups)**:
  - ❄️ *Freeze Time*: Đóng băng đồng hồ thêm 10 giây.
  - ⚡ *50:50*: Loại bỏ ngay 2 phương án sai.
  - 🌟 *2x Points*: Nhân đôi điểm số đạt được ở câu hiện tại.
- **Bảng xếp hạng trực tiếp (Simulated Live Leaderboard)**: Cạnh tranh điểm số theo thời gian thực cùng các bạn học trong lớp (Hoàng Nam, Minh Anh, Thu Trang, Quốc Bảo,...).
- **Lễ vinh danh bục chiến thắng (Podium 1st, 2nd, 3rd)**: Bục nhận giải Top 1-2-3 rực rỡ kèm thống kê độ chính xác (%), chuỗi cao nhất, điểm tổng.
- **Xem lại chi tiết bài làm**: Bảng tổng kết từng câu đã trả lời đúng/sai, kèm giải thích cặn kẽ và phiên âm.

---

## 🎯 Bảng Đối Chiếu 26 Mã PIN Wayground & Ngày Ôn Tập

| Mã PIN (Game Code) | Nội Dung Ôn Tập | Ngày Ôn Tập |
| :--- | :--- | :--- |
| **66560969** | GAME QUIZIZZ ÔN TỪ VỰNG [DAY 0] | Day 0 |
| **61030441** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [0 + 1] | Day 0, 1 |
| **32456745** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [0 + 1 + 2] | Day 0, 1, 2 |
| **47759401** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [1 + 2 + 3] | Day 1, 2, 3 |
| **42230569** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [1 + 2 + 3 + 4] | Day 1, 2, 3, 4 |
| **37393065** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [3 + 4 + 5] | Day 3, 4, 5 |
| **27497129** | GAME QUIZIZZ [TÍNH TỪ ĐUÔI ING & ED] | Day 6, 7 |
| **28021417** | GAME QUIZIZZ [TÍNH TỪ ĐUÔI ING & ED - BẢN 2] | Day 6, 7 |
| **20234665** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [8 + 9] | Day 8, 9 |
| **34783657** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [10 + 11] | Day 10, 11 |
| **53367017** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [12 + 13] | Day 12, 13 |
| **21941993** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [14 + 15] | Day 14, 15 |
| **59338009** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [16 + 17] | Day 16, 17 |
| **62975257** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [18 + 19] | Day 18, 19 |
| **00847129** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [0 + 20 + 21] | Day 0, 20, 21 |
| **26766233** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [1 + 22 + 23] | Day 1, 22, 23 |
| **19032985** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [2 + 24 + 25] | Day 2, 24, 25 |
| **59837913** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [3 + 26 + 27] | Day 3, 26, 27 |
| **44371417** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [4 + 5 + 28] | Day 4, 5, 28 |
| **38997465** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [6 + 7 + 29] | Day 6, 7, 29 |
| **14355929** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [8 + 9 + 30] | Day 8, 9, 30 |
| **19767685** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [10 + 11 + 31] | Day 10, 11, 31 |
| **29743557** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [12 + 13 + 32] | Day 12, 13, 32 |
| **25348773** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [14 + 15 + 33] | Day 14, 15, 33 |
| **48351909** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [16 + 17 + 34] | Day 16, 17, 34 |
| **14273189** | GAME QUIZIZZ ÔN TỪ VỰNG DAY [18 + 19 + 35] | Day 18, 19, 35 |

---

## 🛠️ Lệnh Khởi Động Lại Server (Nếu cần)

```bash
cd /Users/andynguyen/workspace/35-days
python3 server.py 3000
```
