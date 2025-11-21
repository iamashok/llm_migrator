// Main application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const scanBtn = document.getElementById('scanBtn');
    const demoBtn = document.getElementById('demoBtn');
    const githubScanBtn = document.getElementById('githubScanBtn');
    const scanPath = document.getElementById('scanPath');
    const githubUrl = document.getElementById('githubUrl');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const error = document.getElementById('error');

    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');

            // Remove active class from all tabs
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Add active class to clicked tab
            this.classList.add('active');
            document.getElementById(tabName + 'Tab').classList.add('active');
        });
    });

    // Example repo buttons
    const exampleBtns = document.querySelectorAll('.example-btn');
    exampleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const url = this.getAttribute('data-url');
            githubUrl.value = url;
            githubScanBtn.click();
        });
    });

    scanBtn.addEventListener('click', function() {
        const path = scanPath.value.trim();
        if (!path) {
            showError('Please enter a path to scan');
            return;
        }
        scanDirectory(path);
    });

    demoBtn.addEventListener('click', function() {
        runDemo();
    });

    githubScanBtn.addEventListener('click', function() {
        const url = githubUrl.value.trim();
        if (!url) {
            showError('Please enter a GitHub repository URL');
            return;
        }
        scanGithubRepo(url);
    });

    scanPath.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            scanBtn.click();
        }
    });

    githubUrl.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            githubScanBtn.click();
        }
    });

    function scanDirectory(path) {
        showLoading();

        fetch('/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: path })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                displayResults(data);
            }
        })
        .catch(err => {
            showError('Error scanning directory: ' + err.message);
        });
    }

    function runDemo() {
        showLoading();

        fetch('/demo')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                displayResults(data);
            }
        })
        .catch(err => {
            showError('Error running demo: ' + err.message);
        });
    }

    function scanGithubRepo(url) {
        showLoading();
        document.querySelector('#loading p').textContent = 'Cloning and scanning GitHub repository...';

        fetch('/scan-github', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: url })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                displayResults(data);
            }
        })
        .catch(err => {
            showError('Error scanning GitHub repository: ' + err.message);
        })
        .finally(() => {
            document.querySelector('#loading p').textContent = 'Scanning codebase...';
        });
    }

    function showLoading() {
        loading.classList.remove('hidden');
        results.classList.add('hidden');
        error.classList.add('hidden');
    }

    function showError(message) {
        loading.classList.add('hidden');
        results.classList.add('hidden');
        error.classList.remove('hidden');
        document.getElementById('errorMessage').textContent = message;
    }

    function displayResults(data) {
        loading.classList.add('hidden');
        error.classList.add('hidden');
        results.classList.remove('hidden');

        // Update summary stats
        document.getElementById('totalCalls').textContent = data.summary.total_calls;
        document.getElementById('filesAffected').textContent = data.summary.files_affected;
        document.getElementById('savings').textContent = '$' + data.cost_savings.savings;
        document.getElementById('effort').textContent = data.effort_estimate + ' min';

        // Update cost comparison
        document.getElementById('openaiCost').textContent = '$' + data.cost_savings.openai_cost + '/mo';
        document.getElementById('mistralCost').textContent = '$' + data.cost_savings.mistral_cost + '/mo';
        document.getElementById('savingsPercent').textContent = data.cost_savings.percentage + '%';

        const mistralBarFill = document.getElementById('mistralBarFill');
        mistralBarFill.style.width = '0%';
        setTimeout(() => {
            mistralBarFill.style.width = (100 - data.cost_savings.percentage) + '%';
        }, 100);

        // Display patterns
        displayPatterns(data.summary.patterns);

        // Display examples
        displayExamples(data.examples);

        // Display files
        displayFiles(data.files);

        // Scroll to results
        results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function displayPatterns(patterns) {
        const patternsList = document.getElementById('patternsList');
        patternsList.innerHTML = '';

        for (const [pattern, count] of Object.entries(patterns)) {
            const badge = document.createElement('div');
            badge.className = 'pattern-badge';
            badge.innerHTML = `
                <span>${pattern}</span>
                <span class="pattern-count">${count} call${count !== 1 ? 's' : ''}</span>
            `;
            patternsList.appendChild(badge);
        }
    }

    function displayExamples(examples) {
        const examplesList = document.getElementById('examplesList');
        examplesList.innerHTML = '';

        examples.forEach(example => {
            const card = document.createElement('div');
            card.className = 'example-card';

            const keyChangesList = example.key_changes.map(change =>
                `<li>${escapeHtml(change)}</li>`
            ).join('');

            card.innerHTML = `
                <div class="example-header">
                    <span class="example-title">${escapeHtml(example.type)}</span>
                    <span class="difficulty-badge">Effort: ${escapeHtml(example.difficulty)}</span>
                </div>
                <div class="code-comparison">
                    <div class="code-panel">
                        <h4>Before (OpenAI)</h4>
                        <pre>${escapeHtml(example.before)}</pre>
                    </div>
                    <div class="code-panel">
                        <h4>After (Mistral)</h4>
                        <pre>${escapeHtml(example.after)}</pre>
                    </div>
                </div>
                <div class="key-changes">
                    <h4>Key Changes:</h4>
                    <ul>${keyChangesList}</ul>
                </div>
            `;
            examplesList.appendChild(card);
        });
    }

    function displayFiles(files) {
        const filesList = document.getElementById('filesList');
        filesList.innerHTML = '';

        if (Object.keys(files).length === 0) {
            filesList.innerHTML = '<p style="text-align: center; color: #666;">No files detected with OpenAI usage</p>';
            return;
        }

        for (const [filename, locations] of Object.entries(files)) {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';

            const locationBadges = locations.map(loc =>
                `<span class="location-badge">Line ${loc.line}: ${escapeHtml(loc.pattern_type)}</span>`
            ).join('');

            fileItem.innerHTML = `
                <div class="file-name">📄 ${escapeHtml(filename)}</div>
                <div class="file-locations">${locationBadges}</div>
            `;
            filesList.appendChild(fileItem);
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
