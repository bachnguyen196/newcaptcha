document.addEventListener('DOMContentLoaded', () => {
    const mode = document.getElementById('scenario-mode');
    const replayResult = document.getElementById('scenario-replay-result');
    const messageInput = document.getElementById('scenario-message');
    const fuzzResult = document.getElementById('scenario-fuzz-result');
    const tokenResult = document.getElementById('scenario-token-result');
    const impactResult = document.getElementById('scenario-impact-result');
    const demoTokens = [
        'SIM-NOT-A-REAL-TOKEN-01',
        'SIM-NOT-A-REAL-TOKEN-02',
        'SIM-NOT-A-REAL-TOKEN-03'
    ];

    document.getElementById('scenario-replay').addEventListener('click', () => {
        if (mode.value === 'vulnerable') {
            replayResult.textContent = 'Request 1: HTTP 200 (mô phỏng) · Request 2: HTTP 200 (mô phỏng). Lỗi giả lập: token không bị thu hồi sau lần xác thực đầu.';
        } else {
            replayResult.textContent = 'Request 1: HTTP 200 (mô phỏng) · Request 2: bị từ chối REPLAY_ATTACK. Token đã được đánh dấu dùng một lần.';
        }
    });

    document.getElementById('scenario-fuzz').addEventListener('click', () => {
        const containsSpecialSyntax = /['"\\]|--|\/\*|\b(union|select|sleep)\b|\bor\b\s+\d+\s*=\s*\d+/i
            .test(messageInput.value);
        if (mode.value === 'vulnerable' && containsSpecialSyntax) {
            fuzzResult.textContent = 'Kết quả giả lập: phát hiện dấu hiệu đầu vào có cú pháp đáng ngờ; minh họa lỗi phản hồi DB. Không có truy vấn hoặc lỗi DB thực nào được tạo.';
        } else if (containsSpecialSyntax) {
            fuzzResult.textContent = 'Kết quả giả lập: đầu vào được xử lý như dữ liệu bằng truy vấn tham số hóa; không có truy vấn SQL nào được thực thi.';
        } else {
            fuzzResult.textContent = 'Kết quả giả lập: không phát hiện mẫu ký tự trong chuỗi này. Đây không phải kiểm tra bảo mật thực.';
        }
    });

    document.getElementById('scenario-exfiltrate').addEventListener('click', () => {
        if (mode.value === 'vulnerable') {
            tokenResult.textContent = `Dữ liệu giả định (không hợp lệ): ${demoTokens.join(', ')}. Đây là chuỗi tĩnh minh họa, không lấy từ cơ sở dữ liệu.`;
        } else {
            tokenResult.textContent = 'Không có dữ liệu token nào được trả về trong chế độ phòng thủ. Truy vấn tham số hóa và giới hạn quyền DB giúp ngăn đọc ngoài mục đích.';
        }
    });

    document.getElementById('scenario-impact').addEventListener('click', () => {
        if (mode.value === 'vulnerable') {
            impactResult.textContent = `Tác động minh họa: ${demoTokens.length} mã giả × 2 lần gửi = ${demoTokens.length * 2} kết quả chấp nhận giả định. Không request nào được gửi và đây không phải kết quả xác thực thật.`;
        } else {
            impactResult.textContent = 'Tác động minh họa: phát lại bị chặn sau lần dùng đầu; đầu vào không truy vấn DB. Không có request đăng nhập hay tác vụ hàng loạt nào được chạy.';
        }
    });
});
