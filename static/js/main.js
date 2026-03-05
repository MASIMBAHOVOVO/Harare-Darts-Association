/* =============================================================================
   HARARE DARTS ASSOCIATION — Main JavaScript
   ============================================================================= */

document.addEventListener('DOMContentLoaded', () => {
    initMobileNav();
    initCountdowns();
    autoCloseFlash();
});

/* ---------- Mobile Navigation ---------- */
function initMobileNav() {
    const toggle = document.getElementById('navToggle');
    const menu = document.getElementById('navMenu');

    if (!toggle || !menu) return;

    toggle.addEventListener('click', () => {
        toggle.classList.toggle('active');
        menu.classList.toggle('active');
    });

    // Close menu when clicking a link
    menu.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            toggle.classList.remove('active');
            menu.classList.remove('active');
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!toggle.contains(e.target) && !menu.contains(e.target)) {
            toggle.classList.remove('active');
            menu.classList.remove('active');
        }
    });
}

/* ---------- Countdown Timers ---------- */
function initCountdowns() {
    const countdowns = document.querySelectorAll('.countdown');
    if (countdowns.length === 0) return;

    function updateCountdowns() {
        countdowns.forEach(el => {
            const target = new Date(el.dataset.target).getTime();
            const now = new Date().getTime();
            const diff = target - now;

            const days = el.querySelector('.days');
            const hours = el.querySelector('.hours');
            const minutes = el.querySelector('.minutes');
            const seconds = el.querySelector('.seconds');

            if (!days || !hours || !minutes || !seconds) return;

            if (diff <= 0) {
                days.textContent = '0';
                hours.textContent = '0';
                minutes.textContent = '0';
                seconds.textContent = '0';
                el.closest('.tournament-card')?.classList.add('event-started');
                return;
            }

            days.textContent = Math.floor(diff / (1000 * 60 * 60 * 24));
            hours.textContent = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            minutes.textContent = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            seconds.textContent = Math.floor((diff % (1000 * 60)) / 1000);
        });
    }

    updateCountdowns();
    setInterval(updateCountdowns, 1000);
}

/* ---------- Auto-close Flash Messages ---------- */
function autoCloseFlash() {
    const flashes = document.querySelectorAll('.flash-message');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });
}

/* ---------- Navbar scroll effect ---------- */
let lastScroll = 0;
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    const currentScroll = window.pageYOffset;
    if (currentScroll > 100) {
        navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.5)';
    } else {
        navbar.style.boxShadow = 'none';
    }
    lastScroll = currentScroll;
});
