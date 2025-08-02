document.addEventListener('DOMContentLoaded', () => {
    // ---- ESTADO E CONSTANTES GLOBAIS ----
    let targets = [];
    const settingsModal = new bootstrap.Modal(document.getElementById('settingsModal'));
    const assetModal = new bootstrap.Modal(document.getElementById('assetModal'));
    const notificationToast = new bootstrap.Toast(document.getElementById('notificationToast'));

    const targetForm = document.getElementById('target-form');
    const targetIdInput = document.getElementById('target-id');
    const targetNameInput = document.getElementById('target-name');
    const targetUrlInput = document.getElementById('target-url');
    const targetDescriptionInput = document.getElementById('target-description');
    const targetList = document.getElementById('target-list');
    const dashboardGrid = document.getElementById('dashboard-grid');
    
    // ---- FUNÇÕES DE INICIALIZAÇÃO E PERSISTÊNCIA ----
    const loadTargetsFromStorage = () => {
        const storedTargets = localStorage.getItem('spectre-targets');
        targets = storedTargets ? JSON.parse(storedTargets) : [];
    };

    const saveTargetsToStorage = () => {
        localStorage.setItem('spectre-targets', JSON.stringify(targets));
    };
    
    // ---- FUNÇÕES DE RENDERIZAÇÃO ----
    const renderTargetList = () => {
        targetList.innerHTML = '';
        if (targets.length === 0) {
            targetList.innerHTML = '<li class="list-group-item">Nenhum alvo configurado.</li>';
            return;
        }
        targets.forEach((target, index) => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            li.innerHTML = `
                <div>
                    <strong>${target.name}</strong>
                    <small class="d-block text-muted">${target.url}</small>
                </div>
                <div>
                    <button class="btn btn-sm btn-outline-info me-2" onclick="app.editTarget(${index})"><i class="bi bi-pencil-fill"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="app.deleteTarget(${index})"><i class="bi bi-trash-fill"></i></button>
                </div>
            `;
            targetList.appendChild(li);
        });
    };

    const renderDashboard = () => {
        dashboardGrid.innerHTML = '';
        if (targets.length === 0) {
            dashboardGrid.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info text-center">
                        <h4>NENHUM ALVO CONFIGURADO</h4>
                        <p>Abra as <strong>Configurações</strong> <i class="bi bi-gear-fill"></i> para adicionar seu primeiro servidor.</p>
                    </div>
                </div>
            `;
            return;
        }
        targets.forEach((target, index) => {
            fetchTargetStatus(target, index);
        });
    };

    const createStatusCard = (target, index, statusData, error = null) => {
        let statusIndicator, statusText, deviceCount, cardBody;
        if (error) {
            statusIndicator = 'status-desconhecido';
            statusText = 'FALHA NA CONEXÃO';
            deviceCount = 'N/A';
            cardBody = `<p class="card-text text-danger">Erro ao interrogar o alvo: ${error.message}</p>`;
        } else {
            const isOnline = statusData.cloudflared_process_running;
            statusIndicator = isOnline ? 'status-integro' : 'status-inoperante';
            statusText = isOnline ? 'ÍNTEGRO' : 'INOPERANTE';
            deviceCount = statusData.shared_device_count;
            cardBody = `
                <p class="card-text">
                    <span class="status-indicator ${statusIndicator}"></span>
                    <strong>Status do Túnel:</strong> ${statusText}
                </p>
                <p class="card-text">
                    <i class="bi bi-usb-drive-fill"></i>
                    <strong>Dispositivos Compartilhados:</strong> 
                    <span class="badge bg-primary fs-6">${deviceCount}</span>
                </p>
            `;
        }

        const card = `
            <div class="col">
                <div class="card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span>${target.name}</span>
                        <i class="bi bi-reception-4 text-info"></i>
                    </div>
                    <div class="card-body">
                        ${cardBody}
                    </div>
                    <div class="card-footer text-center">
                        <button class="btn btn-outline-warning w-100" onclick="app.openAssetModal(${index})" ${error ? 'disabled' : ''}>
                            <i class="bi bi-joystick"></i> CONTROLAR ATIVOS
                        </button>
                    </div>
                </div>
            </div>
        `;
        dashboardGrid.innerHTML += card;
    };

    const renderAssetTable = (devices, targetIndex) => {
        const container = document.getElementById('asset-table-container');
        if (devices.length === 0) {
            container.innerHTML = '<p class="text-center">Nenhum ativo encontrado para este alvo.</p>';
            return;
        }
        
        let tableHTML = `
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th>Descrição do Ativo</th>
                        <th>ID de Combate</th>
                        <th>Status Operacional</th>
                        <th class="text-center">Ordem</th>
                    </tr>
                </thead>
                <tbody>
        `;

        devices.forEach(device => {
            const isActionable = device.status === 'shared' || device.status === 'connected' || device.status === 'unshared';
            const isShared = device.status === 'shared' || device.status === 'connected';
            const buttonClass = isShared ? 'btn-cease' : 'btn-share';
            const buttonText = isShared ? 'CESSAR' : 'COMPARTILHAR';
            const action = isShared ? 'unshare' : 'share';

            tableHTML += `
                <tr>
                    <td>${device.description}</td>
                    <td><code>${device.devID}</code></td>
                    <td><span class="badge bg-${device.status === 'connected' ? 'success' : 'secondary'}">${device.status.toUpperCase()}</span></td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-ordem ${buttonClass}" 
                                data-action="${action}" 
                                data-devid="${device.devID}" 
                                data-target-index="${targetIndex}"
                                ${!isActionable ? 'disabled' : ''}>
                            <span>${buttonText}</span>
                        </button>
                    </td>
                </tr>
            `;
        });

        tableHTML += '</tbody></table>';
        container.innerHTML = tableHTML;
    };
    
    // ---- LÓGICA DE API E EVENTOS ----
    const fetchTargetStatus = async (target, index) => {
        try {
            const response = await fetch(`${target.url}/status`, { signal: AbortSignal.timeout(8000) });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            createStatusCard(target, index, data);
        } catch (error) {
            createStatusCard(target, index, null, error);
        }
    };
    
    const fetchAssets = async (targetIndex) => {
        const target = targets[targetIndex];
        const container = document.getElementById('asset-table-container');
        container.innerHTML = `
            <div class="d-flex justify-content-center align-items-center p-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <span class="ms-3">Interrogando ativos...</span>
            </div>
        `;

        try {
            const response = await fetch(`${target.url}/devices`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const devices = await response.json();
            renderAssetTable(devices, targetIndex);
        } catch (error) {
            container.innerHTML = `<p class="text-center text-danger">Falha ao buscar ativos: ${error.message}</p>`;
        }
    };
    
    const handleOrder = async (event) => {
        const button = event.target.closest('button');
        if (!button) return;

        const { action, devid, targetIndex } = button.dataset;
        const target = targets[targetIndex];
        const originalContent = button.innerHTML;
        
        button.disabled = true;
        button.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div>';

        try {
            const response = await fetch(`${target.url}/${action}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ devID: devid })
            });
            const result = await response.json();
            if (response.ok && result.status === 'sucesso') {
                showToast("Ordem Executada", "ORDEM EXECUTADA COM SUCESSO", true);
                await fetchAssets(targetIndex); // Recarrega a tabela
            } else {
                throw new Error(result.message || 'Resposta inválida da API');
            }
        } catch (error) {
            showToast("Falha na Execução", `FALHA NA EXECUÇÃO DA ORDEM: ${error.message}`, false);
            button.disabled = false;
            button.innerHTML = originalContent;
        }
    };
    
    const showToast = (title, message, isSuccess) => {
        const toastEl = document.getElementById('notificationToast');
        const header = toastEl.querySelector('.toast-header');
        
        toastEl.classList.remove('text-bg-success', 'text-bg-danger');
        header.classList.remove('text-bg-success', 'text-bg-danger');

        const bgClass = isSuccess ? 'text-bg-success' : 'text-bg-danger';
        toastEl.classList.add(bgClass);
        
        document.getElementById('toast-title').innerText = title;
        document.getElementById('toast-body').innerText = message;
        notificationToast.show();
    };

    targetForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const id = targetIdInput.value;
        const newTarget = {
            name: targetNameInput.value.trim(),
            url: targetUrlInput.value.trim().replace(/\/$/, ""), // Remove a barra final
            description: targetDescriptionInput.value.trim(),
        };

        if (id) {
            targets[id] = newTarget;
        } else {
            targets.push(newTarget);
        }
        
        saveTargetsToStorage();
        renderTargetList();
        renderDashboard();
        targetForm.reset();
        targetIdInput.value = '';
        // settingsModal.hide(); // Opcional: fechar o modal ao salvar
    });
    
    document.getElementById('asset-table-container').addEventListener('click', handleOrder);

    // ---- API PÚBLICA DO MÓDULO `app` ----
    window.app = {
        editTarget: (index) => {
            const target = targets[index];
            targetIdInput.value = index;
            targetNameInput.value = target.name;
            targetUrlInput.value = target.url;
            targetDescriptionInput.value = target.description;
        },
        deleteTarget: (index) => {
            if (confirm(`Tem certeza que deseja remover o alvo "${targets[index].name}"?`)) {
                targets.splice(index, 1);
                saveTargetsToStorage();
                renderTargetList();
                renderDashboard();
            }
        },
        openAssetModal: (index) => {
            const target = targets[index];
            document.getElementById('assetModalLabel').innerHTML = `<i class="bi bi-hdd-stack-fill"></i> Arsenal - ${target.name}`;
            assetModal.show();
            fetchAssets(index);
        }
    };

    // ---- INICIALIZAÇÃO DA APLICAÇÃO ----
    loadTargetsFromStorage();
    renderTargetList();
    renderDashboard();
});