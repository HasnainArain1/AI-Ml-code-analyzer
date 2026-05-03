/* ═══════════════════════════════════════════════════
   AI Code Reviewer — Frontend Logic
   ═══════════════════════════════════════════════════ */

const API = '';

// ── State ──
let currentReview = null;
let activeTab = 'analyze';

// ── DOM Ready ──
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    addGaugeGradient();
    positionTabIndicator();        // Initial position for the indicator
    window.addEventListener('resize', positionTabIndicator);
});

function addGaugeGradient() {
    const svg = document.querySelector('.gauge-svg');
    if (!svg) return;
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML = `
        <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#7c3aed"/>
            <stop offset="100%" stop-color="#3b82f6"/>
        </linearGradient>
    `;
    svg.prepend(defs);
}

// ═══════════════════════════════════════════════════
// TAB SWITCHING
// ═══════════════════════════════════════════════════

function switchTab(tab) {
    if (activeTab === tab) return;
    activeTab = tab;

    // Toggle tab buttons
    document.getElementById('tabBtnAnalyze').classList.toggle('active', tab === 'analyze');
    document.getElementById('tabBtnDebug').classList.toggle('active', tab === 'debug');

    // Toggle content
    document.getElementById('tabAnalyze').classList.toggle('active', tab === 'analyze');
    document.getElementById('tabDebug').classList.toggle('active', tab === 'debug');

    // Move indicator
    positionTabIndicator();
}

function positionTabIndicator() {
    const indicator = document.getElementById('tabIndicator');
    const activeBtn = document.querySelector('.tab-btn.active');
    if (!indicator || !activeBtn) return;

    indicator.style.width = activeBtn.offsetWidth + 'px';
    indicator.style.left = activeBtn.offsetLeft + 'px';
}

// ═══════════════════════════════════════════════════
// ANALYZE CODE  (Tab 1)
// ═══════════════════════════════════════════════════

async function analyzeCode() {
    const code = document.getElementById('codeInput').value.trim();
    const errorBanner = document.getElementById('analyzeErrorBanner');

    // Hide previous errors
    errorBanner.style.display = 'none';

    if (!code) {
        showValidationError('analyze', 'Please paste a Python function first.');
        return;
    }

    // Show loading
    const btn = document.getElementById('analyzeBtn');
    btn.disabled = true;
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('loadingSection').style.display = 'block';

    // Animate loading steps
    animateLoadingSteps();

    try {
        const response = await fetch(`${API}/api/review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code }),
        });

        if (!response.ok) {
            let errMsg = 'Failed to analyze code';
            try {
                const err = await response.json();
                errMsg = err.detail || errMsg;
            } catch (_) {
                errMsg = await response.text() || errMsg;
            }
            throw new Error(errMsg);
        }

        const data = await response.json();
        currentReview = data;

        // Hide loading, show results
        document.getElementById('loadingSection').style.display = 'none';
        displayResults(data);
        loadHistory(); // Refresh sidebar

        showToast('Code analysis complete!', 'success');
    } catch (error) {
        document.getElementById('loadingSection').style.display = 'none';
        showValidationError('analyze', error.message);
    } finally {
        btn.disabled = false;
    }
}

// ═══════════════════════════════════════════════════
// DEBUG CODE  (Tab 2)
// ═══════════════════════════════════════════════════

async function debugCode() {
    const code = document.getElementById('debugCodeInput').value.trim();
    const resultSection = document.getElementById('debugResultSection');
    const resultPanel = document.getElementById('debugResultPanel');

    // Hide previous
    resultSection.style.display = 'none';

    if (!code) {
        showDebugResult(false, ['Please paste some Python code first.']);
        return;
    }

    const btn = document.getElementById('debugBtn');
    btn.disabled = true;

    try {
        const response = await fetch(`${API}/api/validate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code }),
        });

        const data = await response.json();

        if (data.valid) {
            showDebugResult(true, []);
        } else {
            showDebugResult(false, data.errors || ['Unknown validation error.']);
        }
    } catch (error) {
        showDebugResult(false, ['Network error: ' + error.message]);
    } finally {
        btn.disabled = false;
    }
}

function showDebugResult(valid, errors) {
    const section = document.getElementById('debugResultSection');
    const panel = document.getElementById('debugResultPanel');

    if (valid) {
        panel.className = 'glass-panel debug-result-panel debug-success';
        panel.innerHTML = `
            <div class="debug-result-icon success-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
            <div class="debug-result-body">
                <h3 class="debug-result-title">No errors found ✅</h3>
                <p class="debug-result-desc">Your code is syntactically correct and contains a valid Python function definition. Great job!</p>
            </div>
        `;
    } else {
        const errorHtml = errors.map(e => `
            <div class="debug-error-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                <span>${escapeHtml(e)}</span>
            </div>
        `).join('');

        panel.className = 'glass-panel debug-result-panel debug-error';
        panel.innerHTML = `
            <div class="debug-result-icon error-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <div class="debug-result-body">
                <h3 class="debug-result-title">Errors Found</h3>
                <div class="debug-error-list">${errorHtml}</div>
            </div>
        `;
    }

    section.style.display = 'block';
    section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ═══════════════════════════════════════════════════
// SHARED: VALIDATION ERROR BANNER (Analyze tab)
// ═══════════════════════════════════════════════════

function showValidationError(tab, message) {
    if (tab === 'analyze') {
        const banner = document.getElementById('analyzeErrorBanner');
        const msg = document.getElementById('analyzeErrorMsg');
        msg.textContent = message;
        banner.style.display = 'flex';
        banner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        showDebugResult(false, [message]);
    }
}

// ═══════════════════════════════════════════════════
// DISPLAY RESULTS
// ═══════════════════════════════════════════════════

function displayResults(data) {
    const section = document.getElementById('resultsSection');
    section.style.display = 'flex';

    // ── Rating Badge ──
    const badge = document.getElementById('ratingBadge');
    const label = data.rating.toLowerCase();
    badge.className = `rating-badge ${label}`;
    document.getElementById('ratingLabel').textContent = data.rating;

    const descriptions = {
        good: 'Excellent! Your code follows best practices and is well-structured.',
        okay: 'Decent code, but there are areas that could be improved.',
        bad: 'This code needs significant refactoring for better quality.',
    };
    document.getElementById('ratingDesc').textContent = descriptions[label] || '';

    // ── Score Gauge ──
    animateScore(data.score);

    // ── Metrics Grid ──
    renderMetrics(data.metrics);

    // ── Suggestions ──
    renderSuggestions(data.suggestions);

    // ── Improved Code ──
    document.getElementById('improvedCodeContent').textContent = data.improved_code || '';

    // ── Diff ──
    renderDiff(data.diff);

    // Scroll to results
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function animateScore(score) {
    const gauge = document.getElementById('gaugeFill');
    const valueEl = document.getElementById('scoreValue');

    // Circumference = 2 * PI * r = 2 * 3.14159 * 52 ≈ 326.73
    const circumference = 326.73;
    const offset = circumference - (score / 10) * circumference;

    // Set color based on score
    if (score >= 7.5) {
        gauge.style.stroke = '#10b981';
    } else if (score >= 4.5) {
        gauge.style.stroke = '#f59e0b';
    } else {
        gauge.style.stroke = '#f43f5e';
    }

    // Animate
    setTimeout(() => {
        gauge.style.strokeDashoffset = offset;
    }, 100);

    // Count up animation
    let current = 0;
    const target = score;
    const duration = 1200;
    const start = performance.now();

    function tick(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        current = (target * eased).toFixed(1);
        valueEl.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(tick);
        }
    }
    requestAnimationFrame(tick);
}

function renderMetrics(metrics) {
    const grid = document.getElementById('metricsGrid');

    const metricConfig = [
        { key: 'cyclomatic_complexity', label: 'Complexity', icon: '⚡', cls: 'complexity' },
        { key: 'num_params', label: 'Parameters', icon: '📥', cls: 'params' },
        { key: 'num_lines', label: 'Lines', icon: '📏', cls: 'lines' },
        { key: 'has_docstring', label: 'Docstring', icon: '📖', cls: 'docstring' },
        { key: 'comment_ratio', label: 'Comment Ratio', icon: '💬', cls: 'comments' },
        { key: 'nesting_depth', label: 'Nesting Depth', icon: '🪺', cls: 'nesting' },
        { key: 'num_returns', label: 'Returns', icon: '↩️', cls: 'returns' },
    ];

    grid.innerHTML = metricConfig.map(m => {
        let value = metrics[m.key];
        let displayValue = value;

        if (m.key === 'has_docstring') {
            displayValue = value ? '✅ Yes' : '❌ No';
        } else if (m.key === 'comment_ratio') {
            displayValue = (value * 100).toFixed(1) + '%';
        }

        return `
            <div class="metric-card">
                <div class="metric-icon ${m.cls}">${m.icon}</div>
                <div class="metric-info">
                    <span class="metric-value">${displayValue}</span>
                    <span class="metric-label">${m.label}</span>
                </div>
            </div>
        `;
    }).join('');
}

function renderSuggestions(suggestions) {
    const container = document.getElementById('suggestionsContent');

    if (!suggestions) {
        container.innerHTML = '<p style="color: var(--text-muted);">No suggestions available.</p>';
        return;
    }

    // Parse numbered suggestions
    const lines = suggestions.split('\n').filter(l => l.trim());
    let html = '';

    for (const line of lines) {
        const match = line.match(/^(\d+)\.\s*(.*)/);
        if (match) {
            html += `
                <div class="suggestion-item">
                    <span class="suggestion-num">${match[1]}.</span>
                    <span>${escapeHtml(match[2])}</span>
                </div>
            `;
        } else {
            html += `
                <div class="suggestion-item">
                    <span class="suggestion-num">•</span>
                    <span>${escapeHtml(line.replace(/^[-•*]\s*/, ''))}</span>
                </div>
            `;
        }
    }

    container.innerHTML = html;
}

function renderDiff(diff) {
    const container = document.getElementById('diffContent');

    if (!diff || !diff.trim()) {
        container.innerHTML = '<div class="diff-line context" style="padding:20px; text-align:center; color:var(--text-muted);">No differences — code is already optimal!</div>';
        return;
    }

    const lines = diff.split('\n');
    let html = '';

    for (const line of lines) {
        if (line.startsWith('+++') || line.startsWith('---')) {
            html += `<div class="diff-line info">${escapeHtml(line)}</div>`;
        } else if (line.startsWith('@@')) {
            html += `<div class="diff-line info">${escapeHtml(line)}</div>`;
        } else if (line.startsWith('+')) {
            html += `<div class="diff-line add">${escapeHtml(line)}</div>`;
        } else if (line.startsWith('-')) {
            html += `<div class="diff-line remove">${escapeHtml(line)}</div>`;
        } else {
            html += `<div class="diff-line context">${escapeHtml(line)}</div>`;
        }
    }

    container.innerHTML = html;
}

// ═══════════════════════════════════════════════════
// LOADING ANIMATION
// ═══════════════════════════════════════════════════

function animateLoadingSteps() {
    const steps = ['step1', 'step2', 'step3', 'step4'];
    let current = 0;

    // Reset
    steps.forEach(id => {
        const el = document.getElementById(id);
        el.className = 'loading-step';
    });
    document.getElementById('step1').classList.add('active');

    const interval = setInterval(() => {
        if (current < steps.length) {
            document.getElementById(steps[current]).classList.remove('active');
            document.getElementById(steps[current]).classList.add('done');
        }
        current++;
        if (current < steps.length) {
            document.getElementById(steps[current]).classList.add('active');
        } else {
            clearInterval(interval);
        }
    }, 1500);
}

// ═══════════════════════════════════════════════════
// HISTORY
// ═══════════════════════════════════════════════════

async function loadHistory() {
    try {
        const response = await fetch(`${API}/api/history`);
        if (!response.ok) return;

        const text = await response.text();
        let reviews;
        try {
            reviews = JSON.parse(text);
        } catch (_) {
            console.error('History response is not valid JSON:', text);
            return;
        }
        renderHistory(reviews);
    } catch (e) {
        console.error('Failed to load history:', e);
    }
}

function renderHistory(reviews) {
    const container = document.getElementById('historyList');

    if (!reviews.length) {
        container.innerHTML = `
            <div class="history-empty">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/></svg>
                <p>No reviews yet</p>
            </div>
        `;
        return;
    }

    container.innerHTML = reviews.map(r => {
        const rating = r.rating.toLowerCase();
        const date = new Date(r.created_at).toLocaleDateString('en-US', {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });

        return `
            <div class="history-item" onclick="loadReview(${r.id})">
                <div class="history-dot ${rating}"></div>
                <div class="history-info">
                    <div class="history-name">${escapeHtml(r.func_name || 'Unnamed')}</div>
                    <div class="history-meta">${date} · ${r.rating}</div>
                </div>
                <div class="history-score">${r.score}</div>
                <button class="history-delete" onclick="event.stopPropagation(); deleteReview(${r.id})" title="Delete">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                </button>
            </div>
        `;
    }).join('');
}

async function loadReview(id) {
    try {
        const response = await fetch(`${API}/api/history/${id}`);
        if (!response.ok) throw new Error('Failed to load review');

        const data = await response.json();
        currentReview = data;

        // Switch to Analyze tab
        switchTab('analyze');

        // Put code back in editor
        document.getElementById('codeInput').value = data.code;

        // Display results
        displayResults(data);

        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
            toggleHistory();
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function deleteReview(id) {
    try {
        const response = await fetch(`${API}/api/history/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete');

        loadHistory();
        showToast('Review deleted', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function toggleHistory() {
    const sidebar = document.getElementById('historySidebar');
    sidebar.classList.toggle('open');

    // Toggle overlay
    let overlay = document.querySelector('.sidebar-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.onclick = toggleHistory;
        document.body.appendChild(overlay);
    }
    overlay.classList.toggle('active');
}

// ═══════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════

function clearCode(tab) {
    if (tab === 'debug') {
        document.getElementById('debugCodeInput').value = '';
        document.getElementById('debugResultSection').style.display = 'none';
    } else {
        document.getElementById('codeInput').value = '';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('analyzeErrorBanner').style.display = 'none';
    }
}

function loadSample(tab) {
    const sample = `def process_data(data, threshold=0.5, max_retries=3):
    results = []
    for item in data:
        if item is not None:
            if isinstance(item, dict):
                if 'value' in item:
                    val = item['value']
                    if val > threshold:
                        for i in range(max_retries):
                            try:
                                processed = val * 2.5
                                results.append(processed)
                                break
                            except Exception:
                                if i == max_retries - 1:
                                    results.append(None)
    return results`;

    if (tab === 'debug') {
        document.getElementById('debugCodeInput').value = sample;
    } else {
        document.getElementById('codeInput').value = sample;
    }
}

function copyImprovedCode() {
    const code = document.getElementById('improvedCodeContent').textContent;
    navigator.clipboard.writeText(code).then(() => {
        showToast('Copied to clipboard!', 'success');
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ── Toast Notifications ──
function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        ${type === 'success' ? '✅' : '⚠️'}
        <span>${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}
