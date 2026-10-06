/**
 * Slider Puzzle CAPTCHA - Client Interaction Controller
 * Captcha Security Lab - Information Security Capstone
 */

class SliderCaptcha {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`SliderCaptcha: Container #${containerId} not found.`);
            return;
        }

        this.options = {
            challengeUrl: '/captcha/challenge',
            width: 320,
            pieceSize: 48,
            onSolved: null,
            ...options
        };

        this.challengeId = null;
        this.targetY = 0;
        this.isDragging = false;
        this.startX = 0;
        this.currentX = 0;
        this.maxDrag = this.options.width - this.options.pieceSize;

        this.initDOM();
        this.loadChallenge();
    }

    initDOM() {
        this.container.innerHTML = `
            <div class="captcha-widget" id="captcha-widget-inner">
                <div class="captcha-image-wrapper">
                    <div class="captcha-loading" id="captcha-loading">
                        <div class="spinner"></div>
                        <span>Đang tạo ảnh bảo mật...</span>
                    </div>
                    <img id="captcha-bg" class="captcha-bg-img" alt="Captcha Background" />
                    <img id="captcha-piece" class="captcha-piece-img" alt="Puzzle Piece" />
                    <button type="button" class="captcha-refresh-btn" id="captcha-refresh" title="Đổi câu đố khác">🔄</button>
                </div>

                <div class="captcha-slider-track" id="captcha-track">
                    <div class="captcha-slider-progress" id="captcha-progress"></div>
                    <div class="captcha-slider-text" id="captcha-text">Kéo thanh trượt để khớp mảnh ghép &rarr;</div>
                    <div class="captcha-slider-thumb" id="captcha-thumb">&#10140;</div>
                </div>

                <div class="captcha-status" id="captcha-status"></div>

                <!-- Hidden inputs for Form submission -->
                <input type="hidden" name="captcha_challenge_id" id="captcha_challenge_id" value="" />
                <input type="hidden" name="captcha_user_x" id="captcha_user_x" value="" />
            </div>
        `;

        // Cache elements
        this.bgImg = this.container.querySelector('#captcha-bg');
        this.pieceImg = this.container.querySelector('#captcha-piece');
        this.loadingEl = this.container.querySelector('#captcha-loading');
        this.trackEl = this.container.querySelector('#captcha-track');
        this.progressEl = this.container.querySelector('#captcha-progress');
        this.thumbEl = this.container.querySelector('#captcha-thumb');
        this.textEl = this.container.querySelector('#captcha-text');
        this.statusEl = this.container.querySelector('#captcha-status');
        this.widgetEl = this.container.querySelector('#captcha-widget-inner');
        this.refreshBtn = this.container.querySelector('#captcha-refresh');

        this.inputChallengeId = this.container.querySelector('#captcha_challenge_id');
        this.inputUserX = this.container.querySelector('#captcha_user_x');

        // Bind events
        this.bindEvents();
    }

    bindEvents() {
        this.refreshBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.loadChallenge();
        });

        // Mouse events
        this.thumbEl.addEventListener('mousedown', (e) => this.startDrag(e.clientX));
        window.addEventListener('mousemove', (e) => this.onDrag(e.clientX));
        window.addEventListener('mouseup', () => this.endDrag());

        // Touch events
        this.thumbEl.addEventListener('touchstart', (e) => {
            if (e.touches.length > 0) this.startDrag(e.touches[0].clientX);
        }, { passive: true });

        window.addEventListener('touchmove', (e) => {
            if (e.touches.length > 0) this.onDrag(e.touches[0].clientX);
        }, { passive: true });

        window.addEventListener('touchend', () => this.endDrag());
    }

    async loadChallenge() {
        this.resetSlider();
        this.loadingEl.style.display = 'flex';
        this.statusEl.innerText = '';
        this.statusEl.style.color = '';

        try {
            const res = await fetch(this.options.challengeUrl);
            const data = await res.json();

            if (data.status === 'success') {
                this.challengeId = data.challenge_id;
                this.targetY = data.y;
                this.options.width = data.width || 320;
                this.options.pieceSize = data.piece_size || 48;
                this.maxDrag = this.options.width - this.options.pieceSize;

                // Set image sources
                this.bgImg.src = data.bg_image;
                this.pieceImg.src = data.piece_image;
                this.pieceImg.style.top = `${this.targetY}px`;
                this.pieceImg.style.transform = `translateX(0px)`;

                // Update form hidden input
                this.inputChallengeId.value = this.challengeId;
                this.inputUserX.value = '0';

                this.loadingEl.style.display = 'none';
            } else {
                this.statusEl.innerText = 'Lỗi tải ảnh Captcha. Vui lòng bấm làm mới!';
                this.statusEl.style.color = '#ef4444';
                this.loadingEl.style.display = 'none';
            }
        } catch (err) {
            console.error('Error fetching captcha:', err);
            this.statusEl.innerText = 'Không thể kết nối đến máy chủ!';
            this.statusEl.style.color = '#ef4444';
            this.loadingEl.style.display = 'none';
        }
    }

    startDrag(clientX) {
        if (!this.challengeId) return;
        this.isDragging = true;
        this.startX = clientX;
        this.textEl.style.opacity = '0';
        this.widgetEl.classList.remove('fail', 'shake', 'success');
    }

    onDrag(clientX) {
        if (!this.isDragging) return;

        const delta = clientX - this.startX;
        let x = Math.max(0, Math.min(delta, this.maxDrag));
        this.currentX = x;

        // Move slider thumb and progress bar
        this.thumbEl.style.transform = `translateX(${x}px)`;
        const percent = (x / this.maxDrag) * 100;
        this.progressEl.style.width = `${percent}%`;

        // Move puzzle piece
        this.pieceImg.style.transform = `translateX(${x}px)`;

        // Keep hidden input synchronized
        this.inputUserX.value = Math.round(x);
    }

    endDrag() {
        if (!this.isDragging) return;
        this.isDragging = false;

        const finalX = Math.round(this.currentX);
        this.inputUserX.value = finalX;

        // Provide immediate visual feedback that position is set
        if (finalX > 15) {
            this.statusEl.innerText = `Đã căn chỉnh vị trí (X=${finalX}). Sẵn sàng xác thực!`;
            this.statusEl.style.color = '#38bdf8';
        } else {
            this.resetSlider();
        }

        if (typeof this.options.onSolved === 'function') {
            this.options.onSolved(this.challengeId, finalX);
        }
    }

    resetSlider() {
        this.currentX = 0;
        this.thumbEl.style.transform = 'translateX(0px)';
        this.progressEl.style.width = '0%';
        this.pieceImg.style.transform = 'translateX(0px)';
        this.textEl.style.opacity = '1';
        this.widgetEl.classList.remove('fail', 'shake', 'success');
        this.inputUserX.value = '0';
    }

    markSuccess(msg = 'Xác thực thành công!') {
        this.widgetEl.classList.add('success');
        this.statusEl.innerText = msg;
        this.statusEl.style.color = '#34d399';
        this.thumbEl.innerHTML = '&#10004;';
    }

    markFail(msg = 'Vị trí chưa khớp! Đang làm mới...') {
        this.widgetEl.classList.add('fail', 'shake');
        this.statusEl.innerText = msg;
        this.statusEl.style.color = '#ef4444';
        setTimeout(() => {
            this.loadChallenge();
        }, 900);
    }
}

// Make globally accessible
window.SliderCaptcha = SliderCaptcha;
