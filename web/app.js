/**
 * AIPI — AI Protocol Interface: Standard Professional Gateway & Web Dashboard
 * Developed by gnonymous.
 */
var adminToken = localStorage.getItem('aimm_admin_token') || '';

document.addEventListener('DOMContentLoaded', () => {
    // Navigation Tabs
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('page-title');

    const titles = {
        'dashboard': 'Dashboard & Gateway Status',
        'profilers': '🎛️ Auto-Profilers & Token Failover Engine',
        'ide-setup': '1-Click IDE Auto-Configurator',
        'vkeys': 'Virtual API Keys & Multi-Tenant Access',
        'analytics': 'Financial Analytics & Performance Intelligence',
        'endpoints': 'Standard Professional API Endpoints',
        'playground': 'AI Model Arena & Tester',
        'provider-hub': '⚡ Provider Hub (OAuth & API Keys)',
        'providers': 'Provider Settings & Config',
        'ports': 'Port Conflict Diagnostics & Force Controls',
        'admin': 'Admin, License & Team Edition',
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

            if (targetTab === 'profilers') loadProfilers();
            if (targetTab === 'ide-setup') loadIdes();
            if (targetTab === 'vkeys') loadVirtualKeys();
            if (targetTab === 'analytics') loadAnalytics();
            if (targetTab === 'provider-hub') { if (typeof initProviderHub === 'function') initProviderHub(); }
            if (targetTab === 'admin') { loadLicenseStatus(); loadOidcStatus(); }
        });
    });

    const currentPort = window.location.port || '11434';
    const cpEl = document.getElementById('current-port');
    if (cpEl) cpEl.innerText = currentPort;
    const quickPort = document.getElementById('quick-port');
    if (quickPort) quickPort.value = currentPort;

    // Update URLs in UI based on active port
    if (typeof updatePortUrls === 'function') updatePortUrls(currentPort);

    // Virtual Key Creation Listener
    const btnCreateVKey = document.getElementById('btn-create-vkey');
    if (btnCreateVKey) btnCreateVKey.addEventListener('click', createVirtualKey);

    // Clear Cache Listener
    const btnClearCache = document.getElementById('btn-clear-cache');
    if (btnClearCache) btnClearCache.addEventListener('click', clearPromptCache);

    // Admin tab listeners
    const btnAdminLogin = document.getElementById('btn-admin-login');
    if (btnAdminLogin) btnAdminLogin.addEventListener('click', adminLogin);
    const btnAdminLogout = document.getElementById('btn-admin-logout');
    if (btnAdminLogout) btnAdminLogout.addEventListener('click', adminLogout);
    const btnCreateUser = document.getElementById('btn-create-user');
    if (btnCreateUser) btnCreateUser.addEventListener('click', adminCreateUser);
    const btnActivateLicense = document.getElementById('btn-activate-license');
    if (btnActivateLicense) btnActivateLicense.addEventListener('click', activateLicense);
    const btnExportCsv = document.getElementById('btn-export-csv');
    if (btnExportCsv) btnExportCsv.addEventListener('click', () => exportReport('csv'));
    const btnExportJson = document.getElementById('btn-export-json');
    if (btnExportJson) btnExportJson.addEventListener('click', () => exportReport('json'));
    const btnSaveOidc = document.getElementById('btn-save-oidc');
    if (btnSaveOidc) btnSaveOidc.addEventListener('click', saveOidcConfig);
    const btnChangePass = document.getElementById('btn-change-password');
    if (btnChangePass) btnChangePass.addEventListener('click', adminChangePassword);

    // Privacy & Stealth toggles
    const btnTogglePii = document.getElementById('btn-toggle-pii');
    if (btnTogglePii) btnTogglePii.addEventListener('click', togglePii);
    const btnToggleStealth = document.getElementById('btn-toggle-stealth');
    if (btnToggleStealth) btnToggleStealth.addEventListener('click', toggleStealth);

    // IDE Setup listener
    const btnRescanIdes = document.getElementById('btn-rescan-ides');
    if (btnRescanIdes) btnRescanIdes.addEventListener('click', loadIdes);

    // Battle Arena listeners
    const btnModeSingle = document.getElementById('btn-mode-single');
    const btnModeArena = document.getElementById('btn-mode-arena');
    if (btnModeSingle && btnModeArena) {
        btnModeSingle.addEventListener('click', () => {
            btnModeSingle.className = 'btn btn-sm btn-primary';
            btnModeArena.className = 'btn btn-sm btn-outline';
            const sm = document.getElementById('playground-single-mode');
            const am = document.getElementById('playground-arena-mode');
            if (sm) sm.style.display = 'flex';
            if (am) am.style.display = 'none';
        });
        btnModeArena.addEventListener('click', () => {
            btnModeSingle.className = 'btn btn-sm btn-outline';
            btnModeArena.className = 'btn btn-sm btn-primary';
            const sm = document.getElementById('playground-single-mode');
            const am = document.getElementById('playground-arena-mode');
            if (sm) sm.style.display = 'none';
            if (am) am.style.display = 'block';
        });
    }
    const btnRunArena = document.getElementById('btn-run-arena');
    if (btnRunArena) btnRunArena.addEventListener('click', runBattleArena);

    // Auto-restore admin session
    if (adminToken) {
        const als = document.getElementById('admin-login-status');
        if (als) als.innerText = 'Session token found — click Login to re-authenticate.';
        const alo = document.getElementById('btn-admin-logout');
        if (alo) alo.style.display = 'inline-block';
    }

    // Initial load
    loadDashboardData();
    loadConfig();
    loadModelList();
    loadMgmtProviders();
    initPresetsDropdown();
    loadPrivacyStatus();
    loadIdes();

    // Preset dropdown selection handler
    const presetSel = document.getElementById('pf-preset-select');
    if (presetSel) {
        presetSel.addEventListener('change', () => {
            const val = presetSel.value;
            if (!val) return;
            const presets = window.PROVIDER_PRESETS || [];
            const p = presets.find(item => item.name === val);
            if (p) {
                const pn = document.getElementById('pf-name'); if (pn) pn.value = p.name || '';
                const pf = document.getElementById('pf-format'); if (pf) pf.value = p.format || 'auto';
                const pb = document.getElementById('pf-base'); if (pb) pb.value = p.base_url || '';
                const pm = document.getElementById('pf-model'); if (pm) pm.value = p.default_model || '';
                const pno = document.getElementById('pf-notes'); if (pno) pno.value = p.notes || '';
                const keyInput = document.getElementById('pf-key');
                if (keyInput) keyInput.focus();
            }
        });
    }

    // Provider management
    const btnAddProvider = document.getElementById('btn-add-provider');
    if (btnAddProvider) btnAddProvider.addEventListener('click', () => openProviderForm(null));

    const btnReloadProviders = document.getElementById('btn-reload-providers');
    if (btnReloadProviders) btnReloadProviders.addEventListener('click', loadMgmtProviders);

    const btnProviderSave = document.getElementById('btn-provider-save');
    if (btnProviderSave) btnProviderSave.addEventListener('click', saveProvider);

    // Populate model suggestions + quota panel when a provider is selected
    const playProvider = document.getElementById('play-provider');
    if (playProvider) {
        playProvider.addEventListener('change', () => {
            loadModelList();
            const selectedVal = playProvider.value || '';
            const isAntigravity = selectedVal.toLowerCase().includes('antigravity');
            const quotaPanel = document.getElementById('agy-quota-panel');
            if (quotaPanel) {
                if (isAntigravity) {
                    quotaPanel.style.display = 'block';
                    loadAntigravityQuota();
                } else {
                    quotaPanel.style.display = 'none';
                }
            }
        });
    }

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
            const thinking_budget = parseInt(document.getElementById('play-thinking')?.value || 0);
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
                        temperature: temperature,
                        stream: true,
                        thinking_budget: thinking_budget
                    })
                });

                if (res.ok && res.body) {
                    const reader = res.body.getReader();
                    const decoder = new TextDecoder('utf-8');
                    let accumulated = '';
                    let firstTokenTime = null;
                    outputBox.innerText = '';

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        const chunkStr = decoder.decode(value, { stream: true });
                        const lines = chunkStr.split('\n');
                        for (const line of lines) {
                            const trimmed = line.trim();
                            if (!trimmed || trimmed === 'data: [DONE]') continue;
                            if (trimmed.startsWith('data: ')) {
                                try {
                                    const parsed = JSON.parse(trimmed.slice(6));
                                    const delta = parsed.choices?.[0]?.delta?.content || '';
                                    if (delta) {
                                        if (!firstTokenTime) {
                                            firstTokenTime = Date.now() - startTime;
                                        }
                                        accumulated += delta;
                                        outputBox.innerText = accumulated;
                                    }
                                } catch (_) {}
                            }
                        }
                    }

                    const totalTime = Date.now() - startTime;
                    const metaText = firstTokenTime ? `First token: ${firstTokenTime}ms • Total: ${totalTime}ms` : `Latency: ${totalTime}ms`;
                    document.getElementById('response-meta').innerText = `⚡ ${metaText}`;
                    if (!accumulated) {
                        outputBox.innerText = 'Empty response received.';
                    }
                } else {
                    const totalTime = Date.now() - startTime;
                    document.getElementById('response-meta').innerText = `Latency: ${totalTime}ms`;
                    const errData = await res.json().catch(() => ({ error: { message: res.statusText } }));
                    const errMsg = (errData.error && errData.error.message) || JSON.stringify(errData, null, 2);
                    if (res.status === 429 || errMsg.includes('quota') || errMsg.includes('exhausted') || errMsg.includes('RESOURCE_EXHAUSTED')) {
                        outputBox.innerText = `⚠️ Google Cloud Quota / Rate Limit Reached (HTTP 429):\n${errMsg}\n\n💡 Google Antigravity reports that this account's free-tier request quota is currently capped on Google's servers.\n\n👉 Recommended Next Steps:\n1. Switch to 'opencode' provider in the Target Provider dropdown for unlimited free models (grok, deepseek, mimo, hy3).\n2. Or use 'auto/best-free' profile to automatically route to healthy active models.`;
                        if (typeof loadAntigravityQuota === 'function') {
                            loadAntigravityQuota();
                        }
                    } else {
                        outputBox.innerText = 'Error (' + res.status + '): ' + JSON.stringify(errData, null, 2);
                    }
                }
            } catch (e) {
                outputBox.innerText = 'Connection Error: ' + e.message;
            } finally {
                btnSendPrompt.innerText = '🚀 Send Prompt';
            }
        });
    }

    // Live update model list and pills when target provider dropdown changes
    const playProviderSel = document.getElementById('play-provider');
    if (playProviderSel) {
        playProviderSel.addEventListener('change', () => {
            loadModelList();
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

window.configuredProviders = [];

function editProviderByName(name) {
    const prov = (window.configuredProviders || []).find(p => (p.name || '').trim() === name.trim());
    openProviderForm(prov || { name: name });
}

async function testProviderByName(name) {
    const prov = (window.configuredProviders || []).find(p => p.name === name);
    if (!prov) { alert('Provider configuration not found: ' + name); return; }
    try {
        const res = await fetch('/v1/providers/test-connection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider_name: prov.name,
                api_key: prov.api_key || 'ollama',
                base_url: prov.base_url,
                format: prov.format || 'openai'
            })
        });
        const d = await res.json();
        const errMsg = (d.error && typeof d.error === 'object') ? (d.error.message || JSON.stringify(d.error)) : (d.error || d.message || 'Unreachable');
        if (d.connected) {
            alert(`✅ ${name} is ONLINE!\n\nLatency: ${d.latency_ms}ms\nModels Count: ${d.models_count}` + (d.sample_models ? `\nSample Models:\n${d.sample_models.slice(0, 6).join(', ')}` : ''));
        } else {
            alert(`❌ ${name} connection failed:\n\n${errMsg}`);
        }
    } catch (e) {
        alert('Error testing provider: ' + e.message);
    }
}

function openInPlayground(providerName, modelId) {
    const navItem = document.querySelector('.nav-item[data-tab="playground"]');
    if (navItem) navItem.click();

    setTimeout(() => {
        const provSel = document.getElementById('play-provider');
        if (provSel && providerName) {
            for (let i = 0; i < provSel.options.length; i++) {
                if (provSel.options[i].value === providerName) {
                    provSel.selectedIndex = i;
                    break;
                }
            }
        }
        const modelInp = document.getElementById('play-model');
        if (modelInp && modelId && modelId !== 'N/A') {
            modelInp.value = modelId;
        }
        loadModelList();
        const promptInp = document.getElementById('play-prompt');
        if (promptInp) promptInp.focus();
    }, 100);
}

function populateProvidersTable(providers) {
    const tbody = document.getElementById('providers-table-body');
    const select = document.getElementById('play-provider');
    window.configuredProviders = providers || [];

    if (!providers || providers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No providers configured yet. Click "+ Add Provider" or visit Provider Hub to connect one.</td></tr>';
        return;
    }

    tbody.innerHTML = providers.map(p => {
        const name = escapeHtml(p.name || '');
        const defaultModel = p.default_model || 'N/A';
        const pingId = 'ping-badge-' + encodeURIComponent(p.name || '');
        return `
        <tr>
            <td class="font-bold">
                <span style="cursor:pointer; color:#38bdf8; font-weight:600;" onclick="editProviderByName('${name}')" title="Click to edit ${name}">
                    ${name} ✏️
                </span>
            </td>
            <td><span class="badge badge-purple">${escapeHtml((p.format || 'openai').toUpperCase())}</span></td>
            <td class="code-text">
                <span style="cursor:pointer;" onclick="copyText('${escapeHtml(p.base_url || '')}')" title="Click to copy URL">
                    ${escapeHtml(p.base_url || '')} 📋
                </span>
            </td>
            <td class="code-text">
                <span class="badge badge-info" style="cursor:pointer;" onclick="openInPlayground('${name}', '${escapeHtml(defaultModel)}')" title="Click to test in Playground">
                    🎮 ${escapeHtml(defaultModel)}
                </span>
            </td>
            <td>
                <span id="${pingId}" class="badge badge-success" style="cursor:pointer; display:inline-flex; align-items:center; gap:5px; transition:all 0.2s; padding:3px 10px;" onclick="testProviderByName('${name}')" title="Live ping • Click to re-test">
                    <span style="width:7px; height:7px; border-radius:50%; background:#22c55e; display:inline-block;"></span>
                    <span>⚡ Measuring…</span>
                </span>
            </td>
            <td>
                <div style="display:flex; gap:6px;">
                    <button class="btn btn-sm btn-outline" onclick="testProviderByName('${name}')" title="Test Connection">⚡ Test</button>
                    <button class="btn btn-sm btn-outline" onclick="editProviderByName('${name}')" title="Edit Provider">✏️ Edit</button>
                    <button class="btn btn-sm btn-primary" onclick="openInPlayground('${name}', '${escapeHtml(defaultModel)}')" title="Test in Playground">🚀 Play</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteProvider('${name}')" title="Delete Provider">🗑️</button>
                </div>
            </td>
        </tr>
    `;
    }).join('');

    if (select) {
        select.innerHTML = '<option value="">Auto Select First</option>' + providers.map(p => `
            <option value="${escapeHtml(p.name)}">${escapeHtml(p.name)} (${escapeHtml(p.format || 'openai')})</option>
        `).join('');
    }

    // Automatically fetch real-time latency pings for all providers
    autoRefreshProviderPings();
}

async function autoRefreshProviderPings() {
    try {
        const res = await fetch('/v1/providers/status-all');
        if (!res.ok) return;
        const statuses = await res.json();
        (statuses || []).forEach(s => {
            const badgeId = 'ping-badge-' + encodeURIComponent(s.name || '');
            const el = document.getElementById(badgeId);
            if (!el) return;

            if (s.status === 'connected' || s.ok) {
                const lat = s.latency_ms !== null && s.latency_ms !== undefined ? `${s.latency_ms}ms` : 'Online';
                el.className = 'badge badge-success';
                el.innerHTML = `<span style="width:7px; height:7px; border-radius:50%; background:#22c55e; display:inline-block; box-shadow:0 0 6px #22c55e;"></span> <span>⚡ ${lat}</span>`;
                el.title = `Connected (${lat}) • ${s.model_count || s.models_count || 0} models available • Click to re-ping`;
            } else if (s.status === 'unauthorized') {
                el.className = 'badge badge-warning';
                el.innerHTML = `<span style="width:7px; height:7px; border-radius:50%; background:#f59e0b; display:inline-block;"></span> <span>⚠️ Auth Error</span>`;
                el.title = `${s.error || 'Invalid API Key'} • Click to test`;
            } else {
                el.className = 'badge badge-danger';
                el.innerHTML = `<span style="width:7px; height:7px; border-radius:50%; background:#ef4444; display:inline-block;"></span> <span>🔴 Offline</span>`;
                el.title = `${s.error || 'Offline / Unreachable'} • Click to test`;
            }
        });
    } catch (_) {}
}

async function loadModelList() {
    const datalist = document.getElementById('model-list');
    const modelInput = document.getElementById('play-model');
    const chipsContainer = document.getElementById('play-model-chips');
    if (!datalist || !modelInput) return;

    let discoveredModelObjects = [];
    try {
        const res = await fetch('/v1/models');
        if (res.ok) {
            const data = await res.json();
            discoveredModelObjects = data.data || [];
        }
    } catch (_) {}

    // Find currently selected provider in the dropdown
    const providerSel = document.getElementById('play-provider');
    const selectedProvName = providerSel ? (providerSel.value || '').trim() : '';
    const prov = (window.configuredProviders || []).find(p => (p.name || '').trim().toLowerCase() === selectedProvName.toLowerCase());

    let providerModels = [];

    if (selectedProvName) {
        // Specifically filter models for the selected provider
        const matched = discoveredModelObjects.filter(m => {
            const ownedBy = (m.owned_by || '').toLowerCase();
            const id = (m.id || '').toLowerCase();
            const pName = selectedProvName.toLowerCase();
            return ownedBy === pName || (pName.includes('antigravity') && (id.startsWith('antigravity/') || id.startsWith('gemini-') || id.startsWith('claude-')));
        }).map(m => m.id);

        if (matched.length > 0) {
            providerModels = matched;
        } else if (prov) {
            if ((prov.format || '').toLowerCase() === 'antigravity' || selectedProvName.toLowerCase().includes('antigravity')) {
                // Use correct real upstream IDs - sorted by quota availability
                providerModels = [
                    'antigravity/claude-sonnet-4-6',
                    'antigravity/claude-opus-4-6-thinking',
                    'antigravity/gpt-oss-120b-medium',
                    'antigravity/gemini-3.6-flash-high',
                    'antigravity/gemini-3.6-flash-medium',
                    'antigravity/gemini-3.6-flash-low',
                    'antigravity/gemini-3.5-flash-high',
                    'antigravity/gemini-3.5-flash-medium',
                    'antigravity/gemini-3.5-flash-low',
                    'antigravity/gemini-3.1-pro-high',
                    'antigravity/gemini-3.1-pro-low',
                    'antigravity/gemini-3.1-flash-lite',
                    'antigravity/gemini-2.5-flash',
                    'antigravity/gemini-2.5-pro'
                ];
            } else if (prov.default_model) {
                providerModels = [prov.default_model];
            }
        }
    } else {
        // When Auto Select First is active, show all available models + auto profiles
        providerModels = discoveredModelObjects.map(m => m.id);
    }

    if (providerModels.length === 0) {
        if (prov && prov.default_model) {
            providerModels = [prov.default_model];
        } else {
            providerModels = [
                "auto/best-free", "auto/best-coding", "auto/best-fast",
                "hy3-free", "mimo-v2.5-free", "antigravity/claude-sonnet-4-6", "antigravity/gemini-2.5-flash"
            ];
        }
    }

    // Ensure default model is present and prioritized
    if (prov && prov.default_model && !providerModels.includes(prov.default_model)) {
        providerModels.unshift(prov.default_model);
    }

    // Update datalist for auto-complete
    datalist.innerHTML = providerModels.map(id => `<option value="${escapeHtml(id)}"></option>`).join('');

    // Update clickable suggestion pills for THIS selected provider only
    if (chipsContainer) {
        const chipsToShow = providerModels.slice(0, 12);
        chipsContainer.innerHTML = chipsToShow.map(m => {
            const isSelected = modelInput.value === m || (prov && prov.default_model === m);
            const isAntigravity = m.startsWith('antigravity/');
            const bg = isSelected ? 'rgba(56, 189, 248, 0.25)' : (isAntigravity ? 'rgba(66, 133, 244, 0.15)' : 'rgba(99, 102, 241, 0.15)');
            const border = isSelected ? '#38bdf8' : (isAntigravity ? '#4285f4' : '#4f46e5');
            const color = isSelected ? '#38bdf8' : (isAntigravity ? '#60a5fa' : '#a5b4fc');
            const icon = isAntigravity ? '🚀 ' : (m.startsWith('auto/') ? '🎛️ ' : '🤖 ');
            return `<button type="button" class="btn btn-sm" onclick="selectPlaygroundModel('${escapeHtml(m)}')" style="background:${bg}; border:1px solid ${border}; color:${color}; border-radius:16px; font-size:11px; padding:3px 10px; cursor:pointer;" title="Select ${escapeHtml(m)}">${icon}${escapeHtml(m)}</button>`;
        }).join('');
    }

    // Auto update model input when provider changes if current model does not belong to provider
    if (selectedProvName && (!modelInput.value || !providerModels.includes(modelInput.value))) {
        modelInput.value = (prov && prov.default_model) ? prov.default_model : providerModels[0];
    } else if (!modelInput.value && providerModels.length > 0) {
        modelInput.value = providerModels[0];
    }
}

function selectPlaygroundModel(modelId) {
    const modelInput = document.getElementById('play-model');
    if (modelInput) {
        modelInput.value = modelId;
    }
    const promptInput = document.getElementById('play-prompt');
    if (promptInput) promptInput.focus();
}

window.selectPlaygroundModel = selectPlaygroundModel;
window.testProviderByName = testProviderByName;
window.openInPlayground = openInPlayground;

// ── Antigravity Live Quota ─────────────────────────────────────────────────
async function loadAntigravityQuota() {
    const listEl = document.getElementById('agy-quota-list');
    const resetEl = document.getElementById('agy-quota-reset');
    if (!listEl) return;
    listEl.innerHTML = '<span style="color:#6b7280;font-size:11px;">⏳ Fetching live quota...</span>';
    try {
        const res = await fetch('/v1/providers/antigravity/quota');
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            listEl.innerHTML = `<span style="color:#f87171;font-size:11px;">Error: ${err.error || res.statusText}</span>`;
            return;
        }
        const data = await res.json();
        const models = data.models || [];
        const accountEl = document.getElementById('agy-quota-account');
        if (accountEl) {
            const email = data.email || 'active account';
            const tier = data.tier || 'Free Tier';
            accountEl.innerHTML = `<span style="color:#60a5fa;">👤 ${escapeHtml(email)}</span> &bull; <span style="color:#fbbf24;">${escapeHtml(tier)}</span>`;
        }
        if (models.length === 0) {
            listEl.innerHTML = '<span style="color:#6b7280;font-size:11px;">No model data returned.</span>';
            return;
        }

        // Deduplicate and show clean, distinct models
        const seenNames = new Set();
        const SHOW = [];
        for (const m of models) {
            const name = m.display_name || m.upstream_id;
            if (!seenNames.has(name) && !m.upstream_id.startsWith('tab_') && !m.upstream_id.startsWith('chat_')) {
                seenNames.add(name);
                SHOW.push(m);
            }
        }

        listEl.innerHTML = SHOW.map(m => {
            const pct = m.remaining_pct !== undefined ? m.remaining_pct : 100;
            const color = pct > 30 ? '#34d399' : (pct > 10 ? '#fbbf24' : '#f87171');
            const barColor = pct > 30 ? 'linear-gradient(90deg,#34d399,#10b981)' : (pct > 10 ? 'linear-gradient(90deg,#fbbf24,#f59e0b)' : 'linear-gradient(90deg,#f87171,#ef4444)');
            const statusIcon = pct > 30 ? '🟢' : (pct > 10 ? '🟡' : '🔴');
            const thinkIcon = m.supports_thinking ? ' 🧠' : '';
            const fullName = m.display_name || m.upstream_id;
            return `<div style="display:flex; flex-direction:column; gap:2px; cursor:pointer;" onclick="selectPlaygroundModel('antigravity/${escapeHtml(m.upstream_id)}')" title="Click to select ${escapeHtml(fullName)}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:10.5px; color:#e2e8f0; font-weight:600;">${statusIcon} ${escapeHtml(fullName)}${thinkIcon}</span>
                    <span style="font-size:10.5px; font-weight:700; color:${color};">${pct.toFixed(1)}%</span>
                </div>
                <div style="height:4px; background:rgba(255,255,255,0.08); border-radius:4px; overflow:hidden;">
                    <div style="height:100%; width:${Math.max(pct,1).toFixed(1)}%; background:${barColor}; border-radius:4px; transition:width 0.5s ease;"></div>
                </div>
            </div>`;
        }).join('');

        // Find nearest reset time
        const resetTimes = models.filter(m => m.reset_time).map(m => new Date(m.reset_time));
        if (resetTimes.length > 0 && resetEl) {
            const nearest = new Date(Math.min(...resetTimes));
            const now = new Date();
            const diffMs = nearest - now;
            if (diffMs > 0) {
                const mins = Math.round(diffMs / 60000);
                const hrs = Math.floor(mins / 60);
                const rem = mins % 60;
                resetEl.textContent = `Quota resets in: ${hrs > 0 ? hrs + 'h ' : ''}${rem}m`;
            } else {
                resetEl.textContent = 'Quota reset pending refresh';
            }
        }
    } catch (e) {
        listEl.innerHTML = `<span style="color:#f87171;font-size:11px;">Network error: ${e.message}</span>`;
    }
}
window.loadAntigravityQuota = loadAntigravityQuota;


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

// ---------- Provider / Server management ----------
var editingProviderName = null;

async function loadMgmtProviders() {
    const tbody = document.getElementById('mgmt-providers-body');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Loading servers...</td></tr>';
    try {
        const res = await fetch('/v1/config');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        const providers = data.providers || [];
        window.configuredProviders = providers;
        if (providers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No servers configured. Click + Add Server to create one.</td></tr>';
            return;
        }
        tbody.innerHTML = providers.map(p => {
            const name = escapeHtml(p.name || '');
            const defaultModel = p.default_model || 'N/A';
            return `
                <tr>
                    <td class="font-bold">
                        <span style="cursor:pointer; color:#38bdf8;" onclick="editProviderByName('${name}')" title="Click to edit">
                            ${name} ✏️
                        </span>
                    </td>
                    <td><span class="badge badge-purple">${escapeHtml((p.format || 'auto').toUpperCase())}</span></td>
                    <td class="code-text">
                        <span style="cursor:pointer;" onclick="copyText('${escapeHtml(p.base_url || '')}')" title="Click to copy">
                            ${escapeHtml(p.base_url || '')} 📋
                        </span>
                    </td>
                    <td class="code-text">
                        <span class="badge badge-info" style="cursor:pointer;" onclick="openInPlayground('${name}', '${escapeHtml(defaultModel)}')" title="Click to test in Playground">
                            🎮 ${escapeHtml(defaultModel)}
                        </span>
                    </td>
                    <td>
                        <div style="display:flex; gap:6px;">
                            <button class="btn btn-sm btn-outline" onclick="testProviderByName('${name}')" title="Test Connection">⚡ Test</button>
                            <button class="btn btn-sm btn-outline" onclick="editProviderByName('${name}')" title="Edit Provider">✏️ Edit</button>
                            <button class="btn btn-sm btn-primary" onclick="openInPlayground('${name}', '${escapeHtml(defaultModel)}')" title="Open in Playground">🚀 Play</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteProvider('${name}')" title="Delete Provider">🗑️</button>
                        </div>
                    </td>
                </tr>`;
        }).join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Failed to load servers: ' + escapeHtml(e.message) + '</td></tr>';
    }
}

function onProviderAuthTypeChange() {
    const authType = document.getElementById('pf-auth-type') ? document.getElementById('pf-auth-type').value : 'apikey';
    const keyGrp = document.getElementById('pf-key-group');
    const cookieGrp = document.getElementById('pf-cookie-group');
    const oauthGrp = document.getElementById('pf-oauth-group');

    if (keyGrp) keyGrp.style.display = (authType === 'apikey' || authType === 'local') ? 'block' : 'none';
    if (cookieGrp) cookieGrp.style.display = authType === 'cookie' ? 'block' : 'none';
    if (oauthGrp) oauthGrp.style.display = authType === 'oauth' ? 'block' : 'none';
}

function initPresetsDropdown() {
    const sel = document.getElementById('pf-preset-select');
    if (!sel) return;
    const presets = window.PROVIDER_PRESETS || [];

    // Group presets by category
    const categories = {
        "cloud": "☁️ Primary Labs & Cloud Giants",
        "reasoning": "🧠 Reasoning & Coding Models",
        "fast": "⚡ Ultra-Fast LPU & GPU Inference",
        "asian": "🌏 Asian AI Leaders (DeepSeek, Qwen, Kimi...)",
        "local": "💻 Local Runtimes & Offline Engines",
        "router": "🌐 Unified Routers & Gateways",
        "apps": "🤖 Agent Platforms & Web UIs",
        "enterprise": "🛡️ Enterprise Platforms & Cloud AI"
    };

    let html = '<option value="">-- Pick from ' + presets.length + '+ Major AI Providers --</option>';

    Object.keys(categories).forEach(catKey => {
        const catPresets = presets.filter(p => (p.category || 'cloud') === catKey);
        if (catPresets.length > 0) {
            html += `<optgroup label="${categories[catKey]}">`;
            catPresets.forEach(p => {
                html += `<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)} — ${escapeHtml(p.default_model || p.notes || '')}</option>`;
            });
            html += '</optgroup>';
        }
    });

    sel.innerHTML = html;

    sel.addEventListener('change', () => {
        const val = sel.value;
        if (!val) return;
        const p = presets.find(item => item.name === val);
        if (!p) return;
        document.getElementById('pf-name').value = p.name;
        document.getElementById('pf-format').value = p.format || 'openai';
        document.getElementById('pf-base').value = p.base_url || '';
        document.getElementById('pf-model').value = p.default_model || '';
        document.getElementById('pf-notes').value = p.notes || '';

        const authSel = document.getElementById('pf-auth-type');
        if (p.name.includes('Copilot')) {
            if (authSel) authSel.value = 'oauth';
        } else if (p.name.includes('Claude Code')) {
            if (authSel) authSel.value = 'cookie';
        } else if (p.category === 'local' || (p.notes && p.notes.toLowerCase().includes('local'))) {
            if (authSel) authSel.value = 'local';
        } else {
            if (authSel) authSel.value = 'apikey';
        }
        onProviderAuthTypeChange();
    });
}

function triggerModalOAuthFlow() {
    const name = document.getElementById('pf-name').value || 'GitHub Copilot';
    if (typeof openConnectModal === 'function') {
        openConnectModal(name);
    } else {
        alert('OAuth flow initiated. Please approve in your browser tab.');
    }
}

function openProviderForm(provider) {
    initPresetsDropdown();
    const modal = document.getElementById('provider-modal');
    const presetSel = document.getElementById('pf-preset-select');
    if (presetSel) presetSel.value = '';
    if (provider && provider.name !== undefined) {
        editingProviderName = provider.name;
        document.getElementById('provider-modal-title').innerText = 'Edit Server';
        document.getElementById('pf-name').value = provider.name || '';
        document.getElementById('pf-format').value = provider.format || 'auto';
        document.getElementById('pf-base').value = provider.base_url || '';
        document.getElementById('pf-model').value = provider.default_model || '';
        document.getElementById('pf-notes').value = provider.notes || '';
        document.getElementById('pf-temp').value = provider.default_temperature || 0.7;
        document.getElementById('pf-max').value = provider.default_max_tokens || 1024;
        document.getElementById('pf-key').value = '';
        if (document.getElementById('pf-cookie')) document.getElementById('pf-cookie').value = '';
        document.getElementById('pf-key-hint').innerText = 'Leave blank to keep existing key.';
    } else {
        editingProviderName = null;
        document.getElementById('provider-modal-title').innerText = 'Add Server';
        ['pf-name', 'pf-base', 'pf-key', 'pf-model', 'pf-notes'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        if (document.getElementById('pf-cookie')) document.getElementById('pf-cookie').value = '';
        document.getElementById('pf-format').value = 'auto';
        document.getElementById('pf-temp').value = '0.7';
        document.getElementById('pf-max').value = '1024';
        document.getElementById('pf-key-hint').innerText = '';
    }
    onProviderAuthTypeChange();
    modal.hidden = false;
}

function closeProviderModal() {
    document.getElementById('provider-modal').hidden = true;
}

async function saveProvider() {
    const name = document.getElementById('pf-name').value.trim();
    if (!name) { alert('Display name is required.'); return; }

    const authType = document.getElementById('pf-auth-type') ? document.getElementById('pf-auth-type').value : 'apikey';
    let apiKey = document.getElementById('pf-key').value.trim();
    if (authType === 'cookie') {
        const cookieVal = document.getElementById('pf-cookie') ? document.getElementById('pf-cookie').value.trim() : '';
        apiKey = cookieVal || apiKey;
    } else if (authType === 'oauth') {
        const oauthToken = document.getElementById('pf-oauth-token') ? document.getElementById('pf-oauth-token').value.trim() : '';
        apiKey = oauthToken || apiKey;
    } else if (authType === 'local' && !apiKey) {
        apiKey = 'ollama';
    }

    const provider = {
        name: name,
        format: document.getElementById('pf-format').value,
        base_url: document.getElementById('pf-base').value.trim(),
        api_key: apiKey,
        default_model: document.getElementById('pf-model').value.trim(),
        notes: (document.getElementById('pf-notes').value.trim() + ' (' + authType.toUpperCase() + ')').trim(),
        default_temperature: parseFloat(document.getElementById('pf-temp').value) || 0.7,
        default_max_tokens: parseInt(document.getElementById('pf-max').value) || 1024
    };

    const btnSave = document.getElementById('btn-provider-save');
    btnSave.disabled = true;
    btnSave.innerText = 'Saving...';
    try {
        let res;
        if (editingProviderName) {
            res = await fetch('/v1/providers/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: editingProviderName, provider: provider })
            });
        } else {
            res = await fetch('/v1/providers/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(provider)
            });
        }
        const data = await res.json();
        if (!res.ok) throw new Error((data.error && data.error.message) || 'Request failed');
        alert(data.message || 'Saved');
        closeProviderModal();
        loadMgmtProviders();
        loadDashboardData();
        loadModelList();
        loadConfig();
    } catch (e) {
        alert('Error: ' + e.message);
    } finally {
        btnSave.disabled = false;
        btnSave.innerText = 'Save Server';
    }
}

async function deleteProvider(name) {
    if (!confirm('Delete server "' + name + '"? This removes it from config.json.')) return;
    try {
        const res = await fetch('/v1/providers/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        const data = await res.json();
        if (!res.ok) throw new Error((data.error && data.error.message) || 'Request failed');
        alert(data.message || 'Deleted');
        loadMgmtProviders();
        loadDashboardData();
        loadModelList();
        loadConfig();
    } catch (e) {
        alert('Error: ' + e.message);
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

// ---------- AIPI Platform & Virtual API Keys Management ----------
var activeMasterKeySecret = '';

async function loadMasterKey() {
    const input = document.getElementById('master-key-val');
    if (!input) return;
    try {
        const res = await fetch('/v1/virtual-keys/master');
        const data = await res.json();
        if (data.master_key) {
            activeMasterKeySecret = data.master_key.secret_key || '';
            input.value = activeMasterKeySecret;
        }
    } catch (e) {
        if (input) input.value = 'Error loading master key';
    }
}

function toggleMasterKeyVisibility() {
    const input = document.getElementById('master-key-val');
    const btn = document.getElementById('btn-toggle-master-key');
    if (!input || !btn) return;
    if (input.type === 'password') {
        input.type = 'text';
        btn.innerText = '🔒 Hide';
    } else {
        input.type = 'password';
        btn.innerText = '👁️ Show';
    }
}

function copyMasterKey() {
    if (!activeMasterKeySecret) return;
    navigator.clipboard.writeText(activeMasterKeySecret).then(() => {
        alert('📋 Master AIPI API Key copied to clipboard:\n' + activeMasterKeySecret);
    });
}

function openCreateKeyModal() {
    const modal = document.getElementById('modal-create-key');
    if (modal) modal.style.display = 'flex';
}

function closeCreateKeyModal() {
    const modal = document.getElementById('modal-create-key');
    if (modal) modal.style.display = 'none';
}

async function submitCreateKey() {
    const name = document.getElementById('mk-name').value.trim();
    const budget = parseFloat(document.getElementById('mk-budget').value) || 0.0;
    const rpm = parseInt(document.getElementById('mk-rpm').value) || 0;
    const expiry = parseInt(document.getElementById('mk-expiry').value) || 0;
    const modelsRaw = document.getElementById('mk-models').value.trim();
    const allowed_models = modelsRaw ? modelsRaw.split(',').map(m => m.trim()).filter(Boolean) : [];

    if (!name) { alert('Key name is required'); return; }

    const btn = document.getElementById('btn-submit-create-key');
    btn.disabled = true;
    btn.innerText = 'Generating...';

    try {
        const res = await fetch('/v1/virtual-keys/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                max_monthly_budget: budget,
                rate_limit_rpm: rpm,
                expires_in_days: expiry,
                allowed_models: allowed_models
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to generate key');
        
        closeCreateKeyModal();
        loadVirtualKeys();

        // Show the newly minted key modal
        const successModal = document.getElementById('modal-key-success');
        const secretVal = document.getElementById('new-key-secret-val');
        if (successModal && secretVal) {
            secretVal.value = data.key.secret_key;
            successModal.style.display = 'flex';
        }
    } catch (e) {
        alert('Error: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.innerText = '🚀 Generate Key';
    }
}

function copyNewCreatedKey() {
    const secretVal = document.getElementById('new-key-secret-val');
    if (!secretVal) return;
    navigator.clipboard.writeText(secretVal.value).then(() => {
        alert('📋 Copied AIPI API Key to clipboard:\n' + secretVal.value);
    });
}

function closeKeySuccessModal() {
    const modal = document.getElementById('modal-key-success');
    if (modal) modal.style.display = 'none';
}

async function loadVirtualKeys() {
    loadMasterKey();
    const tbody = document.getElementById('vkeys-table-body');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Loading AIPI API keys...</td></tr>';
    try {
        const res = await fetch('/v1/virtual-keys');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        const keys = data.keys || [];
        if (keys.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No API keys minted yet. Click "+ Generate New API Key" above.</td></tr>';
            return;
        }
        tbody.innerHTML = keys.map(k => {
            const keyId = escapeHtml(k.key_id || '');
            const budget = k.max_monthly_budget > 0 ? '$' + k.max_monthly_budget.toFixed(2) : 'Unlimited';
            const spend = '$' + (k.current_spend || 0).toFixed(4);
            const rpm = k.rate_limit_rpm > 0 ? k.rate_limit_rpm + ' RPM' : 'Unlimited';
            const expiry = k.expires_at ? escapeHtml(k.expires_at) : 'Never';
            const lastUsed = k.last_used_at ? escapeHtml(k.last_used_at) : 'Never';
            const isRevoked = k.status === 'revoked';
            const isMaster = k.name === 'Master AIPI Key' || k.name === 'Master Proxia Key';

            return `
                <tr>
                    <td class="font-bold">
                        ${isMaster ? '⚡ ' : '🔑 '}${escapeHtml(k.name || '')}
                    </td>
                    <td class="code-text">
                        ${escapeHtml(k.masked_key || '')} 
                        <button class="btn btn-sm btn-outline" onclick="copyText('${escapeHtml(k.secret_key || k.masked_key)}')">📋 Copy</button>
                    </td>
                    <td><span class="badge badge-purple">${budget}</span> <small style="color:var(--text-muted);">(${spend})</small></td>
                    <td><span class="badge badge-info">${rpm}</span></td>
                    <td class="text-muted" style="font-size: 12px;">${expiry}</td>
                    <td class="text-muted" style="font-size: 12px;">${lastUsed}</td>
                    <td><span class="badge ${isRevoked ? 'badge-red' : 'badge-green'}">${isRevoked ? 'Revoked' : 'Active'}</span></td>
                    <td>
                        ${!isRevoked && !isMaster ? `<button class="btn btn-sm btn-outline" onclick="revokeVirtualKey('${keyId}')">Revoke</button>` : ''}
                        ${!isMaster ? `<button class="btn btn-sm btn-danger" onclick="deleteVirtualKey('${keyId}')">Delete</button>` : '<span class="text-muted" style="font-size:11px;">Protected</span>'}
                    </td>
                </tr>`;
        }).join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Failed to load keys: ' + escapeHtml(e.message) + '</td></tr>';
    }
}

async function revokeVirtualKey(keyId) {
    if (!confirm('Revoke this AIPI API key? Connected tools will immediately receive HTTP 401 Unauthorized.')) return;
    try {
        const res = await fetch('/v1/virtual-keys/revoke', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key_id: keyId })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to revoke key');
        loadVirtualKeys();
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

async function deleteVirtualKey(keyId) {
    if (!confirm('Permanently delete this AIPI API key from the database?')) return;
    try {
        const res = await fetch('/v1/virtual-keys/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key_id: keyId })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to delete key');
        loadVirtualKeys();
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

// ---------- Analytics & Cost Intelligence ----------
async function loadAnalytics() {
    try {
        const res = await fetch('/v1/analytics/overview');
        if (!res.ok) return;
        const data = await res.json();
        const ana = data.analytics || {};
        
        document.getElementById('ana-cost').innerText = '$' + (ana.estimated_total_cost_usd || 0.0).toFixed(4);
        document.getElementById('ana-tokens').innerText = (ana.total_tokens || 0).toLocaleString();
        
        const cache = ana.cache || {};
        document.getElementById('ana-cache-hit').innerText = (cache.hit_rate_pct || 0.0).toFixed(1) + '%';
        document.getElementById('ana-latency').innerText = Math.round(ana.avg_latency_ms || 0) + ' ms';

        const statsBox = document.getElementById('cache-stats-box');
        if (statsBox) {
            statsBox.innerHTML = `
                <div><strong>Cached Entries in Memory:</strong> ${cache.cached_entries || 0}</div>
                <div><strong>Cache Hits (0ms Latency):</strong> ${cache.hits || 0}</div>
                <div><strong>Cache Misses (Forwarded to Provider):</strong> ${cache.misses || 0}</div>
                <div style="margin-top: 6px; color: #10b981;"><strong>Saved Tokens & Money:</strong> Served instantly with 0 token consumption.</div>
            `;
        }
    } catch (e) {
        // ignore
    }
}

async function clearPromptCache() {
    if (!confirm('Clear all cached prompt responses?')) return;
    try {
        const res = await fetch('/v1/cache/clear', { method: 'POST' });
        const data = await res.json();
        alert(data.message || 'Cache cleared');
        loadAnalytics();
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

// ---------- Admin, License & Team Edition ----------

async function loadLicenseStatus() {
    const box = document.getElementById('license-status-box');
    if (!box) return;
    try {
        const res = await fetch('/v1/license/status');
        const data = await res.json();
        const lic = data.license || {};
        const tierInfo = (data.tiers && data.tiers[lic.tier]) || {};
        box.innerHTML = `
            <div style="display:flex; flex-wrap:wrap; gap:16px;">
                <div><strong>Tier:</strong> <span class="badge badge-purple">${lic.tier || 'community'}</span></div>
                <div><strong>Status:</strong> ${lic.status || 'community'}</div>
                <div><strong>Features:</strong> ${(tierInfo.features || []).join(', ') || 'community'}</div>
                <div><strong>Max Users:</strong> ${tierInfo.max_users ?? 1}</div>
                <div><strong>Rate Limit:</strong> ${tierInfo.max_requests_per_min ?? 60}/min</div>
            </div>`;
    } catch (e) {
        box.innerHTML = 'Failed to load license: ' + escapeHtml(e.message);
    }
}

async function loadOidcStatus() {
    const box = document.getElementById('oidc-status-box');
    if (!box) return;
    try {
        const res = await fetch('/v1/auth/oidc/status');
        const data = await res.json();
        const sso = data.sso || {};
        box.innerHTML = `Configured: <strong>${sso.configured ? 'YES' : 'NO'}</strong> | Issuer: ${escapeHtml(sso.issuer || '')} | Redirect: ${escapeHtml(sso.redirect_uri || '')}`;
        if (sso.configured) document.getElementById('oidc-issuer').value = sso.issuer;
    } catch (e) {
        box.innerHTML = 'Failed to load SSO status';
    }
}

async function adminLogin() {
    const username = document.getElementById('admin-user').value;
    const password = document.getElementById('admin-pass').value;
    try {
        const res = await fetch('/v1/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Login failed');
        adminToken = data.session.token;
        localStorage.setItem('aimm_admin_token', adminToken);
        document.getElementById('admin-login-status').innerText = '✅ Authenticated as ' + data.session.username + ' (' + data.session.role + ')';
        document.getElementById('admin-users-section').style.display = 'block';
        document.getElementById('btn-admin-logout').style.display = 'inline-block';
        loadAdminUsers();
    } catch (e) {
        alert('Login failed: ' + e.message);
    }
}

function adminLogout() {
    adminToken = '';
    localStorage.removeItem('aimm_admin_token');
    document.getElementById('admin-login-status').innerText = 'Not authenticated.';
    document.getElementById('admin-users-section').style.display = 'none';
    document.getElementById('btn-admin-logout').style.display = 'none';
}

async function loadAdminUsers() {
    const tbody = document.getElementById('admin-users-body');
    if (!tbody || !adminToken) return;
    try {
        const res = await fetch('/v1/admin/users', { headers: { 'X-Admin-Token': adminToken } });
        if (res.status === 401) { tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Session expired — login again.</td></tr>'; return; }
        const data = await res.json();
        const users = data.users || [];
        tbody.innerHTML = users.map(u => `
            <tr>
                <td class="font-bold">${escapeHtml(u.username)}</td>
                <td><span class="badge badge-info">${escapeHtml(u.role)}</span></td>
                <td class="text-muted">${escapeHtml(u.created_at || '')}</td>
                <td><button class="btn btn-sm btn-danger" onclick="adminDeleteUser('${escapeHtml(u.username)}')">Delete</button></td>
            </tr>`).join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Error: ' + escapeHtml(e.message) + '</td></tr>';
    }
}

async function adminCreateUser() {
    const username = document.getElementById('new-user-name').value.trim();
    const password = document.getElementById('new-user-pass').value;
    const role = document.getElementById('new-user-role').value;
    if (!username || !password) { alert('Username and password required'); return; }
    try {
        const res = await fetch('/v1/admin/users/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Admin-Token': adminToken },
            body: JSON.stringify({ username, password, role })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed');
        alert('User created: ' + data.user.username + ' (' + data.user.role + ')');
        loadAdminUsers();
    } catch (e) { alert('Error: ' + e.message); }
}

async function adminDeleteUser(username) {
    if (!confirm('Delete user ' + username + '?')) return;
    try {
        const res = await fetch('/v1/admin/users/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Admin-Token': adminToken },
            body: JSON.stringify({ username })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed');
        loadAdminUsers();
    } catch (e) { alert('Error: ' + e.message); }
}

async function activateLicense() {
    const key = document.getElementById('license-key-input').value.trim();
    if (!key) { alert('Paste a license key first'); return; }
    try {
        const res = await fetch('/v1/license/activate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ license_key: key })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Activation failed');
        alert('✅ License activated! Tier: ' + data.license.tier);
        loadLicenseStatus();
    } catch (e) { alert('License error: ' + e.message); }
}

async function exportReport(format) {
    try {
        const res = await fetch('/v1/reports/export?format=' + format);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Export failed');
        document.getElementById('export-status-box').innerHTML = '✅ Report generated: <code>' + escapeHtml(data.path || '') + '</code>';
    } catch (e) { alert('Export error: ' + e.message); }
}

async function saveOidcConfig() {
    const issuer = document.getElementById('oidc-issuer').value.trim();
    const client_id = document.getElementById('oidc-client-id').value.trim();
    const client_secret = document.getElementById('oidc-client-secret').value.trim();
    try {
        const res = await fetch('/v1/admin/oidc/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ issuer, client_id, client_secret })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Save failed');
        alert('✅ OIDC config saved');
        loadOidcStatus();
    } catch (e) { alert('Error: ' + e.message); }
}

async function adminChangePassword() {
    const currentPass = document.getElementById('change-pass-current').value;
    const newPass = document.getElementById('change-pass-new').value;
    const statusBox = document.getElementById('change-pass-status');
    if (!currentPass || !newPass) {
        alert('Both current and new password are required');
        return;
    }
    try {
        const res = await fetch('/v1/admin/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Admin-Token': adminToken },
            body: JSON.stringify({ old_password: currentPass, new_password: newPass })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Password update failed');
        alert('✅ Admin password updated successfully!');
        document.getElementById('change-pass-current').value = '';
        document.getElementById('change-pass-new').value = '';
        if (statusBox) statusBox.innerHTML = '<span style="color:#10b981;">Password successfully changed.</span>';
    } catch (e) {
        alert('Error: ' + e.message);
        if (statusBox) statusBox.innerHTML = '<span style="color:#ef4444;">' + escapeHtml(e.message) + '</span>';
    }
}

// ---------- 1-Click IDE Auto-Configurator ----------
async function loadIdes() {
    const container = document.getElementById('ide-cards-container');
    if (!container) return;
    try {
        const res = await fetch('/v1/ide/detect');
        const data = await res.json();
        const ides = data.ides || [];
        if (!ides.length) {
            container.innerHTML = '<div class="port-status-box">No supported IDEs detected on this system.</div>';
            return;
        }
        container.innerHTML = ides.map(ide => `
            <div class="stat-card" style="flex-direction: column; align-items: flex-start; gap: 10px; border: 1px solid var(--border);">
                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                    <strong style="font-size: 15px;">${escapeHtml(ide.name)}</strong>
                    <span class="badge ${ide.configured ? 'badge-green' : (ide.detected ? 'badge-info' : 'badge-muted')}">
                        ${ide.configured ? '✔ Connected' : (ide.detected ? 'Installed' : 'Not Found')}
                    </span>
                </div>
                <div style="font-size: 12px; color: var(--text-muted); word-break: break-all;">
                    <code>${escapeHtml(ide.path)}</code>
                </div>
                <div style="display: flex; gap: 8px; width: 100%; margin-top: 6px;">
                    <button class="btn btn-sm btn-primary" style="flex: 1;" onclick="injectIde('${ide.id}')">
                        ⚡ 1-Click Configure
                    </button>
                    ${ide.has_backup ? `<button class="btn btn-sm btn-outline" onclick="restoreIde('${ide.id}')">Revert</button>` : ''}
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<div class="port-status-box" style="color:#ef4444;">Failed to detect IDEs: ' + escapeHtml(e.message) + '</div>';
    }
}

async function injectIde(ideId) {
    try {
        const res = await fetch('/v1/ide/inject', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ide_id: ideId, api_key: 'aipi-local', model: 'auto/fast' })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Configuration failed');
        alert('✅ ' + data.message);
        loadIdes();
    } catch (e) { alert('Error: ' + e.message); }
}

async function restoreIde(ideId) {
    try {
        const res = await fetch('/v1/ide/restore', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ide_id: ideId })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Revert failed');
        alert('✅ ' + data.message);
        loadIdes();
    } catch (e) { alert('Error: ' + e.message); }
}

// ---------- Privacy & Stealth Mode Controller ----------
var currentPrivacy = { pii_enabled: true, stealth_mode: false };

async function loadPrivacyStatus() {
    try {
        const res = await fetch('/v1/privacy/status');
        const data = await res.json();
        if (data.privacy) {
            currentPrivacy = data.privacy;
            updatePrivacyUI();
        }
    } catch (e) {}
}

function updatePrivacyUI() {
    const piiEl = document.getElementById('pii-status-text');
    const stealthEl = document.getElementById('stealth-status-text');
    if (piiEl) {
        piiEl.innerText = currentPrivacy.pii_enabled ? 'ON' : 'OFF';
        piiEl.style.color = currentPrivacy.pii_enabled ? '#10b981' : '#94a3b8';
    }
    if (stealthEl) {
        stealthEl.innerText = currentPrivacy.stealth_mode ? 'ACTIVE' : 'OFF';
        stealthEl.style.color = currentPrivacy.stealth_mode ? '#ef4444' : '#94a3b8';
    }
}

async function togglePii() {
    currentPrivacy.pii_enabled = !currentPrivacy.pii_enabled;
    try {
        const res = await fetch('/v1/privacy/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentPrivacy)
        });
        const data = await res.json();
        if (data.privacy) currentPrivacy = data.privacy;
        updatePrivacyUI();
    } catch (e) { alert('Error toggling PII: ' + e.message); }
}

async function toggleStealth() {
    currentPrivacy.stealth_mode = !currentPrivacy.stealth_mode;
    try {
        const res = await fetch('/v1/privacy/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentPrivacy)
        });
        const data = await res.json();
        if (data.privacy) currentPrivacy = data.privacy;
        updatePrivacyUI();
        alert(currentPrivacy.stealth_mode ? '🔒 Stealth Mode ACTIVE: All requests restricted to localhost/LAN.' : '🌐 Stealth Mode OFF: Cloud routing enabled.');
    } catch (e) { alert('Error toggling Stealth: ' + e.message); }
}

// ---------- Multi-Model Battle Arena Controller ----------
async function runBattleArena() {
    const modelA = document.getElementById('arena-model-a').value.trim();
    const modelB = document.getElementById('arena-model-b').value.trim();
    const modelC = document.getElementById('arena-model-c').value.trim();
    const prompt = document.getElementById('arena-prompt').value.trim();
    const grid = document.getElementById('arena-results-grid');
    const btn = document.getElementById('btn-run-arena');

    if (!prompt) { alert('Enter a prompt for the arena battle'); return; }
    const candidates = [];
    if (modelA) candidates.push({ model: modelA });
    if (modelB) candidates.push({ model: modelB });
    if (modelC) candidates.push({ model: modelC });

    if (!candidates.length) { alert('Specify at least one candidate model'); return; }

    btn.disabled = true;
    btn.innerText = '⚔️ Battle in Progress...';
    grid.innerHTML = candidates.map(c => `
        <div class="stat-card" style="flex-direction: column; align-items: flex-start; gap: 10px;">
            <div style="font-weight: 600; color: #38bdf8;">🥊 ${escapeHtml(c.model)}</div>
            <div style="color: var(--text-muted); font-size: 13px;">⏳ Generating response...</div>
        </div>
    `).join('');

    try {
        const res = await fetch('/v1/arena/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, candidates, max_tokens: 512, temperature: 0.7 })
        });
        const data = await res.json();
        const results = data.results || [];
        grid.innerHTML = results.map(r => `
            <div class="stat-card" style="flex-direction: column; align-items: flex-start; gap: 8px; border: 1px solid var(--border); background: var(--bg-card);">
                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                    <strong style="color: #38bdf8; font-size: 14px;">🥊 ${escapeHtml(r.model)}</strong>
                    <span class="badge ${r.ok ? 'badge-green' : 'badge-red'}">${r.ok ? r.latency_ms + ' ms' : 'Failed'}</span>
                </div>
                <div style="display: flex; gap: 12px; font-size: 11px; color: var(--text-muted);">
                    <span><strong>Tokens:</strong> ${r.total_tokens || 0}</span>
                    <span><strong>Cost:</strong> $${(r.cost_usd || 0).toFixed(6)}</span>
                </div>
                <div class="code-font" style="font-size: 12px; white-space: pre-wrap; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px; width: 100%; max-height: 280px; overflow-y: auto;">
                    ${escapeHtml(r.response || r.error || '')}
                </div>
            </div>
        `).join('');
    } catch (e) {
        alert('Arena error: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.innerText = '⚔️ Run 3-Way Battle';
    }
}

// ============================================================================
// AUTO-PROFILERS & DYNAMIC TOKEN FAILOVER ENGINE CONTROLLER
// ============================================================================
let _cachedProfiles = [];
let _activeProfFilter = 'all';

async function loadProfilers() {
    try {
        const res = await fetch('/v1/profiles');
        const data = await res.json();
        _cachedProfiles = data.profiles || [];
        const stats = data.stats || {};

        const elCount = document.getElementById('prof-count');
        const elRouted = document.getElementById('prof-routed');
        const elFailovers = document.getElementById('prof-failovers');
        if (elCount) elCount.textContent = _cachedProfiles.length;
        if (elRouted) elRouted.textContent = stats.total_routed || 0;
        if (elFailovers) elFailovers.textContent = stats.quota_failovers || stats.fallbacks_triggered || 0;

        renderProfilers(_cachedProfiles, _activeProfFilter);
    } catch (e) {
        console.error('Failed to load profiles:', e);
    }
}

// Setup profile filter buttons
document.addEventListener('click', (e) => {
    if (e.target && e.target.classList.contains('prof-filter-btn')) {
        document.querySelectorAll('.prof-filter-btn').forEach(b => {
            b.classList.remove('btn-primary', 'active');
            b.classList.add('btn-outline');
        });
        e.target.classList.remove('btn-outline');
        e.target.classList.add('btn-primary', 'active');
        _activeProfFilter = e.target.dataset.filter || 'all';
        renderProfilers(_cachedProfiles, _activeProfFilter);
    }
});

function renderProfilers(profiles, filter = 'all') {
    const container = document.getElementById('profiler-cards-container');
    if (!container) return;

    let filtered = profiles;
    if (filter !== 'all') {
        filtered = profiles.filter(p => p.category === filter);
    }

    if (!filtered || filtered.length === 0) {
        container.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:30px; color:#64748b;">No profiles found for filter '${escapeHtml(filter)}'.</div>`;
        return;
    }

    container.innerHTML = filtered.map(p => {
        const models = Array.isArray(p.models) ? p.models : [];
        const categoryBadges = {
            'free': '<span class="badge badge-success">🆓 Free Tier</span>',
            'coding': '<span class="badge badge-primary">💻 Coding</span>',
            'reasoning': '<span class="badge badge-info">🧠 Reasoning</span>',
            'fast': '<span class="badge badge-warning">⚡ Fast Latency</span>',
            'vision': '<span class="badge badge-purple">👁️ Vision</span>',
            'general': '<span class="badge badge-secondary">💬 General</span>',
            'custom': '<span class="badge badge-cyan">✨ Custom</span>'
        };

        const badgeHtml = categoryBadges[p.category] || `<span class="badge badge-secondary">${escapeHtml(p.category || 'general')}</span>`;

        const cascadeChips = models.map((m, idx) => {
            const isPrimary = idx === 0;
            const arrow = (idx < models.length - 1) ? '<span class="prof-step-arrow">➔</span>' : '';
            return `
                <span class="prof-step ${isPrimary ? 'primary' : ''}" title="Priority ${idx + 1}: ${escapeHtml(m)}">
                    ${isPrimary ? '🥇' : (idx + 1) + '.'} ${escapeHtml(m)}
                </span>
                ${arrow}
            `;
        }).join('');

        return `
            <div class="prof-card">
                <div>
                    <div class="prof-header">
                        <div>
                            <h4 class="prof-title">${escapeHtml(p.name)}</h4>
                            <div class="prof-id-tag">${escapeHtml(p.id)}</div>
                        </div>
                        <div>${badgeHtml}</div>
                    </div>
                    <div class="prof-desc">${escapeHtml(p.description || 'Intelligent fallback cascade.')}</div>

                    <div class="prof-cascade-box">
                        <div class="prof-cascade-title">
                            <span>Sequential Failover Chain</span>
                            <span>${models.length} Candidates</span>
                        </div>
                        <div class="prof-cascade-list">
                            ${cascadeChips || '<span style="color:#64748b; font-size:11px;">No models configured</span>'}
                        </div>
                    </div>

                    <div class="prof-triggers">
                        <span class="prof-trigger-chip">⚡ Rate-Limit (429) Failover</span>
                        <span class="prof-trigger-chip">🪙 Quota Failover</span>
                        <span class="prof-trigger-chip">⏱️ ${p.timeout_seconds || 25}s Timeout</span>
                    </div>
                </div>

                <div class="prof-footer">
                    <div style="display:flex; gap:6px;">
                        <button class="btn btn-xs btn-outline" onclick="copyProfileId('${escapeHtml(p.id)}')">📋 Copy ID</button>
                        <button class="btn btn-xs btn-outline" onclick="testProfileById('${escapeHtml(p.id)}')">⚡ Test</button>
                    </div>
                    <div style="display:flex; gap:6px;">
                        <button class="btn btn-xs btn-primary" onclick="injectProfileToIde('${escapeHtml(p.id)}')">🎯 Use in IDE</button>
                        ${!p.is_system_preset ? `
                            <button class="btn btn-xs btn-outline" onclick="editProfileById('${escapeHtml(p.id)}')">✏️</button>
                            <button class="btn btn-xs btn-outline" style="color:#ef4444;" onclick="deleteProfileById('${escapeHtml(p.id)}')">🗑️</button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function copyProfileId(id) {
    navigator.clipboard.writeText(id).then(() => {
        alert(`✅ Copied Profile ID: "${id}"\n\nYou can use this directly as your model name in Cursor, Continue.dev, Claude Code, OpenCode CLI, or any OpenAI API client!`);
    }).catch(() => {
        prompt('Copy Profile ID:', id);
    });
}

function openProfileEditorModal(p = null) {
    const modal = document.getElementById('modal-profile-editor');
    if (!modal) return;

    document.getElementById('pe-modal-title').textContent = p ? '✏️ Edit Auto-Profiler' : '✨ Create Auto-Profiler';
    document.getElementById('pe-id').value = p ? p.id : '';
    document.getElementById('pe-id').disabled = !!(p && p.is_system_preset);
    document.getElementById('pe-name').value = p ? p.name : '';
    document.getElementById('pe-category').value = p ? (p.category || 'coding') : 'coding';
    document.getElementById('pe-strategy').value = p ? (p.strategy || 'priority_failover') : 'priority_failover';
    document.getElementById('pe-desc').value = p ? (p.description || '') : '';
    document.getElementById('pe-models').value = p ? (Array.isArray(p.models) ? p.models.join(', ') : p.models) : 'antigravity/claude-sonnet-4-6, hy3-free, mimo-v2.5-free';
    
    modal.style.display = 'flex';
}

function closeProfileEditorModal() {
    const modal = document.getElementById('modal-profile-editor');
    if (modal) modal.style.display = 'none';
}

async function saveProfileFromModal() {
    const id = document.getElementById('pe-id').value.trim();
    const name = document.getElementById('pe-name').value.trim();
    const category = document.getElementById('pe-category').value;
    const strategy = document.getElementById('pe-strategy').value;
    const desc = document.getElementById('pe-desc').value.trim();
    const rawModels = document.getElementById('pe-models').value.trim();

    if (!name) {
        alert('Please provide a profile name.');
        return;
    }

    const models = rawModels.split(',').map(m => m.trim()).filter(m => m.length > 0);
    if (models.length === 0) {
        alert('Please specify at least 1 candidate model.');
        return;
    }

    try {
        const res = await fetch('/v1/profiles/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: id || ('profile/' + name.toLowerCase().replace(/[^a-z0-9]+/g, '-')),
                name,
                category,
                strategy,
                description: desc,
                models,
                failover_on_rate_limit: document.getElementById('pe-trig-rate').checked ? 1 : 0,
                failover_on_token_exhaustion: document.getElementById('pe-trig-quota').checked ? 1 : 0,
                failover_on_error: document.getElementById('pe-trig-error').checked ? 1 : 0,
                failover_on_timeout: document.getElementById('pe-trig-timeout').checked ? 1 : 0,
                timeout_seconds: 25.0
            })
        });
        const data = await res.json();
        if (data.status === 'ok') {
            closeProfileEditorModal();
            loadProfilers();
            alert('✅ Profile saved successfully!');
        } else {
            alert('❌ Failed to save profile: ' + (data.error || data.message));
        }
    } catch (e) {
        alert('Error saving profile: ' + e.message);
    }
}

async function deleteProfileById(id) {
    if (!confirm(`Are you sure you want to delete profile "${id}"?`)) return;
    try {
        const res = await fetch('/v1/profiles/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id })
        });
        const data = await res.json();
        if (data.status === 'ok') {
            loadProfilers();
        } else {
            alert('❌ Failed to delete: ' + data.message);
        }
    } catch (e) {
        alert('Error deleting profile: ' + e.message);
    }
}

function editProfileById(id) {
    const prof = _cachedProfiles.find(p => p.id === id);
    if (prof) openProfileEditorModal(prof);
}

function injectProfileToIde(profId) {
    const navItem = document.querySelector('.nav-item[data-tab="ide-setup"]');
    if (navItem) navItem.click();
    setTimeout(() => {
        const customModelInput = document.getElementById('custom-model-input');
        if (customModelInput) {
            customModelInput.value = profId;
            customModelInput.scrollIntoView({ behavior: 'smooth' });
        }
        alert(`🎯 Selected profile "${profId}". Click "1-Click Configure" on any IDE to activate this profile!`);
    }, 200);
}

// ── Simulator ─────────────────────────────────────────────────────────────
function openProfileSimulator() {
    const modal = document.getElementById('modal-profile-sim');
    if (!modal) return;

    const sel = document.getElementById('sim-profile-select');
    sel.innerHTML = _cachedProfiles.map(p => `
        <option value="${escapeHtml(p.id)}">${escapeHtml(p.name)} (${escapeHtml(p.id)})</option>
    `).join('');

    previewSimCascade();
    document.getElementById('sim-results').style.display = 'none';
    modal.style.display = 'flex';
}

function closeProfileSimulator() {
    const modal = document.getElementById('modal-profile-sim');
    if (modal) modal.style.display = 'none';
}

function previewSimCascade() {
    const sel = document.getElementById('sim-profile-select');
    const profId = sel.value;
    const prof = _cachedProfiles.find(p => p.id === profId);
    const preview = document.getElementById('sim-cascade-preview');
    if (!prof || !preview) return;

    const models = Array.isArray(prof.models) ? prof.models : [];
    preview.innerHTML = `
        <div style="font-weight:600; color:#38bdf8; margin-bottom:6px;">Target Cascade (${models.length} models):</div>
        <div style="display:flex; flex-direction:column; gap:4px;">
            ${models.map((m, idx) => `
                <div style="display:flex; justify-content:space-between; color:#94a3b8;">
                    <span>${idx + 1}. <code>${escapeHtml(m)}</code></span>
                    <span style="color:#10b981;">Ready</span>
                </div>
            `).join('')}
        </div>
    `;
}

async function runLiveProfileSimulation() {
    const sel = document.getElementById('sim-profile-select');
    const profId = sel.value;
    const btn = document.getElementById('btn-run-sim');
    const resBox = document.getElementById('sim-results');

    btn.disabled = true;
    btn.textContent = '⏳ Testing Dynamic Failover...';
    resBox.style.display = 'block';
    resBox.innerHTML = '<div style="color:#38bdf8;">⚡ Dispatching live test request through router...</div>';

    try {
        const res = await fetch('/v1/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: profId,
                messages: [{ role: 'user', content: 'Say "Profile Online" in 2 words.' }],
                max_tokens: 30
            })
        });
        const data = await res.json();
        if (data.choices && data.choices[0]) {
            resBox.innerHTML = `
                <div style="color:#10b981; font-weight:700; font-size:14px; margin-bottom:8px;">✅ Profile Route Succeeded!</div>
                <div style="color:#cbd5e1; margin-bottom:6px;"><strong>Active Model Selected:</strong> <code>${escapeHtml(data.model || profId)}</code></div>
                <div style="color:#cbd5e1; margin-bottom:6px;"><strong>Response:</strong> ${escapeHtml(data.choices[0].message?.content || '')}</div>
                <div style="color:#64748b; font-size:11px;">Latency: ${data.latency_ms || 350}ms • Quota Failover Engine: Active</div>
            `;
        } else {
            resBox.innerHTML = `<div style="color:#ef4444;">❌ Error: ${escapeHtml(JSON.stringify(data.error || data))}</div>`;
        }
    } catch (e) {
        resBox.innerHTML = `<div style="color:#ef4444;">❌ Network Error: ${escapeHtml(e.message)}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '🚀 Run Real-Time Test';
    }
}

async function testProfileById(id) {
    try {
        const res = await fetch('/v1/profiles/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_id: id })
        });
        const data = await res.json();
        if (data.cascade) {
            const chain = data.cascade.map((c, i) => `${i + 1}. [${c.provider}] ${c.model}`).join('\n');
            alert(`✅ Profile "${id}" is ACTIVE & READY!\n\nResolved Failover Cascade (${data.routes_count} nodes):\n${chain}`);
        }
    } catch (e) {
        alert('Test error: ' + e.message);
    }
}

// Global exports for inline HTML onclick handlers
window.deleteProvider = deleteProvider;
window.editProviderByName = editProviderByName;
window.deleteVirtualKey = deleteVirtualKey;
window.revokeVirtualKey = revokeVirtualKey;
window.adminDeleteUser = adminDeleteUser;
window.injectIde = injectIde;
window.restoreIde = restoreIde;
window.openProviderForm = openProviderForm;
window.closeProviderModal = closeProviderModal;
window.saveProvider = saveProvider;
window.copyText = copyText;
window.onProviderAuthTypeChange = onProviderAuthTypeChange;
window.triggerModalOAuthFlow = triggerModalOAuthFlow;

// Auto-Profilers exports
window.loadProfilers = loadProfilers;
window.openProfileEditorModal = openProfileEditorModal;
window.closeProfileEditorModal = closeProfileEditorModal;
window.saveProfileFromModal = saveProfileFromModal;
window.deleteProfileById = deleteProfileById;
window.editProfileById = editProfileById;
window.copyProfileId = copyProfileId;
window.injectProfileToIde = injectProfileToIde;
window.openProfileSimulator = openProfileSimulator;
window.closeProfileSimulator = closeProfileSimulator;
window.previewSimCascade = previewSimCascade;
window.runLiveProfileSimulation = runLiveProfileSimulation;
window.testProfileById = testProfileById;


