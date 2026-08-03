// Default sample code
const defaultCode = `import os

def CalculateAverage(numbers):
    total = sum(numbers)
    return total / len(numbers)   # Potential ZeroDivisionError

def load_config():
    # Hardcoded secret - security risk
    API_KEY = "sk-1234567890abcdef"
    return API_KEY

def process_data(data):
    result = []
    for i in range(len(data)):
        result.append(data[i] * 2)
    return result
`;

// Elements
const codeInput = document.getElementById('code-input');
const filePathInput = document.getElementById('file-path');
const charCount = document.getElementById('char-count');
const reviewBtn = document.getElementById('review-btn');
const clearBtn = document.getElementById('clear-btn');
const memoryToggle = document.getElementById('memory-toggle');
const globalStatusPanel = document.getElementById('global-status-panel');
const currentStageText = document.getElementById('current-stage');
const statusMessage = document.getElementById('status-message');
const mainSpinner = document.getElementById('main-spinner');
const findingsPanel = document.getElementById('findings-panel');
const findingsList = document.getElementById('findings-list');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toast-message');

let currentEventSource = null;

// Initialize
codeInput.value = defaultCode;
updateCharCount();

// Event Listeners
codeInput.addEventListener('input', updateCharCount);

clearBtn.addEventListener('click', () => {
    codeInput.value = '';
    filePathInput.value = 'src/main.py';
    updateCharCount();
});

reviewBtn.addEventListener('click', startReview);

function updateCharCount() {
    charCount.textContent = `${codeInput.value.length} chars`;
    if (codeInput.value.length > 5000) {
        charCount.style.color = 'var(--severity-medium)';
        charCount.textContent += ' (Warning: Large file)';
    } else {
        charCount.style.color = 'var(--text-muted)';
    }
}

function showError(msg) {
    toastMessage.textContent = msg;
    toast.classList.remove('hidden');
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 5000);
}

function resetUI() {
    ['StyleAgent', 'BugAgent', 'SecurityAgent'].forEach(agent => {
        setAgentStatus(agent, 'idle');
        document.getElementById(`progress-${agent}`).style.width = '0%';
    });
    findingsPanel.style.display = 'none';
    globalStatusPanel.style.display = 'block';
    findingsList.innerHTML = '';
}

function setAgentStatus(agent, state, msg = '') {
    const indicator = document.getElementById(`indicator-${agent}`);
    const statusText = document.getElementById(`status-${agent}`);
    
    indicator.className = `status-indicator ${state}`;
    
    if (state === 'idle') statusText.textContent = 'Idle';
    if (state === 'running') statusText.textContent = msg || 'Analyzing...';
    if (state === 'complete') statusText.textContent = 'Complete';
    if (state === 'error') statusText.textContent = 'Failed';
}

function updateAgentProgress(agent, iteration, confidence) {
    const statusText = document.getElementById(`status-${agent}`);
    const progressBar = document.getElementById(`progress-${agent}`);
    
    statusText.textContent = `Iteration ${iteration} (Conf: ${confidence.toFixed(2)})`;
    const percent = Math.min(100, Math.max(10, (confidence * 100)));
    progressBar.style.width = `${percent}%`;
}

function setGlobalStatus(stage, desc) {
    currentStageText.textContent = stage;
    statusMessage.textContent = desc;
}

async function startReview() {
    if (!codeInput.value.trim()) {
        showError("Please enter some code to review.");
        return;
    }

    if (currentEventSource) {
        currentEventSource.close();
    }

    resetUI();
    reviewBtn.disabled = true;
    mainSpinner.style.display = 'block';
    setGlobalStatus("Submitting Task", "Sending request to MACR API...");

    try {
        const res = await fetch('/api/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_path: filePathInput.value || 'unknown.py',
                code_content: codeInput.value,
                use_memory: memoryToggle.checked
            })
        });

        if (!res.ok) {
            throw new Error(`API Error: ${res.statusText}`);
        }

        const data = await res.json();
        connectSSE(data.job_id);

    } catch (e) {
        showError(e.message);
        reviewBtn.disabled = false;
        mainSpinner.style.display = 'none';
        setGlobalStatus("Error", e.message);
    }
}

function connectSSE(jobId) {
    currentEventSource = new EventSource(`/api/stream/${jobId}`);

    currentEventSource.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        const event = msg.event;
        const data = msg.data;

        if (event === 'review_status') {
            if (data.status === 'initializing') setGlobalStatus("Initializing", "Setting up review environment...");
            if (data.status === 'retrieving_memory') setGlobalStatus("Memory Retrieval", "Searching FAISS for similar past reviews...");
            if (data.status === 'analyzing') setGlobalStatus("Agent Analysis", "Agents are analyzing the code in parallel...");
            if (data.status === 'consensus') setGlobalStatus("Consensus Engine", "Merging conflicting findings semantically...");
        } 
        else if (event === 'memory_context') {
            setGlobalStatus("Memory Context", `Loaded ${data.count} similar past reviews for context.`);
        }
        else if (event === 'agent_status') {
            setAgentStatus(data.agent, data.status === 'starting' ? 'running' : data.status);
        }
        else if (event === 'agent_progress') {
            updateAgentProgress(data.agent, data.iteration, data.confidence);
        }
        else if (event === 'agent_error') {
            setAgentStatus(data.agent, 'error');
            showError(`${data.agent} failed: ${data.error}`);
        }
        else if (event === 'review_error') {
            showError(`Review failed: ${data.error}`);
            reviewBtn.disabled = false;
            mainSpinner.style.display = 'none';
            setGlobalStatus("Review Failed", data.error);
            currentEventSource.close();
        }
        else if (event === 'review_complete') {
            renderFinalReport(data);
            reviewBtn.disabled = false;
            mainSpinner.style.display = 'none';
            currentEventSource.close();
        }
    };

    currentEventSource.onerror = (e) => {
        console.error("SSE Error", e);
        showError("Lost connection to server stream.");
        reviewBtn.disabled = false;
        mainSpinner.style.display = 'none';
        currentEventSource.close();
    };
}

function renderFinalReport(report) {
    globalStatusPanel.style.display = 'none';
    findingsPanel.style.display = 'block';
    
    // Set metrics
    const conf = report.total_confidence !== undefined ? report.total_confidence : 0;
    const agree = report.agent_agreement !== undefined ? report.agent_agreement : 0;
    document.getElementById('metric-confidence').textContent = `${(conf * 100).toFixed(1)}% Confidence`;
    document.getElementById('metric-ratio').textContent = `${(agree * 100).toFixed(1)}% Agreement`;
    
    findingsList.innerHTML = '';
    
    if (report.findings.length === 0) {
        findingsList.innerHTML = `<div class="text-muted" style="text-align: center; padding: 2rem;">No issues found! Your code looks great.</div>`;
        return;
    }

    report.findings.forEach((f, idx) => {
        const card = document.createElement('div');
        card.className = `finding-card severity-${f.severity}`;
        
        let categoryIcon = 'fa-bug';
        if (f.category === 'style') categoryIcon = 'fa-paint-brush';
        if (f.category === 'security') categoryIcon = 'fa-shield-alt';

        // Sometimes the model embeds the rationale inside the explanation with a prefix
        let explanation = f.explanation;
        let rationaleHTML = '';
        if (explanation.includes('[Consensus Rationale]')) {
            const parts = explanation.split('[Consensus Rationale]');
            explanation = parts[0];
            rationaleHTML = `<div class="finding-rationale"><i class="fas fa-info-circle"></i> Consensus Rationale: ${parts[1].replace(/^:/, '').trim()}</div>`;
        } else if (f.resolution_rationale) {
            rationaleHTML = `<div class="finding-rationale"><i class="fas fa-info-circle"></i> Consensus Rationale: ${f.resolution_rationale}</div>`;
        }

        card.innerHTML = `
            <div class="finding-header">
                <div class="finding-title">
                    <i class="fas ${categoryIcon}"></i> ${idx + 1}. [${f.category.toUpperCase()}] ${f.description}
                </div>
            </div>
            <div class="finding-meta" style="margin-bottom: 8px;">
                <span><i class="fas fa-exclamation-triangle"></i> ${f.severity}</span>
                <span><i class="fas fa-code-branch"></i> ${f.code_location}</span>
                <span><i class="fas fa-robot"></i> ${f.agent_name}</span>
                <span><i class="fas fa-chart-line"></i> Conf: ${f.confidence.toFixed(2)}</span>
            </div>
            <div class="finding-desc">${explanation}</div>
            ${rationaleHTML}
        `;
        
        findingsList.appendChild(card);
    });
}
