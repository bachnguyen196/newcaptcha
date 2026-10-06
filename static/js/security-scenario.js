document.addEventListener('DOMContentLoaded', () => {
    const mode = document.getElementById('scenario-mode');
    const progressFill = document.getElementById('scenario-progress-fill');
    const steps = [...document.querySelectorAll('.scenario-step')];
    const panels = [...document.querySelectorAll('.scenario-stage-panel')];
    const replayResult = document.getElementById('scenario-replay-result');
    const fuzzResult = document.getElementById('scenario-fuzz-result');
    const fuzzStream = document.getElementById('scenario-fuzz-stream');
    const timer = document.getElementById('scenario-timer');
    const timerNote = document.getElementById('scenario-timer-note');
    const tokenResult = document.getElementById('scenario-token-result');
    const counter = document.getElementById('scenario-counter');
    const counterLabel = document.querySelector('.scenario-counter span');
    const impactResult = document.getElementById('scenario-impact-result');
    const webNotice = document.getElementById('scenario-web-notice');
    const feedbackName = document.getElementById('scenario-name');
    const feedbackMessage = document.getElementById('scenario-message');
    const victimPanel = document.querySelector('.scenario-victim');
    const dbRows = document.getElementById('scenario-db-rows');
    const dbWarning = document.getElementById('scenario-db-warning');
    const dbLock = document.getElementById('scenario-db-lock');
    const systemAlert = document.getElementById('scenario-system-alert');
    const dbCard = document.querySelector('.scenario-db-card');
    const codeHighlight = document.querySelector('.scenario-code-highlight');
    const fuzzTimerPanel = document.querySelector('.scenario-timer');
    const matrixPanel = document.querySelector('.scenario-matrix');
    const attackPanel = document.querySelector('.scenario-attacker');
    const fakeTokens = [
        'SIM-NOT-A-REAL-TOKEN-A1',
        'SIM-NOT-A-REAL-TOKEN-B2',
        'SIM-NOT-A-REAL-TOKEN-C3',
        'SIM-NOT-A-REAL-TOKEN-D4',
        'SIM-NOT-A-REAL-TOKEN-E5'
    ];
    const mockInputs = [
        { label: 'Văn bản bình thường', delay: '0.1s', anomaly: false },
        { label: 'Dấu nháy đơn / kép', delay: '0.1s', anomaly: false },
        { label: 'Ký tự escape', delay: '0.1s', anomaly: false },
        { label: 'Mẫu logic bất thường', delay: '5.0s', anomaly: true }
    ];

    let currentStage = 1;
    let tokenCreated = false;
    let tokenUsed = false;
    let replayCount = 0;
    let runId = 0;
    let scenarioInitialized = false;

    steps.forEach(step => {
        step.addEventListener('click', () => setStage(Number(step.dataset.stage)));
    });

    mode.addEventListener('change', resetScenario);
    document.getElementById('scenario-solve').addEventListener('click', createFakeToken);
    document.getElementById('scenario-feedback-submit').addEventListener('click', () => {
        setStage(2);
        webNotice.textContent = feedbackName.value.trim() && feedbackMessage.value.trim()
            ? 'Góp ý đã được ghi nhận trong giao diện (mô phỏng); không gửi tới server.'
            : 'Nhập tên và nội dung để xem trạng thái minh họa.';
    });
    document.getElementById('scenario-replay').addEventListener('click', replayFakeToken);
    document.getElementById('scenario-fuzz').addEventListener('click', runFuzzPresentation);
    document.getElementById('scenario-exfiltrate').addEventListener('click', runFakeDataAnimation);
    document.getElementById('scenario-impact').addEventListener('click', runImpactCounter);

    function setStage(stage) {
        currentStage = Math.min(4, Math.max(1, stage));
        steps.forEach((step, index) => {
            const active = index + 1 === currentStage;
            step.classList.toggle('is-active', active);
            step.classList.toggle('is-complete', index + 1 < currentStage);
            if (active) {
                step.setAttribute('aria-current', 'step');
            } else {
                step.removeAttribute('aria-current');
            }
        });
        panels.forEach(panel => {
            panel.classList.toggle('is-active', Number(panel.dataset.panel) === currentStage);
        });
        progressFill.style.width = `${((currentStage - 1) / 3) * 100}%`;
    }

    function resetScenario() {
        runId += 1;
        tokenCreated = false;
        tokenUsed = false;
        replayCount = 0;
        dbRows.replaceChildren();
        const emptyRow = dbRows.insertRow();
        const emptyCell = emptyRow.insertCell();
        emptyCell.colSpan = 2;
        emptyCell.className = 'scenario-db-empty';
        emptyCell.textContent = 'Chưa tạo token mô phỏng.';
        dbWarning.textContent = '? Token mẫu sẽ xuất hiện sau khi bấm “Mô phỏng giải”.';
        dbWarning.classList.remove('is-warning');
        dbLock.textContent = '🔒';
        dbCard.classList.remove('is-compromised');
        codeHighlight.classList.remove('is-flashing');
        fuzzTimerPanel.classList.remove('is-found');
        matrixPanel.classList.remove('is-streaming');
        attackPanel.classList.remove('is-impact');
        victimPanel.classList.remove('is-overloaded');
        document.querySelectorAll('.scenario-web-content input, .scenario-web-content textarea, .scenario-web-content button')
            .forEach(control => { control.disabled = false; });
        document.getElementById('scenario-fuzz').disabled = false;
        document.getElementById('scenario-exfiltrate').disabled = false;
        document.getElementById('scenario-impact').disabled = false;
        fuzzResult.textContent = 'Không có request nào được gửi.';
        fuzzStream.querySelectorAll('.scenario-fuzz-row:not(.scenario-fuzz-header)').forEach(row => row.remove());
        const fuzzPlaceholder = fuzzStream.querySelector('.scenario-fuzz-placeholder');
        if (fuzzPlaceholder) fuzzPlaceholder.hidden = false;
        timer.textContent = '0.0s';
        timerNote.textContent = 'Chưa bắt đầu';
        tokenResult.textContent = 'Chưa có dữ liệu mô phỏng.';
        counter.textContent = '0';
        impactResult.textContent = 'Đây chỉ là hoạt ảnh cục bộ; không request được tạo.';
        webNotice.textContent = 'Chưa có hoạt động trong mô phỏng.';
        systemAlert.textContent = 'Hệ thống hoạt động bình thường · dữ liệu giả lập.';
        systemAlert.classList.remove('is-warning');
        setStage(1);
        if (scenarioInitialized) {
            appendReplayLog(`Chế độ đổi sang: ${mode.options[mode.selectedIndex].text}. Token demo được tạo lại khi bấm “Mô phỏng giải”.`, 'info');
        }
        scenarioInitialized = true;
    }

    function appendReplayLog(message, level = 'info') {
        const previousLatest = replayResult.querySelector('.scenario-log-line.is-new');
        if (previousLatest) {
            previousLatest.classList.remove('is-new');
            previousLatest.classList.add('is-old');
        }
        replayResult.querySelector('.is-placeholder')?.remove();

        const line = document.createElement('div');
        line.className = `scenario-log-line is-new is-${level}`;
        line.textContent = message;
        replayResult.append(line);
        replayResult.scrollTop = replayResult.scrollHeight;
    }

    function createFakeToken() {
        setStage(1);
        tokenCreated = true;
        tokenUsed = false;
        replayCount = 0;
        dbRows.replaceChildren();
        const row = dbRows.insertRow();
        const tokenCell = row.insertCell();
        const statusCell = row.insertCell();
        tokenCell.textContent = fakeTokens[0];
        tokenCell.className = 'scenario-token-flight';
        statusCell.textContent = 'HỢP LỆ · GIẢ';
        statusCell.className = 'scenario-token-valid';
        webNotice.textContent = 'CAPTCHA giải thành công (mô phỏng). Một mã giả đã được đưa vào bảng dữ liệu demo.';
        dbWarning.textContent = mode.value === 'vulnerable'
            ? '? Token không tự đổi trạng thái trong mô phỏng có lỗi.'
            : '✓ Token sẽ chuyển sang ĐÃ DÙNG khi được phát lại lần đầu.';
        dbWarning.classList.toggle('is-warning', mode.value === 'vulnerable');
        systemAlert.textContent = 'Đã tạo 1 token giả · không phải challenge hợp lệ.';
        systemAlert.classList.remove('is-warning');
        codeHighlight.classList.add('is-flashing');
        window.setTimeout(() => codeHighlight.classList.remove('is-flashing'), 1800);
        appendReplayLog(`TOKEN ${fakeTokens[0]} · được tạo trong dữ liệu demo, không dùng để xác thực.`, 'info');
    }

    function replayFakeToken() {
        setStage(1);
        if (!tokenCreated) {
            appendReplayLog('Chưa có token giả. Bấm “Mô phỏng giải” ở khung website trước.', 'warning');
            return;
        }

        replayCount += 1;
        const row = dbRows.rows[0];
        const statusCell = row.cells[1];

        if (mode.value === 'vulnerable') {
            appendReplayLog(`POST #${replayCount} (mô phỏng) → HTTP 200 · token vẫn được chấp nhận. Không có request HTTP thật nào được gửi.`, 'success');
            statusCell.textContent = 'HỢP LỆ · CHƯA THU HỒI';
            statusCell.className = 'scenario-token-valid';
            dbWarning.textContent = '? Lỗi minh họa: token vẫn còn nguyên sau lần xác thực.';
            dbWarning.classList.add('is-warning');
            dbCard.classList.add('is-compromised');
            webNotice.textContent = 'THÀNH CÔNG (mô phỏng) · token giả được chấp nhận lại.';
            systemAlert.textContent = 'CẢNH BÁO GIẢ LẬP: token dùng lại vẫn được chấp nhận.';
            systemAlert.classList.add('is-warning');
        } else if (tokenUsed) {
            appendReplayLog(`POST #${replayCount} (mô phỏng) → bị từ chối REPLAY_ATTACK.`, 'blocked');
            webNotice.textContent = 'BỊ TỪ CHỐI · mã đã được dùng.';
        } else {
            tokenUsed = true;
            statusCell.textContent = 'ĐÃ DÙNG · THU HỒI';
            statusCell.className = 'scenario-token-used';
            appendReplayLog(`POST #${replayCount} (mô phỏng) → HTTP 200 lần đầu. Token được thu hồi; lần kế tiếp sẽ bị chặn.`, 'success');
            dbWarning.textContent = '✓ Token đã đổi sang ĐÃ DÙNG sau lần xác thực.';
            dbWarning.classList.remove('is-warning');
            webNotice.textContent = 'LẦN ĐẦU ĐƯỢC CHẤP NHẬN (mô phỏng) · token đã bị thu hồi.';
            systemAlert.textContent = 'Phòng thủ hoạt động: token một lần đã được thu hồi.';
            systemAlert.classList.remove('is-warning');
        }
    }

    async function runFuzzPresentation() {
        setStage(2);
        const thisRun = ++runId;
        const button = document.getElementById('scenario-fuzz');
        button.disabled = true;
        fuzzTimerPanel.classList.remove('is-found');
        fuzzStream.querySelectorAll('.scenario-fuzz-row:not(.scenario-fuzz-header)').forEach(row => row.remove());
        fuzzStream.querySelector('.scenario-fuzz-placeholder').hidden = true;
        fuzzResult.textContent = 'Đang phát lại các nhãn mẫu dựng sẵn; không có request nào được gửi.';

        for (const sample of mockInputs) {
            if (thisRun !== runId) return;
            const line = document.createElement('div');
            line.className = 'scenario-fuzz-row';
            line.setAttribute('role', 'row');
            const payloadCell = document.createElement('span');
            const timingCell = document.createElement('span');
            payloadCell.setAttribute('role', 'cell');
            timingCell.setAttribute('role', 'cell');
            const slowSample = mode.value === 'vulnerable' && sample.delay === '5.0s';
            const shownDelay = slowSample ? sample.delay : '0.1s';
            payloadCell.textContent = `${sample.anomaly ? '⚠ ' : '› '}${sample.label}`;
            timingCell.textContent = shownDelay;
            timingCell.className = `scenario-fuzz-time${slowSample ? ' is-slow' : ''}`;
            line.append(payloadCell, timingCell);
            fuzzStream.append(line);
            fuzzStream.scrollTop = fuzzStream.scrollHeight;
            timer.textContent = shownDelay;
            timerNote.textContent = 'GIÁ TRỊ MÔ PHỎNG · không đo thời gian thật';
            await wait(380);
        }

        if (thisRun === runId) {
            const anomaly = mode.value === 'vulnerable';
            fuzzTimerPanel.classList.toggle('is-found', anomaly);
            fuzzResult.textContent = anomaly
                ? 'DING! Phát hiện điểm bất thường (hiệu ứng dựng sẵn): có thể giải thích error-based/time-based SQLi trong bài thuyết trình. Không SQL nào được thực thi.'
                : 'Phòng thủ minh họa: lỗi chi tiết không lộ ra; đầu vào được coi là dữ liệu. Mọi thời gian hiển thị đều dựng sẵn.';
            systemAlert.textContent = anomaly
                ? 'CẢNH BÁO GIẢ LẬP: phát hiện phản hồi bất thường ở form góp ý.'
                : 'Phòng thủ giả lập: phản hồi lỗi được xử lý an toàn.';
            systemAlert.classList.toggle('is-warning', anomaly);
            button.disabled = false;
        }
    }

    async function runFakeDataAnimation() {
        setStage(3);
        const thisRun = ++runId;
        const button = document.getElementById('scenario-exfiltrate');
        button.disabled = true;
        tokenResult.replaceChildren();
        matrixPanel.classList.add('is-streaming');
        dbLock.textContent = mode.value === 'vulnerable' ? '🔓' : '🔒';

        const records = mode.value === 'vulnerable'
            ? fakeTokens
            : ['MOCK-REDACTED-BY-DEFENSE', 'MOCK-REDACTED-BY-DEFENSE'];
        for (const token of records) {
            if (thisRun !== runId) return;
            const line = document.createElement('span');
            line.className = 'scenario-matrix-line';
            line.textContent = `${mode.value === 'vulnerable' ? 'SIMULATED_ROW' : 'BLOCKED_ROW'}  ${token}`;
            tokenResult.append(line);
            tokenResult.scrollTop = tokenResult.scrollHeight;
            await wait(320);
        }

        if (thisRun === runId) {
            matrixPanel.classList.remove('is-streaming');
            button.disabled = false;
            if (mode.value === 'vulnerable') {
                dbCard.classList.add('is-compromised');
                dbWarning.textContent = '! Minh họa rủi ro: dữ liệu giả rời khỏi khung DB.';
                dbWarning.classList.add('is-warning');
                systemAlert.textContent = 'CẢNH BÁO GIẢ LẬP: luồng dữ liệu minh họa đã bị lộ.';
                systemAlert.classList.add('is-warning');
            } else {
                dbWarning.textContent = '✓ Không có token thật; bản ghi chỉ là nhãn đã che trong mô phỏng.';
            }
        }
    }

    function runImpactCounter() {
        setStage(4);
        const thisRun = ++runId;
        const button = document.getElementById('scenario-impact');
        button.disabled = true;
        const durationMs = 1800;
        const start = performance.now();
        const maximum = mode.value === 'vulnerable' ? 10000 : 10000;
        counterLabel.textContent = mode.value === 'vulnerable'
            ? 'REQUEST GIẢ LẬP ĐƯỢC CHẤP NHẬN'
            : 'LẦN PHÁT LẠI GIẢ LẬP BỊ CHẶN';
        const finalMessage = mode.value === 'vulnerable'
            ? 'Kết thúc hoạt ảnh: con số không phải tài khoản hay request thật. Hệ thống cảnh báo đỏ chỉ để minh họa tác động.'
            : 'Kết thúc hoạt ảnh: biểu diễn số lần phát lại bị chặn, không phải request thật.';

        attackPanel.classList.add('is-impact');
        systemAlert.textContent = mode.value === 'vulnerable'
            ? 'CẢNH BÁO GIẢ LẬP: lưu lượng bất thường — hoạt ảnh đang chạy.'
            : 'BLUE TEAM: phát lại bị chặn — hoạt ảnh minh họa.';
        systemAlert.classList.toggle('is-warning', mode.value === 'vulnerable');
        impactResult.textContent = 'Đang chạy hoạt ảnh tại chỗ…';

        function drawCount(now) {
            if (thisRun !== runId) return;
            const fraction = Math.min(1, (now - start) / durationMs);
            const eased = 1 - (1 - fraction) * (1 - fraction);
            counter.textContent = Math.floor(eased * maximum).toLocaleString('en-US');
            if (fraction < 1) {
                window.requestAnimationFrame(drawCount);
            } else {
                impactResult.textContent = finalMessage;
                if (mode.value === 'vulnerable') {
                    victimPanel.classList.add('is-overloaded');
                    document.querySelectorAll('.scenario-web-content input, .scenario-web-content textarea, .scenario-web-content button')
                        .forEach(control => { control.disabled = true; });
                    systemAlert.textContent = 'SYSTEM OVERLOAD · website demo đang bị khóa trong hoạt ảnh.';
                    systemAlert.classList.add('is-warning');
                }
                button.disabled = false;
            }
        }
        window.requestAnimationFrame(drawCount);
    }

    function wait(milliseconds) {
        return new Promise(resolve => window.setTimeout(resolve, milliseconds));
    }

    resetScenario();
});
