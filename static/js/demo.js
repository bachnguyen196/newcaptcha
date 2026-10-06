document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('cv-capture-canvas');
    const context = canvas.getContext('2d');
    const slider = document.getElementById('cv-manual-slider');
    const sliderValue = document.getElementById('cv-slider-value');
    const loading = document.getElementById('cv-canvas-loading');
    const defenseToggle = document.getElementById('cv-visual-defense');
    const newChallengeButton = document.getElementById('cv-new-challenge');
    const solverButton = document.getElementById('cv-run-solver');
    const submitButton = document.getElementById('cv-submit-solution');
    const solverResult = document.getElementById('cv-solver-result');
    const verifyResult = document.getElementById('cv-verify-result');

    let challenge = null;
    let backgroundImage = null;
    let pieceImage = null;
    let match = null;
    let verified = false;

    slider.addEventListener('input', () => {
        sliderValue.value = `${slider.value} px`;
        drawChallenge();
        if (challenge && !verified) {
            submitButton.disabled = false;
            submitButton.textContent = 'Gửi tọa độ dự đoán';
        }
    });
    newChallengeButton.addEventListener('click', loadChallenge);
    defenseToggle.addEventListener('change', loadChallenge);
    solverButton.addEventListener('click', runSolver);
    submitButton.addEventListener('click', verifySolution);
    document.getElementById('cv-refresh-logs').addEventListener('click', refreshLogs);

    loadChallenge();

    async function loadChallenge() {
        setBusy(true);
        setSolverResult('running', 'Đang tạo thử thách', 'Yêu cầu ảnh CAPTCHA mới từ server...');
        verifyResult.textContent = '';
        verifyResult.style.color = '';
        submitButton.disabled = true;
        try {
            const defenseParam = defenseToggle.checked ? '1' : '0';
            const response = await fetch(`/api/demo/challenge?visual_defense=${defenseParam}`);
            const data = await response.json();
            if (!response.ok || data.status !== 'success') {
                throw new Error(data.message || `Không thể tạo challenge (HTTP ${response.status}).`);
            }

            challenge = data;
            [backgroundImage, pieceImage] = await Promise.all([
                loadImage(data.bg_image),
                loadImage(data.piece_image)
            ]);
            match = null;
            verified = false;
            submitButton.textContent = 'Gửi tọa độ dự đoán';
            slider.max = String(data.width - data.piece_size);
            slider.value = '0';
            slider.disabled = false;
            sliderValue.value = '0 px';
            drawChallenge();
            solverButton.disabled = false;
            setSolverResult(
                'ready',
                'Challenge sẵn sàng',
                'Ảnh canvas đã dựng. Tọa độ X mục tiêu không có trong payload API.'
            );
        } catch (error) {
            challenge = null;
            slider.disabled = true;
            solverButton.disabled = true;
            setSolverResult('error', 'Không thể tạo CAPTCHA', error.message || String(error));
        } finally {
            setBusy(false);
        }
    }

    async function runSolver() {
        if (!challenge || !backgroundImage || !pieceImage) return;
        solverButton.disabled = true;
        newChallengeButton.disabled = true;
        defenseToggle.disabled = true;
        slider.disabled = true;
        submitButton.disabled = true;
        verified = false;
        match = null;
        slider.value = '0';
        sliderValue.value = '0 px';
        drawChallenge();
        setSolverResult(
            'running',
            'OpenCV đang phân tích ảnh',
            'Chụp canvas PNG và tìm mẫu biên mảnh ghép trên vùng khuyết...'
        );

        try {
            const response = await fetch('/api/demo/cv-solve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Bot-Type': 'computer_vision'
                },
                body: JSON.stringify({
                    canvas_image: canvas.toDataURL('image/png'),
                    piece_image: challenge.piece_image,
                    y: challenge.y
                })
            });
            const result = await response.json();
            if (!response.ok || result.status !== 'success') {
                throw new Error(result.message || `Solver thất bại (HTTP ${response.status}).`);
            }

            match = { x: result.x, y: result.y };
            slider.value = String(result.x);
            sliderValue.value = `${result.x} px`;
            drawChallenge();
            if (challenge.visual_defense) {
                setSolverResult(
                    'error',
                    'Solver bị viền mồi đánh lừa',
                    `Template Matching chọn X=${result.x}, Y=${result.y} · điểm khớp ${result.score}. Hãy gửi tọa độ để thấy server kiểm tra độc lập và từ chối vị trí sai.`
                );
            } else {
                setSolverResult(
                    'success',
                    'Tìm thấy vùng khuyết',
                    `Template Matching dự đoán X=${result.x}, Y=${result.y} · điểm khớp ${result.score}. Biên xanh là vị trí solver tìm được.`
                );
            }
            verifyResult.textContent = 'Tọa độ đã được đưa vào thanh trượt; gửi lên server để kiểm chứng.';
            submitButton.disabled = false;
            refreshLogs();
        } catch (error) {
            if (challenge.visual_defense) {
                setSolverResult(
                    'error',
                    'Phòng thủ đã làm solver mẫu thất bại',
                    `Solver dò viền cyan cố định nên không nhận ra dấu hiệu màu ngẫu nhiên. Đây là giới hạn của thuật toán mẫu, không chứng minh CAPTCHA chống được mọi AI. Chi tiết: ${error.message || error}`
                );
            } else {
                setSolverResult('error', 'Không tìm được vị trí', error.message || String(error));
            }
        } finally {
            solverButton.disabled = false;
            newChallengeButton.disabled = false;
            defenseToggle.disabled = false;
            slider.disabled = !challenge;
        }
    }

    async function verifySolution() {
        if (!challenge) return;
        submitButton.disabled = true;
        verifyResult.textContent = verified
            ? 'Đang phát lại đúng challenge cũ...'
            : 'Server đang xác minh challenge và tọa độ dự đoán...';
        try {
            const response = await fetch('/captcha/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Bot-Type': 'computer_vision'
                },
                body: JSON.stringify({
                    challenge_id: challenge.challenge_id,
                    user_x: Number(slider.value)
                })
            });
            const result = await response.json();
            slider.disabled = true;
            if (response.ok && result.valid) {
                verified = true;
                verifyResult.textContent = `HTTP 200 · CAPTCHA được chấp nhận. Sai số dự đoán nằm trong dung sai server (±5 px). Bấm lại để thử Replay Attack.`;
                submitButton.disabled = false;
                submitButton.textContent = 'Thử phát lại challenge';
            } else if (result.reason === 'REPLAY_ATTACK') {
                verifyResult.textContent = 'HTTP 400 · REPLAY_ATTACK bị chặn: challenge chỉ được dùng một lần.';
                verifyResult.style.color = '#fca5a5';
                submitButton.disabled = true;
                refreshLogs();
            } else {
                verifyResult.textContent = `HTTP ${response.status} · Server từ chối (${result.reason || 'UNKNOWN'}). Tạo challenge mới để thử lại.`;
                verifyResult.style.color = '#fca5a5';
                submitButton.disabled = true;
            }
            refreshLogs();
        } catch (error) {
            slider.disabled = true;
            submitButton.disabled = true;
            verifyResult.textContent = `Không rõ server đã nhận request hay chưa: ${error.message || error}. Tạo challenge mới trước khi thử lại.`;
            verifyResult.style.color = '#fca5a5';
        }
    }

    function drawChallenge() {
        if (!backgroundImage || !pieceImage || !challenge) return;
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(backgroundImage, 0, 0, canvas.width, canvas.height);
        if (match) {
            context.save();
            context.strokeStyle = '#22c55e';
            context.lineWidth = 2;
            context.setLineDash([5, 3]);
            context.strokeRect(match.x + 1, match.y + 1, challenge.piece_size - 2, challenge.piece_size - 2);
            context.restore();
        }
        context.drawImage(pieceImage, Number(slider.value), challenge.y);
    }

    function loadImage(src) {
        return new Promise((resolve, reject) => {
            const image = new Image();
            image.onload = () => resolve(image);
            image.onerror = () => reject(new Error('Không tải được ảnh CAPTCHA.'));
            image.src = src;
        });
    }

    function setBusy(isBusy) {
        loading.hidden = !isBusy;
        newChallengeButton.disabled = isBusy;
        defenseToggle.disabled = isBusy;
        solverButton.disabled = isBusy || !challenge;
    }

    function setSolverResult(state, title, message) {
        solverResult.dataset.state = state;
        solverResult.replaceChildren();
        const indicator = document.createElement('span');
        indicator.className = 'result-indicator';
        const text = document.createElement('div');
        const heading = document.createElement('strong');
        heading.textContent = title;
        const detail = document.createElement('p');
        detail.textContent = message;
        text.append(heading, detail);
        solverResult.append(indicator, text);
    }

    async function refreshLogs() {
        try {
            const response = await fetch('/api/logs');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const result = await response.json();
            if (result.status !== 'success') throw new Error('API không trả về log.');
            const tbody = document.getElementById('cv-logs');
            tbody.replaceChildren();
            if (!result.logs.length) {
                const row = tbody.insertRow();
                const cell = row.insertCell();
                cell.colSpan = 6;
                cell.className = 'cv-empty';
                cell.textContent = 'Chưa có log trong phiên này.';
                return;
            }
            result.logs.slice(0, 12).forEach(log => {
                const row = tbody.insertRow();
                [
                    log.timestamp,
                    log.bot_type,
                    log.endpoint,
                    log.captcha_result,
                    log.status_code,
                    log.action
                ].forEach(value => {
                    const cell = row.insertCell();
                    cell.textContent = value ?? '';
                });
            });
        } catch (error) {
            console.error('Không thể làm mới audit log:', error);
        }
    }
});
