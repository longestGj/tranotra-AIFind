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
    isFetching: false,  // Prevent duplicate requests
    // Table view state
    sortColumn: 'prospect_score',
    sortDirection: 'desc'  // 'asc' or 'desc'
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

    // Initialize keyboard navigation
    setupViewToggleKeyboard();

    // Mobile default: use card view if screen width < 768px
    if (window.innerWidth < 768 && currentState.view !== 'card') {
        // Don't force card view, but log a note
        console.info('Mobile device detected - card view recommended');
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
    card.setAttribute('data-company-id', company.id);

    const scoreClass = company.prospect_score >= 8 ? 'score-high' :
                       company.prospect_score >= 6 ? 'score-medium' : 'score-low';
    const priorityEmoji = company.priority === 'HIGH' ? '🔴' :
                          company.priority === 'MEDIUM' ? '🟡' : '⚫';

    // Check if company is marked as contacted
    const contactedCompanies = JSON.parse(localStorage.getItem('tranotra_leads_contacted_companies') || '{}');
    const isContacted = !!contactedCompanies[company.id];

    card.innerHTML = `
        <div class="card-header">
            <h2 class="card-title" id="company-name-${index}">${escapeHtml(company.name)}</h2>
            <p class="card-location">
                <span class="icon">📍</span>
                ${escapeHtml(company.city || 'N/A')}, ${escapeHtml(company.country || 'N/A')}
            </p>
        </div>

        <div class="score-badge ${scoreClass}" role="img" aria-label="评分: ${company.prospect_score || 'N/A'}/10">
            <span class="score-label">评分:</span>
            <span class="score-value">${company.prospect_score || 'N/A'}/10</span>
            <span class="priority-label">${priorityEmoji} ${escapeHtml(company.priority || 'N/A')}</span>
        </div>

        <div class="card-details-grid">
            <div class="detail-item">
                <span class="icon">👥</span>
                <span class="label">员工:</span>
                <span class="value">${escapeHtml(company.employees || 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="icon">💰</span>
                <span class="label">年收:</span>
                <span class="value">${escapeHtml(company.estimated_revenue || 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="icon">🏭</span>
                <span class="label">产品:</span>
                <span class="value">${escapeHtml(company.main_products || 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="icon">🌍</span>
                <span class="label">出口:</span>
                <span class="value">${escapeHtml(company.export_markets || 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="icon">🎯</span>
                <span class="label">推荐产品:</span>
                <span class="value">${escapeHtml(company.recommended_product || 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="icon">📝</span>
                <span class="label">推荐理由:</span>
                <span class="value">${escapeHtml(company.recommendation_reason || 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="icon">⚙️</span>
                <span class="label">原材料:</span>
                <span class="value">${escapeHtml(company.raw_materials || 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="icon">📅</span>
                <span class="label">成立年份:</span>
                <span class="value">${escapeHtml(company.year_established || 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="icon">🚀</span>
                <span class="label">EU/US/JP出口:</span>
                <span class="value">${escapeHtml(company.eu_us_jp_export || 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="icon">🕐</span>
                <span class="label">创建时间:</span>
                <span class="value">${escapeHtml(company.created_at || 'N/A')}</span>
            </div>
        </div>

        <div class="contact-section">
            <div class="contact-item">
                <span class="icon">📧</span>
                <a href="mailto:${sanitizeEmail(company.contact_email) ? sanitizeEmail(company.contact_email) : '#'}" class="contact-link" aria-label="邮件: ${escapeHtml(company.contact_email || 'N/A')}">${escapeHtml(company.contact_email || 'N/A')}</a>
            </div>
            <div class="contact-item">
                <span class="icon">🔗</span>
                <a href="${sanitizeUrl(company.linkedin_url)}" target="_blank" rel="noopener noreferrer" class="contact-link" aria-label="LinkedIn: ${escapeHtml(company.linkedin_url || 'N/A')}">LinkedIn</a>
            </div>
            <div class="contact-item">
                <span class="icon">🌐</span>
                <a href="${sanitizeUrl(company.website)}" target="_blank" rel="noopener noreferrer" class="contact-link" aria-label="网站: ${escapeHtml(company.website || 'N/A')}">Website</a>
            </div>
            <div class="contact-item">
                <span class="icon">💼</span>
                <span>${escapeHtml(company.best_contact_title || 'N/A')}</span>
            </div>
        </div>

        <div class="card-actions">
            <button class="action-btn btn-copy" data-email="${escapeHtml(company.contact_email || '')}" aria-label="复制邮箱: ${escapeHtml(company.contact_email || 'N/A')}">📋 Copy Email</button>
            <button class="action-btn btn-open-linkedin" data-url="${sanitizeUrl(company.linkedin_url)}" aria-label="打开 LinkedIn">🔗 Open LinkedIn</button>
            <button class="action-btn btn-open-website" data-url="${sanitizeUrl(company.website)}" aria-label="打开网站">🌐 Open Website</button>
            <button class="action-btn btn-draft-email" disabled title="Coming in Phase 2">📧 Draft Email</button>
            <button class="action-btn btn-mark-contacted ${isContacted ? 'active' : ''}" data-company-id="${company.id}" aria-label="${isContacted ? '取消标记' : '标记已联系'}">
                ${isContacted ? '✗ Unmark' : '✓ Mark as Contacted'}
            </button>
            <button class="action-btn btn-add-note" data-company-id="${company.id}" aria-label="添加备注">📝 Add Note</button>
        </div>
    `;

    // Attach event listeners
    attachCardActions(card, company);

    return card;
}

/**
 * Attach event listeners to card action buttons
 */
function attachCardActions(cardElement, company) {
    // Copy email button
    const copyBtn = cardElement.querySelector('.btn-copy');
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            const email = this.getAttribute('data-email');
            copyToClipboard(email, this);
        });
    }

    // Open LinkedIn button
    const linkedinBtn = cardElement.querySelector('.btn-open-linkedin');
    if (linkedinBtn) {
        linkedinBtn.addEventListener('click', function() {
            const url = this.getAttribute('data-url');
            openUrl(url);
        });
    }

    // Open Website button
    const websiteBtn = cardElement.querySelector('.btn-open-website');
    if (websiteBtn) {
        websiteBtn.addEventListener('click', function() {
            const url = this.getAttribute('data-url');
            openUrl(url);
        });
    }

    // Mark as Contacted button
    const markBtn = cardElement.querySelector('.btn-mark-contacted');
    if (markBtn) {
        markBtn.addEventListener('click', function() {
            const companyId = this.getAttribute('data-company-id');
            toggleContacted(companyId, this);
        });
    }

    // Add Note button
    const noteBtn = cardElement.querySelector('.btn-add-note');
    if (noteBtn) {
        noteBtn.addEventListener('click', function() {
            const companyId = this.getAttribute('data-company-id');
            openNoteModal(companyId);
        });
    }
}

/**
 * Render table view with sorting
 */
function renderTableView() {
    const container = document.getElementById('results-container');
    container.innerHTML = '';
    container.className = 'results-container table-view';
    container.setAttribute('role', 'region');
    container.setAttribute('aria-label', `搜索结果表格，共 ${currentState.companies.length} 家公司`);

    // Show mobile warning if on small screen
    if (window.innerWidth < 768) {
        const warning = document.createElement('div');
        warning.className = 'mobile-table-warning';
        warning.setAttribute('role', 'alert');
        warning.innerHTML = '⚠️ 此视图在手机上显示可能不清晰，推荐使用卡片视图';
        warning.style.cssText = `
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 12px 16px;
            margin-bottom: 20px;
            border-radius: 4px;
            font-size: 14px;
        `;
        container.appendChild(warning);
    }

    // Load sort preference from localStorage (only on first render to avoid race conditions)
    // Use a flag to prevent reloading on every render
    if (!currentState._sortPrefLoaded) {
        const sortPref = localStorage.getItem('tranotra_leads_table_sort');
        if (sortPref) {
            try {
                const pref = JSON.parse(sortPref);
                currentState.sortColumn = pref.column || 'prospect_score';
                currentState.sortDirection = pref.direction || 'desc';
            } catch (e) {
                console.warn('Failed to parse sort preference:', e);
                // Fall back to default sort
                currentState.sortColumn = 'prospect_score';
                currentState.sortDirection = 'desc';
            }
        }
        currentState._sortPrefLoaded = true;
    }

    // Sort companies based on current preferences
    const sortedCompanies = sortTableData(currentState.companies, currentState.sortColumn, currentState.sortDirection);

    const table = document.createElement('table');
    table.className = 'companies-table';
    table.setAttribute('role', 'table');
    table.setAttribute('aria-label', '公司搜索结果');

    // Header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    const columns = [
        { key: null, label: '#', sortable: false },
        { key: 'name', label: '公司名称', sortable: true },
        { key: 'country', label: '国家', sortable: true },
        { key: 'prospect_score', label: '评分', sortable: true },
        { key: 'priority', label: '优先级', sortable: true },
        { key: 'contact_email', label: '邮箱', sortable: false },
        { key: 'linkedin_url', label: 'LinkedIn', sortable: false },
        { key: 'website', label: '网站', sortable: true }
    ];

    columns.forEach(col => {
        const th = document.createElement('th');
        if (col.sortable) {
            th.className = 'sortable-header';
            th.setAttribute('data-sort-column', col.key);
            th.style.cursor = 'pointer';

            // Add sort indicator if this is the current sort column
            let indicator = '';
            if (currentState.sortColumn === col.key) {
                indicator = currentState.sortDirection === 'asc' ? ' ↑' : ' ↓';
            }
            th.innerHTML = col.label + indicator;
            th.addEventListener('click', () => handleTableHeaderClick(col.key));
        } else {
            th.innerHTML = col.label;
        }
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Body with sorted data
    const tbody = document.createElement('tbody');
    sortedCompanies.forEach((company, index) => {
        const row = document.createElement('tr');
        row.className = 'data-row ' + (index % 2 === 0 ? 'even' : 'odd');
        row.setAttribute('data-company-id', company.id);

        const cells = [
            `<td class="row-number">${index + 1}</td>`,
            `<td class="company-name-cell" title="${escapeHtml(company.name)}">${escapeHtml(truncateText(company.name, 30))}</td>`,
            `<td>${escapeHtml(company.country || 'N/A')}</td>`,
            `<td class="score-cell">${company.prospect_score || 'N/A'}</td>`,
            `<td><span class="priority-badge priority-${sanitizeCssClass(company.priority || 'LOW')}">${escapeHtml(company.priority || 'N/A')}</span></td>`,
            `<td><a href="${sanitizeEmail(company.contact_email) ? 'mailto:' + sanitizeEmail(company.contact_email) : '#'}" class="table-link">${escapeHtml(company.contact_email || 'N/A')}</a></td>`,
            `<td><a href="${sanitizeUrl(company.linkedin_url)}" target="_blank" rel="noopener noreferrer" class="table-link">LinkedIn</a></td>`,
            `<td class="website-column"><a href="${sanitizeUrl(company.website)}" target="_blank" rel="noopener noreferrer" class="table-link">Website</a></td>`
        ];

        row.innerHTML = cells.join('');

        // Add click handler for row selection
        row.addEventListener('click', () => {
            document.querySelectorAll('.data-row').forEach(r => r.classList.remove('selected'));
            row.classList.add('selected');
        });

        tbody.appendChild(row);
    });
    table.appendChild(tbody);

    container.appendChild(table);
}

/**
 * Sort table data
 */
function sortTableData(companies, column, direction) {
    // Validate column parameter to prevent prototype pollution
    const allowedColumns = ['name', 'country', 'prospect_score', 'priority', 'website'];
    if (!allowedColumns.includes(column)) {
        console.warn(`Invalid sort column: ${column}. Using default.`);
        column = 'prospect_score';
    }

    const sorted = [...companies];

    sorted.sort((a, b) => {
        let aVal = a[column];
        let bVal = b[column];

        // Handle null/undefined values
        if (aVal == null) aVal = '';
        if (bVal == null) bVal = '';

        // Convert to comparable values
        if (typeof aVal === 'string') {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        } else if (typeof aVal === 'number' && typeof bVal === 'number') {
            // Handle numeric comparison directly
            if (direction === 'asc') {
                return aVal - bVal;
            } else {
                return bVal - aVal;
            }
        }

        if (direction === 'asc') {
            return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
        } else {
            return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
        }
    });

    return sorted;
}

/**
 * Handle table header click for sorting
 */
function handleTableHeaderClick(column) {
    const newDirection = (currentState.sortColumn === column && currentState.sortDirection === 'desc') ? 'asc' : 'desc';
    currentState.sortColumn = column;
    currentState.sortDirection = newDirection;

    // Save preference to localStorage with error handling
    try {
        localStorage.setItem('tranotra_leads_table_sort', JSON.stringify({
            column: currentState.sortColumn,
            direction: currentState.sortDirection
        }));
    } catch (e) {
        if (e.name === 'QuotaExceededError') {
            console.warn('localStorage quota exceeded, sort preference not saved');
        } else {
            console.warn('Failed to save sort preference:', e);
        }
        // Continue anyway - sort will still work, just won't be persisted
    }

    // Reset the loaded flag to allow re-reading from localStorage on next render
    currentState._sortPrefLoaded = false;

    // Re-render table
    renderTableView();
}

/**
 * Truncate text to max length
 */
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
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

    // Block dangerous protocols
    const lowerUrl = url.toLowerCase();
    if (lowerUrl.startsWith('javascript:') ||
        lowerUrl.startsWith('data:') ||
        lowerUrl.startsWith('vbscript:')) {
        return '#';
    }

    // Allow http, https, and protocol-relative URLs
    if (url.startsWith('http://') || url.startsWith('https://')) {
        try {
            // Validate it's a valid URL
            new URL(url);
            return url;
        } catch (e) {
            return '#';
        }
    }
    if (url.startsWith('//')) {
        try {
            new URL('https:' + url);
            return 'https:' + url;
        } catch (e) {
            return '#';
        }
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
 * Save card view state (scroll position)
 */
function saveCardViewState() {
    try {
        const scrollPos = document.documentElement.scrollTop || document.body.scrollTop;
        localStorage.setItem('tranotra_leads_card_scroll', scrollPos.toString());
    } catch (e) {
        if (e.name === 'QuotaExceededError') {
            console.warn('localStorage quota exceeded, scroll position not saved');
        }
    }
}

/**
 * Restore card view state (scroll position)
 */
function restoreCardViewState() {
    try {
        const savedScroll = localStorage.getItem('tranotra_leads_card_scroll');
        if (savedScroll) {
            const scrollPos = parseInt(savedScroll, 10);
            if (!isNaN(scrollPos) && scrollPos >= 0) {
                // Use requestAnimationFrame to ensure DOM is fully rendered
                // with longer timeout as fallback for slower devices
                if (window.requestAnimationFrame) {
                    requestAnimationFrame(() => {
                        window.scrollTo(0, scrollPos);
                    });
                } else {
                    setTimeout(() => {
                        window.scrollTo(0, scrollPos);
                    }, 100);
                }
            }
        }
    } catch (e) {
        console.warn('Failed to restore card scroll position:', e);
    }
}

/**
 * Save table view state (sort, direction, page)
 */
function saveTableViewState() {
    try {
        const tableState = {
            view: 'table',
            sortColumn: currentState.sortColumn || 'prospect_score',
            sortDir: currentState.sortDirection || 'desc',
            page: currentState.page || 1
        };
        localStorage.setItem('tranotra_leads_table_state', JSON.stringify(tableState));
    } catch (e) {
        if (e.name === 'QuotaExceededError') {
            console.warn('localStorage quota exceeded, table state not saved');
        }
    }
}

/**
 * Restore table view state (sort, direction, page)
 */
function restoreTableViewState() {
    try {
        const saved = localStorage.getItem('tranotra_leads_table_state');
        if (saved) {
            const state = JSON.parse(saved);
            // Validate state is an object with expected structure
            if (state && typeof state === 'object') {
                // Validate sortColumn exists and is a valid column
                const validColumns = ['name', 'country', 'prospect_score', 'priority', 'website'];
                if (state.sortColumn && validColumns.includes(state.sortColumn)) {
                    currentState.sortColumn = state.sortColumn;
                } else {
                    currentState.sortColumn = 'prospect_score';
                }

                // Validate sortDir is 'asc' or 'desc'
                if (state.sortDir === 'asc' || state.sortDir === 'desc') {
                    currentState.sortDirection = state.sortDir;
                } else {
                    currentState.sortDirection = 'desc';
                }

                // Validate page is a positive integer
                if (typeof state.page === 'number' && state.page >= 1) {
                    currentState.page = Math.floor(state.page);
                } else {
                    currentState.page = 1;
                }
            }
        }
    } catch (e) {
        console.warn('Failed to restore table state:', e);
    }
}

/**
 * Switch view between card and table
 */
function switchView(view) {
    const container = document.getElementById('results-container');

    // Prevent multiple view switches during animation
    if (currentState._animationInProgress) {
        console.warn('View switch animation already in progress, ignoring request');
        return;
    }

    // Save state before switching away
    if (currentState.view === 'card') {
        saveCardViewState();
    } else if (currentState.view === 'table') {
        saveTableViewState();
    }

    currentState.view = view;

    try {
        localStorage.setItem('tranotra_leads_view_preference', view);
    } catch (e) {
        if (e.name === 'QuotaExceededError') {
            console.warn('localStorage quota exceeded, view preference not saved');
        }
    }

    // Update button styles and disable during animation
    const viewBtns = document.querySelectorAll('.view-btn');
    viewBtns.forEach(btn => {
        btn.classList.remove('active');
        btn.disabled = true;  // Disable buttons during animation
    });
    document.querySelector(`.view-btn[data-view="${view}"]`).classList.add('active');

    // Reset sort preference loading flag and restore table state before rendering
    if (view === 'table') {
        currentState._sortPrefLoaded = false;
        // Restore table state before rendering
        restoreTableViewState();
        // Mark as loaded to prevent re-loading in renderTableView
        currentState._sortPrefLoaded = true;
    }

    // Add fade animation
    if (container) {
        currentState._animationInProgress = true;
        container.classList.add('view-fade-out');

        setTimeout(() => {
            // Re-render
            if (view === 'card') {
                renderCardView();
            } else {
                renderTableView();
            }

            // Remove fade-out and add fade-in
            const newContainer = document.getElementById('results-container');
            if (newContainer) {
                newContainer.classList.remove('view-fade-out');
                newContainer.classList.add('view-fade-in');

                setTimeout(() => {
                    newContainer.classList.remove('view-fade-in');
                    // Re-enable buttons after animation
                    viewBtns.forEach(btn => {
                        btn.disabled = false;
                    });
                    currentState._animationInProgress = false;

                    // Restore scroll position after animation completes
                    if (view === 'card') {
                        restoreCardViewState();
                    }
                }, 300);
            }
        }, 150);
    } else {
        // Fallback if container not found
        if (view === 'card') {
            renderCardView();
            restoreCardViewState();
        } else {
            renderTableView();
        }
        // Re-enable buttons
        viewBtns.forEach(btn => {
            btn.disabled = false;
        });
        currentState._animationInProgress = false;
    }
}

/**
 * Update pagination display
 */
function updatePagination() {
    const pageInfo = document.getElementById('page-info');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const pageNumbersContainer = document.getElementById('page-numbers');
    const jumpInput = document.getElementById('jump-page-input');

    // Update page info text
    // Handle case where totalPages is 0 or undefined
    const totalPages = Math.max(currentState.totalPages || 1, 1);
    const totalRecords = (totalPages - 1) * currentState.perPage + currentState.companies.length;
    const startRecord = currentState.companies.length > 0 ? (currentState.page - 1) * currentState.perPage + 1 : 0;
    const endRecord = currentState.companies.length > 0 ? Math.min(currentState.page * currentState.perPage, totalRecords) : 0;
    pageInfo.textContent = `显示 ${startRecord}-${endRecord} / ${totalRecords} 条记录`;

    // Update Previous/Next buttons
    prevBtn.disabled = currentState.page <= 1;
    nextBtn.disabled = currentState.page >= currentState.totalPages;

    // Generate page numbers
    if (pageNumbersContainer) {
        pageNumbersContainer.innerHTML = '';

        const maxPagesToShow = 5;
        let startPage = Math.max(1, currentState.page - Math.floor(maxPagesToShow / 2));
        let endPage = Math.min(currentState.totalPages, startPage + maxPagesToShow - 1);

        if (endPage - startPage + 1 < maxPagesToShow) {
            startPage = Math.max(1, endPage - maxPagesToShow + 1);
        }

        // Add ellipsis if needed at the beginning
        if (startPage > 1) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'page-ellipsis';
            ellipsis.textContent = '...';
            pageNumbersContainer.appendChild(ellipsis);
        }

        // Add page number buttons
        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.className = `page-number ${i === currentState.page ? 'active' : ''}`;
            pageBtn.textContent = i;
            pageBtn.onclick = () => goToPage(i);
            pageNumbersContainer.appendChild(pageBtn);
        }

        // Add ellipsis if needed at the end
        if (endPage < currentState.totalPages) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'page-ellipsis';
            ellipsis.textContent = '...';
            pageNumbersContainer.appendChild(ellipsis);
        }
    }

    // Update jump input max value (always set, regardless of pageNumbersContainer)
    if (jumpInput) {
        jumpInput.max = Math.max(currentState.totalPages, 1);
    }
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
 * Go to specific page
 */
function goToPage(pageNum) {
    // Prevent multiple concurrent requests (race condition)
    if (currentState.isFetching) {
        console.warn('Request already in progress, ignoring duplicate page navigation');
        return;
    }

    if (pageNum >= 1 && pageNum <= currentState.totalPages) {
        currentState.page = pageNum;
        fetchResults();  // fetchResults will update URL and set isFetching flag
        window.scrollTo(0, 0);
    }
}

/**
 * Jump to page via input field
 */
function jumpToPage() {
    const input = document.getElementById('jump-page-input');
    const pageNum = parseInt(input.value, 10);
    const maxPage = Math.max(currentState.totalPages || 1, 1);

    if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= maxPage) {
        goToPage(pageNum);
        input.value = '';
    } else {
        showToast(`请输入 1-${maxPage} 之间的页码`);
        input.value = '';
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

/**
 * Show toast notification
 */
function showToast(message, duration = 2000) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Toggle contacted state (localStorage)
 */
function toggleContacted(companyId, buttonElement) {
    const key = 'tranotra_leads_contacted_companies';
    const contactedStr = localStorage.getItem(key) || '{}';
    const contacted = JSON.parse(contactedStr);

    if (contacted[companyId]) {
        delete contacted[companyId];
    } else {
        contacted[companyId] = {
            contacted: true,
            timestamp: new Date().toISOString()
        };
    }

    localStorage.setItem(key, JSON.stringify(contacted));

    // Update button UI
    if (buttonElement) {
        if (contacted[companyId]) {
            buttonElement.classList.add('active');
            buttonElement.textContent = '✗ Unmark';
        } else {
            buttonElement.classList.remove('active');
            buttonElement.textContent = '✓ Mark as Contacted';
        }
    }
}

/**
 * Open note modal
 */
function openNoteModal(companyId) {
    const key = `tranotra_leads_notes_${companyId}`;
    const existingNote = localStorage.getItem(key) || '';

    const modal = document.createElement('div');
    modal.className = 'note-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>添加备注</h3>
            <textarea placeholder="输入您的备注..." maxlength="500">${escapeHtml(existingNote)}</textarea>
            <div class="modal-actions">
                <button class="btn-save">Save</button>
                <button class="btn-cancel">Cancel</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Focus on textarea
    setTimeout(() => {
        modal.querySelector('textarea').focus();
    }, 100);

    // Save button handler
    modal.querySelector('.btn-save').addEventListener('click', () => {
        const noteText = modal.querySelector('textarea').value;
        localStorage.setItem(key, noteText);
        modal.parentNode.removeChild(modal);
        showToast('备注已保存', 2000);
    });

    // Cancel button handler
    modal.querySelector('.btn-cancel').addEventListener('click', () => {
        modal.parentNode.removeChild(modal);
    });

    // Close on Escape key
    const escapeHandler = (e) => {
        if (e.key === 'Escape') {
            modal.parentNode.removeChild(modal);
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);
}

/**
 * Setup keyboard navigation for view toggle buttons
 * Uses event delegation to avoid duplicate listener registration
 */
function setupViewToggleKeyboard() {
    // Only set up delegation once
    if (currentState._keyboardNavSetup) {
        return;
    }

    const viewToggleContainer = document.querySelector('.view-toggle');
    if (!viewToggleContainer) return;

    // Use event delegation on parent container instead of adding listeners to each button
    viewToggleContainer.addEventListener('keydown', (e) => {
        const btn = e.target;
        if (!btn.classList.contains('view-btn')) return;

        const viewBtns = Array.from(viewToggleContainer.querySelectorAll('.view-btn'));
        const index = viewBtns.indexOf(btn);

        // Allow Enter and Space to activate the button
        if ((e.key === 'Enter' || e.key === ' ') && !btn.disabled) {
            e.preventDefault();
            btn.click();
        }
        // Allow arrow keys to navigate between buttons
        if (e.key === 'ArrowRight' && index < viewBtns.length - 1) {
            e.preventDefault();
            viewBtns[index + 1].focus();
        }
        if (e.key === 'ArrowLeft' && index > 0) {
            e.preventDefault();
            viewBtns[index - 1].focus();
        }
    });

    currentState._keyboardNavSetup = true;
}

/**
 * Global keyboard navigation handler for card/table views
 * Avoids interfering with form inputs and other interactive elements
 */
document.addEventListener('keydown', (e) => {
    const container = document.getElementById('results-container');
    if (!container || !currentState.companies.length) return;

    // Don't intercept keyboard events on form inputs
    const activeElement = document.activeElement;
    if (activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.tagName === 'SELECT' ||
        activeElement.contentEditable === 'true'
    )) {
        return;
    }

    if (currentState.view === 'card') {
        // Arrow down: scroll to next card
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            // Calculate scroll amount based on viewport or estimated card height
            const cardView = container.querySelector('.card-view');
            const cardHeight = cardView ? cardView.querySelector('.company-card')?.offsetHeight || 350 : 350;
            const scrollAmount = Math.max(cardHeight, 200);
            window.scrollBy(0, scrollAmount);
        }
        // Arrow up: scroll to previous card
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            const cardView = container.querySelector('.card-view');
            const cardHeight = cardView ? cardView.querySelector('.company-card')?.offsetHeight || 350 : 350;
            const scrollAmount = Math.max(cardHeight, 200);
            window.scrollBy(0, -scrollAmount);
        }
    } else if (currentState.view === 'table') {
        const rows = container.querySelectorAll('.data-row');
        if (!rows || rows.length === 0) return;

        // Find currently selected or focused row
        let currentRowIndex = Array.from(rows).findIndex(row =>
            row.classList.contains('selected') || document.activeElement === row
        );

        if (currentRowIndex === -1) currentRowIndex = 0;

        // Arrow down: move to next row
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const nextIndex = Math.min(currentRowIndex + 1, rows.length - 1);
            if (rows[nextIndex]) {
                rows[nextIndex].focus();
                rows[nextIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
        // Arrow up: move to previous row
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            const prevIndex = Math.max(currentRowIndex - 1, 0);
            if (rows[prevIndex]) {
                rows[prevIndex].focus();
                rows[prevIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
    }
});
