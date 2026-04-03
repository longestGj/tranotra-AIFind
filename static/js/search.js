// Search form interaction and API communication
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const searchBtn = document.getElementById('searchBtn');
    const countdownText = document.getElementById('countdownText');
    const errorMsg = document.getElementById('errorMsg');
    const successMsg = document.getElementById('successMsg');
    const btnText = document.getElementById('btnText');

    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const country = document.getElementById('country').value;
        const keyword = document.getElementById('keyword').value;

        if (!country || !keyword) {
            showError('请填写国家和关键词');
            return;
        }

        // Hide previous messages
        errorMsg.style.display = 'none';
        successMsg.style.display = 'none';

        // Disable button and start countdown
        searchBtn.disabled = true;
        let countdown = 2;

        const countdownInterval = setInterval(function() {
            if (countdown > 0) {
                countdownText.textContent = `准备搜索 (${countdown}秒延迟)`;
                countdownText.style.display = 'block';
                countdown--;
            } else {
                clearInterval(countdownInterval);
                countdownText.style.display = 'none';
                performSearch(country, keyword);
            }
        }, 1000);

        // Start countdown immediately
        countdownText.textContent = `准备搜索 (2秒延迟)`;
        countdownText.style.display = 'block';
    });

    function performSearch(country, keyword) {
        // Show loading state
        btnText.innerHTML = '<span class="spinner"></span>搜索中...';

        fetch('/api/search/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `country=${encodeURIComponent(country)}&keyword=${encodeURIComponent(keyword)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showSuccess('搜索成功，正在处理结果...');
                // In a real app, would redirect to results page or load results dynamically
            } else if (data.status === 'timeout') {
                showError('搜索超时，请重试');
                searchBtn.disabled = false;
                btnText.textContent = '🔍 搜索';
            } else {
                showError(data.message || '搜索失败，请稍后重试');
                searchBtn.disabled = false;
                btnText.textContent = '🔍 搜索';
            }
        })
        .catch(error => {
            showError('搜索失败，请稍后重试');
            searchBtn.disabled = false;
            btnText.textContent = '🔍 搜索';
        });
    }

    function showError(message) {
        errorMsg.textContent = message;
        errorMsg.style.display = 'block';
        searchBtn.disabled = false;
        btnText.textContent = '🔍 搜索';
    }

    function showSuccess(message) {
        successMsg.textContent = message;
        successMsg.style.display = 'block';
    }
});
