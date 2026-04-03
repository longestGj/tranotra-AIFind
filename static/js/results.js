/**
 * Results page JavaScript - Handles API calls, pagination, and view management
 */

// Global state
let currentState = {
    country: null,
    query: null,
    page: 1,
    perPage: 20,
    view: localStorage.getItem('tranotra_leads_view_preference') || 'card',
    totalPages: 1,
    companies: [],
    scrollPosition: 0,
    newCount: 0,
    duplicateCount: 0,
    avgScore: 0,
    isFetching: false  // Prevent duplicate requests
};

/**
 * Initialize page and fetch results
 */
window.addEventListener('DOMContentLoaded', () => {
    // Extract URL parameters
    const params = new URLSearchParams(window.location.search);
    currentState.country = params.get('country') || null;
    currentState.query = params.get('query') || null;
    currentState.page = parseInt(params.get('page') || '1', 10);
    currentState.view = localStorage.getItem('tranotra_leads_view_preference') || 'card';

    // Update title
    updateTitle();

    // Set active view button and render with saved preference
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.querySelector(`.view-btn[data-view="${currentState.view}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    } else {
        // Fallback if saved view is invalid
        currentState.view = 'card';
        document.querySelector(`.view-btn[data-view="card"]`).classList.add('active');
    }

    // Fetch results
    fetchResults();
});

/**
 * Update page title based on search parameters
 */
function updateTitle() {
    const country = currentState.country || '全部国家';
    const keyword = currentState.query || '全部关键词';
    document.getElementById('results-title').textContent = `搜索: ${country} + ${keyword}`;
}

/**
 * Fetch results from API
 */
async function fetchResults() {
    // Prevent duplicate concurrent requests
    if (currentState.isFetching) {
        console.warn('Request already in progress, ignoring duplicate');
        return;
    }

    const loadingIndicator = document.getElementById('loading-indicator');
    const resultsContainer = document.getElementById('results-container');
    const emptyResults = document.getElementById('empty-results');
    const pagination = document.getElementById('pagination');
    const cacheNotification = document.getElementById('cache-notification');

    // Mark as fetching
    currentState.isFetching = true;

    // Show loading
    loadingIndicator.style.display = 'block';
    resultsContainer.innerHTML = '';
    emptyResults.style.display = 'none';
    pagination.style.display = 'none';
    cacheNotification.style.display = 'none';

    try {
        // Build API URL
        const url = new URL('/api/search/results', window.location.origin);
        if (currentState.country) url.searchParams.append('country', currentState.country);
        if (currentState.query) url.searchParams.append('query', currentState.query);
        url.searchParams.append('page', currentState.page);
        url.searchParams.append('per_page', currentState.perPage);

        // Fetch from API
        const response = await fetch(url.toString());

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (!data.success) {
            showError(data.message || '加载失败');
            loadingIndicator.style.display = 'none';
            currentState.isFetching = false;
            return;
        }

        // Update state
        currentState.companies = data.companies || [];
        currentState.totalPages = data.total_pages || 1;
        currentState.newCount = data.new_count || 0;
        currentState.duplicateCount = data.duplicate_count || 0;
        currentState.avgScore = data.avg_score || 0;

        // Update statistics
        updateStatistics();

        // Show cache notification if needed
        if (data.cached && data.message) {
            document.getElementById('cache-message').textContent = data.message;
            cacheNotification.style.display = 'block';
        }

        // Hide loading
        loadingIndicator.style.display = 'none';

        // Check if empty
        if (currentState.companies.length === 0) {
            emptyResults.style.display = 'block';
            resultsContainer.innerHTML = '';
            pagination.style.display = 'none';
            cacheNotification.style.display = 'none';
            return;
        }

        // Render results based on current view
        if (currentState.view === 'card') {
            renderCardView();
        } else {
            renderTableView();
        }

        // Show pagination
        updatePagination();
        pagination.style.display = 'flex';
        currentState.isFetching = false;

    } catch (error) {
        console.error('Error fetching results:', error);
        showError('加载失败，请重试');
        loadingIndicator.style.display = 'none';
        currentState.isFetching = false;
    }
}

/**
 * Update statistics display
 */
function updateStatistics() {
    document.getElementById('stat-new-count').textContent = currentState.newCount;
    document.getElementById('stat-dup-count').textContent = currentState.duplicateCount;
    document.getElementById('stat-avg-score').textContent = currentState.avgScore.toFixed(1);
}

/**
 * Render card view
 */
function renderCardView() {
    const container = document.getElementById('results-container');
    container.innerHTML = '';
    container.className = 'results-container card-view';
    container.setAttribute('role', 'region');
    container.setAttribute('aria-label', `搜索结果列表，共 ${currentState.companies.length} 家公司`);

    currentState.companies.forEach((company, index) => {
        const card = createCompanyCard(company, index);
        card.setAttribute('role', 'article');
        card.setAttribute('aria-labelledby', `company-name-${index}`);
        container.appendChild(card);
    });
}

/**
 * Create a single company card
 */
function createCompanyCard(company, index = 0) {
    const card = document.createElement('div');
    card.className = 'company-card';
    card.innerHTML = `
        <div class="card-header">
            <h3 class="company-name" id="company-name-${index}">${escapeHtml(company.name)}</h3>
            <p class="company-location">${escapeHtml(company.city || 'N/A')}, ${escapeHtml(company.country || 'N/A')}</p>
        </div>

        <div class="score-badge" style="background-color: ${getScoreColor(company.prospect_score)}" role="img" aria-label="评分: ${company.prospect_score || 'N/A'}/10">
            Score: ${company.prospect_score || 'N/A'}/10
        </div>

        <div class="priority-badge priority-${sanitizeCssClass(company.priority || 'LOW')}" aria-label="优先级: ${escapeHtml(company.priority || 'N/A')}">
            ${escapeHtml(company.priority || 'N/A')}
        </div>

        <div class="card-details">
            <div class="detail-grid">
                <div class="detail-item">
                    <label>👥 员工:</label>
                    <span>${escapeHtml(company.employees || 'N/A')}</span>
                </div>
                <div class="detail-item">
                    <label>💰 年收:</label>
                    <span>${escapeHtml(company.estimated_revenue || 'N/A')}</span>
                </div>
                <div class="detail-item">
                    <label>🏭 产品:</label>
                    <span>${escapeHtml(company.main_products || 'N/A')}</span>
                </div>
                <div class="detail-item">
                    <label>🌍 出口:</label>
                    <span>${escapeHtml(company.export_markets || 'N/A')}</span>
                </div>
                <div class="detail-item">
                    <label>🎯 推荐产品:</label>
                    <span>${escapeHtml(company.recommended_product || 'N/A')}</span>
                </div>
                <div class="detail-item">
                    <label>📝 推荐理由:</label>
                    <span>${escapeHtml(company.recommendation_reason || 'N/A')}</span>
                </div>
            </div>
        </div>

        <div class="card-contact">
            <label>📧 Email:</label>
            <a href="mailto:${sanitizeEmail(company.contact_email) ? 'mailto:' + sanitizeEmail(company.contact_email) : '#'}" aria-label="邮件: ${escapeHtml(company.contact_email || 'N/A')}">${escapeHtml(company.contact_email || 'N/A')}</a>

            <label>🔗 LinkedIn:</label>
            <a href="${sanitizeUrl(company.linkedin_url)}" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn: ${escapeHtml(company.linkedin_url || 'N/A')}">${escapeHtml(company.linkedin_url || 'N/A')}</a>

            <label>🌐 Website:</label>
            <a href="${sanitizeUrl(company.website)}" target="_blank" rel="noopener noreferrer" aria-label="网站: ${escapeHtml(company.website || 'N/A')}">${escapeHtml(company.website || 'N/A')}</a>

            <label>💼 联系职位:</label>
            <span>${escapeHtml(company.best_contact_title || 'N/A')}</span>
        </div>

        <div class="card-actions">
            <button class="action-btn" data-email="${escapeHtml(company.contact_email || '')}" onclick="copyToClipboard(this.getAttribute('data-email'), this)" aria-label="复制邮箱: ${escapeHtml(company.contact_email || 'N/A')}">📋 复制邮箱</button>
            <button class="action-btn" data-url="${sanitizeUrl(company.linkedin_url)}" onclick="openUrl(this.getAttribute('data-url'))" aria-label="打开 LinkedIn">🔗 打开LinkedIn</button>
            <button class="action-btn" data-url="${sanitizeUrl(company.website)}" onclick="openUrl(this.getAttribute('data-url'))" aria-label="打开网站">🌐 打开网站</button>
        </div>
    `;
    return card;
}

/**
 * Render table view
 */
function renderTableView() {
    const container = document.getElementById('results-container');
    container.innerHTML = '';
    container.className = 'results-container table-view';
    container.setAttribute('role', 'region');
    container.setAttribute('aria-label', `搜索结果表格，共 ${currentState.companies.length} 家公司`);

    const table = document.createElement('table');
    table.className = 'companies-table';
    table.setAttribute('role', 'table');
    table.setAttribute('aria-label', '公司搜索结果');

    // Header
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>#</th>
            <th>公司名称</th>
            <th>国家</th>
            <th>评分</th>
            <th>优先级</th>
            <th>邮箱</th>
            <th>LinkedIn</th>
            <th>网站</th>
        </tr>
    `;
    table.appendChild(thead);

    // Body
    const tbody = document.createElement('tbody');
    currentState.companies.forEach((company, index) => {
        const row = document.createElement('tr');
        row.className = index % 2 === 0 ? 'even' : 'odd';
        row.innerHTML = `
            <td>${index + 1}</td>
            <td title="${escapeHtml(company.name)}">${escapeHtml(company.name)}</td>
            <td>${escapeHtml(company.country || 'N/A')}</td>
            <td>${company.prospect_score || 'N/A'}</td>
            <td><span class="priority-badge priority-${sanitizeCssClass(company.priority || 'LOW')}">${escapeHtml(company.priority || 'N/A')}</span></td>
            <td><a href="${sanitizeEmail(company.contact_email) ? 'mailto:' + sanitizeEmail(company.contact_email) : '#'}">${escapeHtml(company.contact_email || 'N/A')}</a></td>
            <td><a href="${sanitizeUrl(company.linkedin_url)}" target="_blank">LinkedIn</a></td>
            <td><a href="${sanitizeUrl(company.website)}" target="_blank">Website</a></td>
        `;
        tbody.appendChild(row);
    });
    table.appendChild(tbody);

    container.appendChild(table);
}

/**
 * Get color based on score
 */
function getScoreColor(score) {
    score = parseInt(score) || 0;
    if (score >= 8) return '#4CAF50'; // Green
    if (score >= 6) return '#FFC107'; // Yellow
    return '#F44336'; // Red
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Validate and sanitize URLs
 */
function sanitizeUrl(url) {
    if (!url || typeof url !== 'string') return '#';
    url = url.trim();
    if (url.startsWith('http://') || url.startsWith('https://')) {
        return url;
    }
    if (url.startsWith('//')) {
        return 'https:' + url;
    }
    return '#';
}

/**
 * Validate and encode email
 */
function sanitizeEmail(email) {
    if (!email || typeof email !== 'string') return '';
    email = email.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (emailRegex.test(email)) {
        return encodeURIComponent(email);
    }
    return '';
}

/**
 * Sanitize CSS class name
 */
function sanitizeCssClass(value) {
    if (!value || typeof value !== 'string') return 'low';
    const sanitized = value.toLowerCase().replace(/[^a-z0-9_-]/g, '');
    return sanitized || 'low';
}

/**
 * Copy to clipboard
 */
function copyToClipboard(text, button) {
    if (!text) {
        alert('邮箱不可用');
        return;
    }
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = '已复制';
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('复制失败');
    });
}

/**
 * Safely open URL
 */
function openUrl(url) {
    const safeUrl = sanitizeUrl(url);
    if (safeUrl !== '#') {
        window.open(safeUrl, '_blank', 'noopener,noreferrer');
    }
}

/**
 * Switch view between card and table
 */
function switchView(view) {
    currentState.view = view;
    localStorage.setItem('tranotra_leads_view_preference', view);

    // Update button styles
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.view-btn[data-view="${view}"]`).classList.add('active');

    // Re-render
    if (view === 'card') {
        renderCardView();
    } else {
        renderTableView();
    }
}

/**
 * Update pagination display
 */
function updatePagination() {
    const pageInfo = document.getElementById('page-info');
    pageInfo.textContent = `第 ${currentState.page} 页，共 ${currentState.totalPages} 页`;

    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

    prevBtn.disabled = currentState.page <= 1;
    nextBtn.disabled = currentState.page >= currentState.totalPages;
}

/**
 * Go to previous page
 */
function previousPage() {
    if (currentState.page > 1) {
        currentState.page--;
        updateUrl();
        fetchResults();
        window.scrollTo(0, 0);
    }
}

/**
 * Go to next page
 */
function nextPage() {
    if (currentState.page < currentState.totalPages) {
        currentState.page++;
        updateUrl();
        fetchResults();
        window.scrollTo(0, 0);
    }
}

/**
 * Update URL to reflect current state
 */
function updateUrl() {
    const params = new URLSearchParams();
    if (currentState.country) params.append('country', currentState.country);
    if (currentState.query) params.append('query', currentState.query);
    if (currentState.page > 1) params.append('page', currentState.page);

    const newUrl = params.toString() ? `/results?${params.toString()}` : '/results';
    window.history.replaceState({}, '', newUrl);
}

/**
 * Go back to search page
 */
function goBackToSearch() {
    window.location.href = '/';
}

/**
 * Show error message
 */
function showError(message) {
    const container = document.getElementById('results-container');
    container.innerHTML = `<div class="error-message"><p>❌ ${escapeHtml(message)}</p></div>`;
}
