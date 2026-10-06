/**
 * Captcha Security Lab - Main Utilities JS
 */

document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-8px)';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // Close alert manually
    document.querySelectorAll('.alert-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alert = e.target.closest('.alert');
            if (alert) alert.remove();
        });
    });
});
