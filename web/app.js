/**
 * AI Model Manager - Standard Professional Python Web Server Dashboard JS
 */

document.addEventListener('DOMContentLoaded', () => {
    // Navigation Tabs
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('page-title');

    const titles = {
        'dashboard': 'Dashboard & Gateway Status',
        'endpoints': 'Standard Professional API Endpoints',
        'playground': 'AI Model Playground & Tester',
        'providers': 'Provider Settings & Config',
        'ports': 'Port Conflict Diagnostics & Force Controls',
        'setup': 'Standard Professional Setup Guide'
    };

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.dataset.tab;
            navItems.forEach(n => n.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            item.classList.add('active');
            const targetEl = document.getElementById('tab-' + targetTab);
            if (targetEl) targetEl.classList.add('active');
            if (pageTitle && titles[targetTab]) pageTitle.innerText = titles[targetTab];
        });
    });

    const currentPort = window.location.port || '11434';
    document.getElementById('current-port').innerText = currentPort;
    const quickPort = document.getElementById('quick-port');
    if (quickPort) quickPort.value = currentPort;

    // Update URLs in UI based on active port
    updatePortUrls(currentPort);

    // Initial load
    loadDashboardData();
    loadConfig();

    // Refresh Status
    const btnRefresh = document.getElementById('btn-refresh-status');
    if (btnRefresh) {
        btnRefresh.addEventListener('click', () => {
            loadDashboardData();
        });
    }

    // Force Start / Restart Gateway on new port
    const btnForceStart = document.getElementById('btn-force-start');
    if (btnForceStart && quickPort) {
        btnForceStart.addEventListener('click', async () => {
            const newPort = quickPort.value;
            btnForceStart.innerText = '⏳ Restarting...';
            try {
                const res = await fetch(`/v1/gateway/restart?port=${newPort}&force=1`, { method: 'POST' });
                const data = await res.json();
                alert(data.message || 'Gateway restarting on port ' + newPort);
                setTimeout(() => {
                    window.location.href = `http://127.0.0.1:${newPort}/`;
                }, 1000);
            } catch (err) {
                alert('Error restarting gateway: ' + err.message);
            } finally {
                btnForceStart.innerText = '⚡ Force Port & Restart';
            }
        });
    }

    // Model Playground Send Prompt
    const btnSendPrompt = document.getElementById('btn-send-prompt');
    if (btnSendPrompt) {
        btnSendPrompt.addEventListener('click', async () => {
            const provider = document.getElementById('play-provider').value;
            const model = document.getElementById('play-model').value;
            const prompt = document.getElementById('play-prompt').value;
            const max_tokens = parseInt(document.getElementById('play-max-tokens').value);
            const temperature = parseFloat(document.getElementById('play-temp').value);
            const outputBox = document.getElementById('play-output');

            btnSendPrompt.innerText = '⏳ Generating Response...';
            outputBox.innerText = 'Connecting to Gateway...';
            const startTime = Date.now();

            try {
                const queryParam = provider ? `?provider=${encodeURIComponent(provider)}` : '';
                const res = await fetch(`/v1/chat/completions${queryParam}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: model,
                        messages: [{ role: 'user', content: prompt }],
                        max_tokens: max_tokens,
                        temperature: temperature
                    })
                });

                const latency = Date.now() - startTime;
                document.getElementById('response-meta').innerText = `Latency: ${latency} ms`;

                if (res.ok) {
                    const data = await res.json();
                    const reply = data.choices && data.choices[0] && data.choices[0].message ? data.choices[0].message.content : JSON.stringify(data, null, 2);
                    outputBox.innerText = reply;
                } else {
                    const errData = await res.json();
                    outputBox.innerText = 'Error (' + res.status + '): ' + JSON.stringify(errData, null, 2);
                }
            } catch (e) {
                outputBox.innerText = 'Connection Error: ' + e.message;
            } finally {
                btnSendPrompt.innerText = '🚀 Send Prompt';
            }
        });
    }

    // Port Diagnostics
    const btnScanPort = document.getElementById('btn-scan-port');
    const btnKillPort = document.getElementById('btn-kill-port');
    const forcePortInput = document.getElementById('force-port-input');
    const portResult = document.getElementById('port-status-result');

    if (btnScanPort && forcePortInput) {
        btnScanPort.addEventListener('click', async () => {
            const port = forcePortInput.value;
            portResult.innerText = `Scanning port ${port}...`;
            try {
                const res = await fetch(`/v1/ports/scan?port=${port}`);
                const data = await res.json();
                if (data.in_use) {
                    portResult.innerHTML = `<span style="color: #ef4444; font-weight: bold;">LOCKED</span> - Port ${port} is bound by PID <strong>${data.pid || 'Unknown'}</strong> (${data.process || 'Process'}).`;
                } else {
                    portResult.innerHTML = `<span style="color: #10b981; font-weight: bold;">FREE</span> - Port ${port} is available for binding.`;
                }
            } catch (e) {
                portResult.innerText = 'Error scanning port: ' + e.message;
            }
        });
    }

    if (btnKillPort && forcePortInput) {
        btnKillPort.addEventListener('click', async () => {
            const port = forcePortInput.value;
            if (!confirm(`Force kill process on port ${port}?`)) return;
            portResult.innerText = `Killing process on port ${port}...`;
            try {
                const res = await fetch(`/v1/ports/kill?port=${port}`, { method: 'POST' });
                const data = await res.json();
                portResult.innerText = data.message || `Process on port ${port} terminated.`;
            } catch (e) {
                portResult.innerText = 'Error killing process: ' + e.message;
            }
        });
    }

    // Save Config
    const btnSaveConfig = document.getElementById('btn-save-config');
    const btnReloadConfig = document.getElementById('btn-reload-config');
    const configRaw = document.getElementById('config-raw');

    if (btnSaveConfig && configRaw) {
        btnSaveConfig.addEventListener('click', async () => {
            try {
                const parsed = JSON.parse(configRaw.value);
                const res = await fetch('/v1/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(parsed)
                });
                const data = await res.json();
                alert(data.message || 'Configuration saved successfully!');
                loadDashboardData();
            } catch (err) {
                alert('Invalid JSON: ' + err.message);
            }
        });
    }

    if (btnReloadConfig) {
        btnReloadConfig.addEventListener('click', loadConfig);
    }
});

function updatePortUrls(port) {
    const host = window.location.hostname || '127.0.0.1';
    const baseUrl = `http://${host}:${port}`;

    document.getElementById('dashboard-endpoint').innerText = `${baseUrl}/v1`;
    document.getElementById('ep-chat').innerText = `${baseUrl}/v1/chat/completions`;
    document.getElementById('ep-messages').innerText = `${baseUrl}/v1/messages`;
    document.getElementById('ep-models').innerText = `${baseUrl}/v1/models`;
    document.getElementById('ep-health').innerText = `${baseUrl}/v1/health`;
    document.getElementById('ep-openapi').innerText = `${baseUrl}/v1/openapi.json`;

    document.querySelectorAll('.guide-port').forEach(el => el.innerText = port);
}

async function loadDashboardData() {
    try {
        const res = await fetch('/v1/health');
        if (res.ok) {
            const data = await res.json();
            document.getElementById('status-dot').style.backgroundColor = '#10b981';
            document.getElementById('dash-provider-count').innerText = `${data.providers_count || 0} Providers`;
            
            // Populate Providers Table
            populateProvidersTable(data.providers || []);
        } else {
            document.getElementById('status-dot').style.backgroundColor = '#ef4444';
        }
    } catch (e) {
        document.getElementById('status-dot').style.backgroundColor = '#ef4444';
    }
}

function populateProvidersTable(providers) {
    const tbody = document.getElementById('providers-table-body');
    const select = document.getElementById('play-provider');

    if (!providers || providers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No providers configured in config.json.</td></tr>';
        return;
    }

    tbody.innerHTML = providers.map(p => `
        <tr>
            <td class="font-bold">${escapeHtml(p.name || '')}</td>
            <td><span class="badge badge-purple">${escapeHtml((p.format || 'openai').toUpperCase())}</span></td>
            <td class="code-text">${escapeHtml(p.base_url || '')}</td>
            <td class="code-text">${escapeHtml(p.default_model || 'N/A')}</td>
            <td><span class="badge badge-success">Ready</span></td>
        </tr>
    `).join('');

    select.innerHTML = '<option value="">Auto Select First</option>' + providers.map(p => `
        <option value="${escapeHtml(p.name)}">${escapeHtml(p.name)} (${escapeHtml(p.format || 'openai')})</option>
    `).join('');
}

async function loadConfig() {
    const configRaw = document.getElementById('config-raw');
    if (!configRaw) return;
    try {
        const res = await fetch('/v1/config');
        if (res.ok) {
            const data = await res.json();
            configRaw.value = JSON.stringify(data, null, 2);
        }
    } catch (e) {
        configRaw.value = 'Failed to load config: ' + e.message;
    }
}

function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard:\n' + text);
    });
}

function escapeHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
