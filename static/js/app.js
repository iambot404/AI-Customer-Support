/**
 * AutoTriage AI Frontend Interactivity
 */

document.addEventListener('DOMContentLoaded', () => {
    initCharCounter();
    initFormSpinner();
    initReclassifySpinner();
    formatTimestamps();
    autoDismissFlashes();
});

// Character Counter for Message Textarea
function initCharCounter() {
    const messageInput = document.getElementById('message');
    const charCountDisplay = document.getElementById('charCount');

    if (messageInput && charCountDisplay) {
        const updateCount = () => {
            const count = messageInput.value.length;
            charCountDisplay.textContent = `${count} / 5000`;
            if (count >= 4900) {
                charCountDisplay.style.color = 'var(--color-urgent)';
            } else if (count >= 4500) {
                charCountDisplay.style.color = 'var(--color-medium)';
            } else {
                charCountDisplay.style.color = 'var(--text-muted)';
            }
        };

        messageInput.addEventListener('input', updateCount);
        updateCount();
    }
}

// Form Submission Spinner
function initFormSpinner() {
    const form = document.getElementById('ticketForm');
    const submitBtn = document.getElementById('submitBtn');

    if (form && submitBtn) {
        form.addEventListener('submit', (e) => {
            const btnText = submitBtn.querySelector('.btn-text');
            const spinner = submitBtn.querySelector('.btn-spinner');

            if (btnText && spinner) {
                btnText.textContent = 'Calling Gemini AI Triage...';
                spinner.classList.remove('hidden');
                submitBtn.disabled = true;
                // Allow form submit to proceed
                form.submit();
            }
        });
    }
}

// Reclassify Button Spinner
function initReclassifySpinner() {
    const reclassifyBtn = document.getElementById('reclassifyBtn');
    if (reclassifyBtn) {
        reclassifyBtn.addEventListener('click', function() {
            this.textContent = '⏳ Re-evaluating with Gemini...';
            this.disabled = true;
            this.closest('form').submit();
        });
    }
}

// Preset Example Fillers
window.fillExample = function(type) {
    const subjectInput = document.getElementById('subject');
    const messageInput = document.getElementById('message');
    const nameInput = document.getElementById('customer_name');
    const emailInput = document.getElementById('customer_email');

    if (!subjectInput || !messageInput) return;

    if (type === 'outage') {
        nameInput.value = 'DevOps Lead - Jordan';
        emailInput.value = 'jordan@cloudenterprise.io';
        subjectInput.value = 'CRITICAL: API gateway 502 Bad Gateway across all production endpoints';
        messageInput.value = 'Starting at 14:15 UTC, all requests to our production API cluster (api.cloudenterprise.io) started returning 502 Bad Gateway. Internal customer traffic is completely blocked, transactions are failing, and our status page is reporting full outage. We need immediate level-3 engineering triage.';
    } else if (type === 'refund') {
        nameInput.value = 'Finance Admin - Sarah';
        emailInput.value = 'sarah@acme.org';
        subjectInput.value = 'Double charge observed on March invoice #INV-98214';
        messageInput.value = 'Hello, our accounting department noticed two separate credit card charges of $499.00 on March 1st for our annual enterprise subscription. Could you please investigate the duplicate charge and process a refund to our original payment method?';
    } else if (type === 'password') {
        nameInput.value = 'Marcus Chen';
        emailInput.value = 'marcus.chen@startup.co';
        subjectInput.value = 'Stuck in password reset verification loop';
        messageInput.value = 'I am trying to log into my developer account, but every time I click the password reset link sent to my inbox, it redirects back to the login page stating "session expired". I cannot access my workspace.';
    } else if (type === 'feature') {
        nameInput.value = 'Elena Rostova';
        emailInput.value = 'elena@designhub.net';
        subjectInput.value = 'Feature request: Add Webhook notifications for resolved tickets';
        messageInput.value = 'It would be fantastic if your platform offered native Slack/Discord webhook alerts whenever a ticket priority changes or gets marked as resolved. This would help our distributed team stay synchronized without checking the dashboard repeatedly.';
    }

    // Trigger character count refresh
    const event = new Event('input', { bubbles: true });
    messageInput.dispatchEvent(event);
};

// Format UTC timestamps into human friendly local strings
function formatTimestamps() {
    document.querySelectorAll('.utc-time').forEach(el => {
        const raw = el.textContent.trim();
        if (raw) {
            try {
                const date = new Date(raw);
                if (!isNaN(date.getTime())) {
                    el.textContent = date.toLocaleString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                }
            } catch (e) {
                // Keep raw if parse fails
            }
        }
    });
}

// Auto-dismiss Flash notifications
function autoDismissFlashes() {
    const flashes = document.querySelectorAll('.flash-alert');
    if (flashes.length > 0) {
        setTimeout(() => {
            flashes.forEach(f => {
                f.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                f.style.opacity = '0';
                f.style.transform = 'translateY(-10px)';
                setTimeout(() => f.remove(), 500);
            });
        }, 6000);
    }
}
