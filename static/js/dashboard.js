/**
 * Dashboard Analytics - Client-side logic for metrics display
 */

/**
 * Get selected period from dropdown
 * @returns {number} Number of days (7, 14, or 30)
 */
function getSelectedPeriod() {
    const period = document.getElementById('period-filter').value;
    return parseInt(period, 10);
}

/**
 * Update dashboard title with selected period
 * @param {number} days - Number of days
 */
function updateDashboardTitle(days) {
    const periodMap = {
        7: '最近7天',
        14: '最近14天',
        30: '最近30天'
    };
    const title = `系统运行效率仪表板 (${periodMap[days]})`;
    document.getElementById('dashboard-title').textContent = title;
}

/**
 * Format number with thousands separator
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(num) {
    if (num === null || num === undefined) return '--';
    if (num === 0) return '0';
    return num.toLocaleString('en-US');
}

/**
 * Format percentage value
 * @param {number} value - Decimal value (0-100)
 * @returns {string} Formatted percentage
 */
function formatPercentage(value) {
    if (value === null || value === undefined) return '--';
    return value.toFixed(1) + '%';
}

/**
 * Format decimal value
 * @param {number} value - Decimal value
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted decimal
 */
function formatDecimal(value, decimals = 1) {
    if (value === null || value === undefined) return '--';
    return value.toFixed(decimals);
}

/**
 * Determine trend direction and CSS class
 * @param {number} value - Trend value (can be negative)
 * @returns {object} {arrow, cssClass}
 */
function getTrendInfo(value) {
    if (value === null || value === undefined || value === 0) {
        return { arrow: '—', cssClass: 'neutral' };
    }
    if (value > 0) {
        return { arrow: '↑', cssClass: 'positive' };
    }
    return { arrow: '↓', cssClass: 'negative' };
}

/**
 * Render metric card HTML
 * @param {string} name - Metric name (Chinese)
 * @param {*} value - Metric value
 * @param {string} format - Format type: 'number', 'percentage', 'decimal'
 * @param {*} trend - Trend value (optional)
 * @param {boolean} hasData - Whether data exists
 * @returns {string} HTML for metric card
 */
function renderMetricCard(name, value, format, trend = null, hasData = true) {
    let displayValue;

    if (!hasData || value === null) {
        displayValue = '—';
    } else {
        switch (format) {
            case 'percentage':
                displayValue = formatPercentage(value);
                break;
            case 'decimal':
                displayValue = formatDecimal(value);
                break;
            case 'number':
            default:
                displayValue = formatNumber(value);
                break;
        }
    }

    let trendHtml = '';
    if (trend !== null && trend !== undefined) {
        const trendInfo = getTrendInfo(trend);
        const trendClass = Math.abs(trend) < 0.01 ? 'neutral' : trendInfo.cssClass;
        const absValue = Math.abs(trend).toFixed(1);
        trendHtml = `
            <div class="metric-trend">
                <span class="trend-arrow ${trendInfo.cssClass}">${trendInfo.arrow}</span>
                <span class="trend-value ${trendClass}">${absValue}%</span>
            </div>
        `;
    }

    const cardClass = !hasData ? 'metric-card no-data' : 'metric-card';
    const borderClass = trend !== null && trend !== undefined
        ? (trend > 0 ? 'positive' : trend < 0 ? 'negative' : 'neutral')
        : '';

    return `
        <div class="${cardClass} ${borderClass}">
            <div class="metric-label">${name}</div>
            <div class="metric-value${format === 'percentage' ? ' small' : ''}">${displayValue}</div>
            ${trendHtml}
        </div>
    `;
}

/**
 * Show loading spinner
 */
function showLoading() {
    document.getElementById('loading-spinner').classList.remove('d-none');
    document.getElementById('error-alert').classList.add('d-none');
    document.getElementById('no-data-message').classList.add('d-none');
    document.getElementById('metrics-container').innerHTML = '';
}

/**
 * Show error message
 * @param {string} message - Error message to display
 */
function showError(message) {
    document.getElementById('loading-spinner').classList.add('d-none');
    document.getElementById('error-alert').classList.remove('d-none');
    document.getElementById('error-message').textContent = message;
    document.getElementById('metrics-container').innerHTML = '';
}

/**
 * Show no data message
 */
function showNoData() {
    document.getElementById('loading-spinner').classList.add('d-none');
    document.getElementById('error-alert').classList.add('d-none');
    document.getElementById('no-data-message').classList.remove('d-none');

    // Still render empty metric cards
    const container = document.getElementById('metrics-container');
    container.innerHTML = `
        ${renderMetricCard('总搜索次数 (Total Searches)', 0, 'number', null, false)}
        ${renderMetricCard('新增公司总数 (Total Companies)', 0, 'number', null, false)}
        ${renderMetricCard('去重率 (Dedup Rate)', 0, 'percentage', null, false)}
        ${renderMetricCard('平均命中率 (Avg Hit Rate)', 0, 'decimal', null, false)}
        ${renderMetricCard('高分占比 (High-Score Rate)', 0, 'percentage', null, false)}
        ${renderMetricCard('日对日增长 (Day-on-Day)', 0, 'percentage', null, false)}
        ${renderMetricCard('周对周增长 (Week-on-Week)', 0, 'percentage', null, false)}
    `;
}

/**
 * Render metrics to dashboard
 * @param {object} metrics - Metrics object from API
 */
function renderMetrics(metrics) {
    const container = document.getElementById('metrics-container');
    const hasData = metrics && Object.values(metrics).some(v => v !== 0 && v !== null);

    if (!hasData) {
        showNoData();
        return;
    }

    container.innerHTML = `
        ${renderMetricCard('总搜索次数 (Total Searches)', metrics.total_searches, 'number', null, true)}
        ${renderMetricCard('新增公司总数 (Total Companies)', metrics.total_companies, 'number', null, true)}
        ${renderMetricCard('去重率 (Dedup Rate)', metrics.dedup_rate, 'percentage', null, true)}
        ${renderMetricCard('平均命中率 (Avg Hit Rate)', metrics.avg_hit_rate, 'decimal', null, true)}
        ${renderMetricCard('高分占比 (High-Score Rate)', metrics.high_score_rate, 'percentage', null, true)}
        ${renderMetricCard('日对日增长 (Day-on-Day)', metrics.day_on_day_growth, 'percentage', metrics.day_on_day_growth, true)}
        ${renderMetricCard('周对周增长 (Week-on-Week)', metrics.week_on_week_growth, 'percentage', metrics.week_on_week_growth, true)}
    `;

    document.getElementById('loading-spinner').classList.add('d-none');
    document.getElementById('error-alert').classList.add('d-none');
    document.getElementById('no-data-message').classList.add('d-none');
}

/**
 * Load dashboard metrics from API
 */
function loadDashboard() {
    const days = getSelectedPeriod();

    // Update title
    updateDashboardTitle(days);

    // Show loading spinner
    showLoading();

    // Fetch metrics from API
    const apiUrl = `/api/analytics/dashboard?days=${days}`;

    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data.success) {
                showError(data.error.message);
                console.error('API error:', data.error);
                return;
            }

            // Render metrics
            renderMetrics(data.data.metrics);
        })
        .catch(error => {
            const errorMsg = `数据加载失败: ${error.message}`;
            showError(errorMsg);
            console.error('Error loading dashboard:', error);
        });
}

/**
 * Initialize dashboard on page load
 */
function initDashboard() {
    // Listen for period filter changes
    const periodFilter = document.getElementById('period-filter');
    if (periodFilter) {
        periodFilter.addEventListener('change', loadDashboard);
    }

    // Load initial dashboard
    loadDashboard();
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}
