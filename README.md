# 🛡️ Captcha Security Lab - Slider Puzzle CAPTCHA & Bot Defense

> **Đồ án Sinh viên Chuyên ngành An toàn Thông tin**  
> **Đề tài:** *"Tìm hiểu CAPTCHA và các phương pháp tạo CAPTCHA trong ứng dụng Web – Xây dựng website tích hợp CAPTCHA, mô phỏng hành vi tự động/bot trong môi trường kiểm thử và triển khai các biện pháp tăng cường bảo vệ."*

---

## 📌 1. Giới Thiệu & Mục Tiêu Đề Tài

Hệ thống được thiết kế để giải quyết bài toán phòng chống hành vi tự động hóa độc hại (credential stuffing, brute-force, web scraping) trên ứng dụng Web bằng cách xây dựng **cơ chế phòng thủ đa lớp (Defense-in-depth)**:
1. **Lớp 1: Slider Puzzle CAPTCHA (Tự phát triển)** – Đòi hỏi nhận thức thị giác và thao tác kéo thả thực tế từ con người.
2. **Lớp 2: Kiểm soát Zero-Trust & Single-Use Token** – Chống tấn công Replay Attack và giới hạn thời gian sống (TTL = 120s).
3. **Lớp 3: Thuật toán Sliding Window Rate Limiting** – Chặn đứng tấn công vét cạn / flooding dồn dập (giới hạn 10 requests / 10s / IP).
4. **Lớp 4: Nhật ký An ninh & Dashboard Forensics** – Phân loại và giám sát lưu lượng thời gian thực giữa Human, HTTP Bot và Selenium Bot.

---

## 🏗️ 2. Kiến Trúc Hệ Thống & Cấu Trúc Thư Mục

```
/captcha-security-lab
  ├── app.py                      # Ứng dụng Flask trung tâm & Điều phối API
  ├── config.py                   # Cấu hình tập trung (TTL, Tolerance, Rate Limit)
  ├── requirements.txt            # Thư viện phụ thuộc chuẩn
  ├── run_tests.py                # Script chạy toàn bộ 20 bài kiểm thử tự động
  ├── README.md                   # Tài liệu hướng dẫn & Kịch bản demo
  │
  ├── database/                   # Quản lý cơ sở dữ liệu SQLite
  │   ├── schema.sql              # Định nghĩa bảng users, challenges, security_logs
  │   └── db.py                   # Hàm thao tác dữ liệu & CRUD bảo mật
  │
  ├── captcha/                    # Lõi cơ chế Slider Puzzle CAPTCHA
  │   ├── generator.py            # Thuật toán sinh ảnh nền động & cắt mảnh Jigsaw (Pillow)
  │   └── validator.py            # Xác thực tọa độ, Replay Attack & TTL 120s
  │
  ├── security/                   # Các lớp phòng thủ bổ sung
  │   ├── rate_limiter.py         # Thuật toán Sliding Window Rate Limiting (HTTP 429)
  │   └── security_logger.py      # Phân tích thống kê đối chiếu A/B & quản lý Log
  │
  ├── bot/                        # Mô phỏng tác tử tự động (CHỈ CHẠY LOCALHOST)
  │   ├── http_bot.py             # Bot tấn công trực tiếp API tầng HTTP (Requests)
  │   └── selenium_bot.py         # Bot điều khiển trình duyệt tự động (Selenium)
  │
  ├── static/                     # Giao diện Dark Mode & Component kéo thả
  │   ├── css/
  │   │   ├── style.css           # Design system Cyber-security hiện đại
  │   │   └── captcha.css         # Styling thanh trượt, mảnh ghép và hiệu ứng rung lắc
  │   └── js/
  │       ├── main.js             # Tiện ích quản lý giao diện
  │       └── slider-captcha.js   # Bộ điều khiển kéo thả hỗ trợ Mouse & Touch
  │
  ├── templates/                  # Giao diện HTML Jinja2
  │   ├── base.html               # Khung sườn chung & Navbar trạng thái
  │   ├── index.html              # Trang tổng quan đề tài & mô hình 3 tác tử
  │   ├── login.html              # Form đăng nhập tích hợp Slider CAPTCHA
  │   ├── register.html           # Form đăng ký tích hợp Slider CAPTCHA
  │   └── dashboard.html          # Bảng điều khiển an ninh & đối chiếu A/B
  │
  └── tests/                      # Bộ kiểm thử tự động (Unit Tests)
      ├── test_captcha_generator.py
      ├── test_captcha_validator.py
      ├── test_rate_limiter.py
      └── test_authentication_flow.py
```

---

## 🔒 3. Các Cơ Chế Bảo Mật Cốt Lõi

### A. Thuật toán sinh Slider Puzzle CAPTCHA (`captcha/generator.py`)
- **Ảnh nền Procedural:** Sinh ngẫu nhiên dải màu Gradient, các khối cầu phát sáng và lưới tọa độ bằng thư viện `Pillow`, đảm bảo câu đố luôn mới lạ mà không cần phụ thuộc mạng Internet.
- **Mặt nạ Jigsaw Mask:** Cắt mảnh ghép kích thước `48x48 px` với 2 chấu lồi và 1 chấu lõm. Thêm viền trắng phát sáng cho mảnh ghép và tạo vùng khuyết màu sẫm viền cyan trên ảnh nền.
- **Bảo mật Zero-Trust:** Tọa độ mục tiêu `target_x` chỉ được lưu trong SQLite Database của server, **tuyệt đối không bao giờ gửi về client**.

### B. Kiểm soát xác thực Server-Side (`captcha/validator.py`)
1. **Chống Replay Attack:** Ngay khi nhận được `challenge_id`, server lập tức cập nhật `used = 1`. Nếu kẻ tấn công phát lại (replay) cùng một request, hệ thống sẽ trả về lỗi `REPLAY_ATTACK`.
2. **Kiểm tra thời gian sống (TTL = 120s):** Nếu người dùng giữ câu đố quá 2 phút, challenge bị hủy với lỗi `EXPIRED`.
3. **Độ sai số dung sai (Tolerance = 5px):** Cho phép sai lệch tự nhiên của tay người `abs(user_x - target_x) <= 5`.

### C. Thuật toán Sliding Window Rate Limiting (`security/rate_limiter.py`)
- Lưu vết dấu thời gian (timestamps) của từng IP trong khoảng trượt 10 giây.
- Cho phép tối đa 10 requests / 10s. Nếu vượt quá, server trả về mã **HTTP 429 Too Many Requests** kèm tiêu đề `Retry-After`.

---

## 🚀 4. Hướng Dẫn Cài Đặt & Khởi Động

### Yêu cầu môi trường:
- Python 3.10 trở lên.
- Trình duyệt Chrome hoặc Microsoft Edge (để chạy Selenium Bot).

### Bước 1: Cài đặt thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### Bước 2: Khởi động Web Server Lab
```bash
python app.py
```
> Server sẽ chạy tại địa chỉ: `http://127.0.0.1:5000`  
> Tài khoản thử nghiệm mặc định có sẵn: `admin` / `password123`

### Bước 3: Chạy bộ kiểm thử tự động (20 Test Cases)
Mở một cửa sổ dòng lệnh khác và chạy:
```bash
python run_tests.py
```
Toàn bộ 20 bài kiểm thử (Sinh CAPTCHA, Xác thực tọa độ, Replay Attack, TTL Expired, Rate Limiter, Luồng Đăng nhập) sẽ được thực thi và in báo cáo chi tiết.

---

## 🎬 5. Kịch Bản Trình Diễn Demo Chi Tiết (4 Kịch Bản)

### 🧪 Phòng Demo Thực Hành
Truy cập `http://127.0.0.1:5000/demo` để chạy thử nghiệm nhận dạng ảnh bằng OpenCV:
1. Trang yêu cầu challenge mới và vẽ ảnh nền cùng mảnh ghép lên canvas. API không gửi `target_x`; chỉ tọa độ Y công khai được dùng để giới hạn hàng tìm kiếm.
2. Bấm **Chạy OpenCV Solver**. Trang chụp canvas thành PNG; OpenCV phân đoạn viền cyan trong HSV và dùng Template Matching với đường biên alpha của mảnh ghép để dự đoán X.
3. Kết quả dự đoán được đặt lên thanh trượt và đánh dấu bằng khung xanh. Bấm **Gửi tọa độ dự đoán** để server kiểm tra; bấm lại để thấy `REPLAY_ATTACK` bị chặn. Có thể kéo thanh trượt thủ công để so sánh.
4. Audit log ghi nhận lần chạy solver và kết quả xác thực dưới tác tử `cv_bot`.
5. Bật **Bật phòng thủ ảnh** để tạo biến thể lab có màu viền thay đổi, nhiễu ngẫu nhiên và các viền mồi. Solver mẫu có thể chọn nhầm viền mồi; gửi tọa độ để thấy server vẫn xác minh đáp án. Đây là bài tập minh họa chống một solver màu cố định, không phải tuyên bố CAPTCHA đã chống được AI tổng quát.

Để áp dụng biến thể phòng thủ cho challenge CAPTCHA thông thường, đặt biến môi trường `CAPTCHA_VISUAL_DEFENSE=true` trước khi chạy ứng dụng. Mặc định là `false` để giữ chế độ baseline. Biến thể này chỉ gây khó cho solver màu cố định trong lab; không thay thế rate limit, xác minh server-side, CAPTCHA thích ứng hay các biện pháp chống bot chuyên dụng.

Solver chỉ nhận ảnh canvas, ảnh mảnh ghép và Y công khai; không đọc cơ sở dữ liệu hay `target_x`. Thử nghiệm chỉ chạy trên CAPTCHA của lab local. Cần cài dependency mới bằng `pip install -r requirements.txt`.

### 🧩 Chuỗi sự cố token và SQLi (mô phỏng giao diện)
Trong cùng trang `/demo`, phần **“Chuỗi sự cố CAPTCHA và SQLi — mô phỏng an toàn”** minh họa bốn giai đoạn của kịch bản thuyết trình:
1. Chọn **Backend có lỗi** hoặc **Backend đã phòng thủ**, rồi so sánh hai kết quả gửi cùng một token giả.
2. Nhập chuỗi mẫu và xem bộ phân loại ký tự chạy cục bộ trên trình duyệt.
3. Ở chế độ lỗi, giao diện hiển thị một số chuỗi `SIM-NOT-A-REAL-TOKEN` viết sẵn để minh họa dữ liệu giả định bị lộ.
4. Xem phép tính tác động giả định; giao diện không gửi request hàng loạt.

Đây là **mô phỏng UI**, không phải một backend dễ khai thác: không có SQL injection thật, không có truy vấn dữ liệu token, không xác thực bằng token mô phỏng, không fuzzing HTTP/time-based và không tạo request đăng nhập hàng loạt. Token mẫu vô hiệu, đầu vào chỉ được xử lý trong JavaScript ở trình duyệt. CAPTCHA thật và kiểm tra replay hiện có của ứng dụng vẫn giữ chế độ phòng thủ.

Hội đồng chấm thi có thể trực tiếp quan sát hiệu quả bảo mật qua 4 kịch bản sau:

### 🌟 Kịch bản 1: Trải nghiệm Người Dùng Thật (Human User)
1. Mở trình duyệt truy cập: `http://127.0.0.1:5000/login`.
2. Nhập thông tin: `admin` / `password123`.
3. Kéo thanh trượt slider từ trái sang phải sao cho mảnh ghép khớp chính xác vào vị trí vùng khuyết.
4. Nhấn **Đăng Nhập** &rarr; Đăng nhập thành công và được chuyển hướng tới trang **Dashboard**.
5. Trong bảng nhật ký Dashboard, dòng log xuất hiện:
   - `Tác tử`: **👤 Human**
   - `Kết quả CAPTCHA`: **PASS**
   - `Mã HTTP`: **200**

---

### 💡 TÍNH NĂNG MỚI: Kích hoạt Bot trực tiếp từ Web Dashboard (GUI 1-Click)
> **Bạn không cần phải mở terminal gõ lệnh nữa!**  
> Ngay trên giao diện Dashboard (`http://127.0.0.1:5000/dashboard`), chúng tôi đã tích hợp sẵn **Khu Vực Thử Nghiệm Tấn Công Bot Trực Tiếp**:
> - **🚀 Nút "Bắt Đầu Tấn Công HTTP Bot"**: Tùy chỉnh số request (5 - 20) và tốc độ gửi, xem stream kết quả trên màn hình Terminal Console đen phong cách SOC.
> - **🤖 Nút "Bắt Đầu Tấn Công Selenium Bot"**: Tùy chọn xem cửa sổ Chrome/Edge tự động bật lên gõ phím trực quan hoặc chạy ẩn (Headless).
> - **Bảng thống kê và Security Audit Logs tự động cập nhật ngay lập tức** sau khi bot chạy xong!

---

### 🤖 Kịch bản 2: HTTP Bot tấn công dò mật khẩu (Brute-Force & Credential Stuffing)
Kịch bản này chứng minh sự khác biệt rõ rệt khi bật và tắt CAPTCHA (A/B Testing).

#### Bước 2.1: Khi CAPTCHA đang BẬT (Mặc định)
Chạy HTTP Bot thử vét cạn danh sách mật khẩu phổ biến:
```bash
python bot/http_bot.py --requests 10 --delay 0.3
```
- **Kết quả:** Toàn bộ 10 requests của bot đều bị server từ chối với mã **HTTP 400** (`[BLOCKED BY CAPTCHA]`).
- **Lý do:** Bot dùng thư viện `requests` gửi dữ liệu thô, không có mắt nhìn để giải câu đố hình học.
- **Trên Dashboard:** Cột *Hiệu quả bảo vệ* hiển thị **Tỉ lệ chặn 100%**.

#### Bước 2.2: Khi CAPTCHA được TẮT (Mô phỏng website không có bảo vệ)
1. Trên giao diện Dashboard, bấm nút: **🔴 Chuyển sang TẮT CAPTCHA**.
2. Chạy lại script HTTP Bot:
   ```bash
   python bot/http_bot.py --requests 10 --delay 0.3
   ```
- **Kết quả:** Bot dễ dàng thử từng mật khẩu, tìm ra mật khẩu đúng `password123` và đăng nhập thành công với mã **HTTP 200 OK** (`[SUCCESS - BYPASSED]`).
- **Ý nghĩa khoa học:** Minh chứng trực quan sự nguy hiểm khi thiếu lớp xác thực thị giác CAPTCHA.

---

### 🕷️ Kịch bản 3: Selenium Headless Bot thao tác DOM
Kịch bản này chứng minh bot có thể tương tác với form (gõ chữ), nhưng buộc phải dừng lại trước rào cản CAPTCHA.

Chạy bot Selenium:
```bash
python bot/selenium_bot.py
```
*(Nếu muốn chạy ẩn nền không mở cửa sổ, thêm cờ `--headless`)*:
```bash
python bot/selenium_bot.py --headless
```
- **Diễn biến:**
  1. Trình duyệt tự động mở lên và truy cập trang đăng nhập.
  2. Bot tự động tìm trường `#username` và gõ `admin`.
  3. Bot tự động tìm trường `#password` và gõ `password123`.
  4. Bot quét mã DOM trang web và phát hiện phần tử `#captcha-container`.
  5. Bot lập tức xuất thông báo cảnh báo và dừng lại:
     ```
     🛑 [ALERT] CAPTCHA detected. Automation stopped.
     [i] Chi tiết: Bot phát hiện rào cản Slider CAPTCHA và không thể tự giải quyết.
     ```
- **Ý nghĩa khoa học:** CAPTCHA vô hiệu hóa các công cụ tự động hóa giao diện trình duyệt.

---

### 🛑 Kịch bản 4: Tấn công dồn dập (Flooding) & Kích hoạt Rate Limiting
Kịch bản này chứng minh khả năng bảo vệ của lớp Rate Limiting khi bị tấn công tần suất cao.

Chạy bot gửi liên tục 15 requests không có độ trễ:
```bash
python bot/http_bot.py --requests 15 --delay 0.05
```
- **Kết quả:**
  - 10 requests đầu tiên gửi đi bình thường.
  - Từ request thứ 11 trở đi, server lập tức kích hoạt bộ lọc và trả về mã **HTTP 429 Too Many Requests** (`[RATE LIMITED (429)]`).
- **Trên Dashboard:** Mục `Rate Limiter Kích Hoạt` tăng lên, ghi nhận các hành vi vi phạm tần suất truy cập.

---

## ⚖️ 6. Ràng Buộc Đạo Đức & Quy Chuẩn An Toàn

1. **Localhost Restriction:** Cả `http_bot.py` và `selenium_bot.py` đều được tích hợp hàm `verify_safe_target()`. Nếu người dùng cố tình truyền vào bất kỳ địa chỉ nào khác ngoài `127.0.0.1` hoặc `localhost`, chương trình sẽ lập tức báo lỗi vi phạm đạo đức và tự động kết thúc.
2. **Academic Purpose:** Không sử dụng kỹ thuật che giấu (stealth), không dùng proxy xoay vòng, không cố tình bẻ khóa CAPTCHA của bên thứ ba. Hệ thống thuần túy là môi trường phòng thí nghiệm học thuật phục vụ đồ án an toàn thông tin.

---

## 👨‍💻 Thông Tin Tác Giả & Đồ Án
- **Chuyên ngành:** An toàn Thông tin (Năm 4)
- **Công nghệ chính:** Python, Flask, Pillow, SQLite, Vanilla JavaScript, HTML5/CSS3, Selenium WebDriver.
