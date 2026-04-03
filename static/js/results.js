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
    avgScore: 0
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

    // Set active view button
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.view-btn[data-view="${currentState.view}"]`).classList.add('active');

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
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultsContainer = document.getElementById('results-container');
    const emptyResults = document.getElementById('empty-results');
    const pagination = document.getElementById('pagination');
    const cacheNotification = document.getElementById('cache-notification');

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
            pagination.style.display = 'none';
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

    } catch (error) {
        console.error('Error fetching results:', error);
        showError('加载失败，请重试');
        loadingIndicator.style.display = 'none';
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

    currentState.companies.forEach((company, index) => {
        const card = createCompanyCard(company);
        container.appendChild(card);
    });
}

/**
 * Create a single company card
 */
function createCompanyCard(company) {
    const card = document.createElement('div');
    card.className = 'company-card';
    card.innerHTML = `
        <div class="card-header">
            <h3 class="company-name">${escapeHtml(company.name)}</h3>
            <p class="company-location">${escapeHtml(company.city || 'N/A')}, ${escapeHtml(company.country || 'N/A')}</p>
        </div>

        <div class="score-badge" style="background-color: ${getScoreColor(company.prospect_score)}">
            Score: ${company.prospect_score || 'N/A'}/10
        </div>

        <div class="priority-badge priority-${(company.priority || 'LOW').toLowerCase()}">
            ${company.priority || 'N/A'}
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
            <a href="mailto:${company.contact_email || '#'}">${escapeHtml(company.contact_email || 'N/A')}</a>

            <label>🔗 LinkedIn:</label>
            <a href="https://${company.linkedin_url || '#'}" target="_blank">${escapeHtml(company.linkedin_url || 'N/A')}</a>

            <label>🌐 Website:</label>
            <a href="https://${company.website || '#'}" target="_blank">${escapeHtml(company.website || 'N/A')}</a>

            <label>💼 联系职位:</label>
            <span>${escapeHtml(company.best_contact_title || 'N/A')}</span>
        </div>

        <div class="card-actions">
            <button class="action-btn" onclick="copyToClipboard('${company.contact_email || ''}', this)">📋 复制邮箱</button>
            <button class="action-btn" onclick="window.open('https://${company.linkedin_url || '#'}', '_blank')">🔗 打开LinkedIn</button>
            <button class="action-btn" onclick="window.open('https://${company.website || '#'}', '_blank')">🌐 打开网站</button>
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

    const table = document.createElement('table');
    table.className = 'companies-table';

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
            <td><span class="priority-badge priority-${(company.priority || 'LOW').toLowerCase()}">${company.priority || 'N/A'}</span></td>
            <td><a href="mailto:${company.contact_email || '#'}">${escapeHtml(company.contact_email || 'N/A')}</a></td>
            <td><a href="https://${company.linkedin_url || '#'}" target="_blank">LinkedIn</a></td>
            <td><a href="https://${company.website || '#'}" target="_blank">Website</a></td>
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
