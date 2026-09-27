// STATIX PRO - Frontend Controller & High-Precision Canvas Renderers

let currentTab = 'tab-beams';
let allPresets = {};
let lastBeamResults = null;
let lastTrussResults = null;

// Initial Model States
let beamModel = {
    length: 12.0,
    supports: [
        { x: 0.0, type: 'pin' },
        { x: 8.0, type: 'roller' }
    ],
    hinges: [],
    point_loads: [
        { x: 12.0, fy: -50.0, fx: 0.0 }
    ],
    moments: [],
    dist_loads: [
        { x1: 0.0, x2: 8.0, w1: -20.0, w2: -20.0 }
    ]
};

let trussModel = {
    nodes: [
        { x: 0, y: 0 }, { x: 4, y: 0 }, { x: 8, y: 0 }, { x: 12, y: 0 },
        { x: 4, y: 3 }, { x: 8, y: 3 }
    ],
    elements: [
        { node1: 0, node2: 1 }, { node1: 1, node2: 2 }, { node1: 2, node2: 3 },
        { node1: 4, node2: 5 },
        { node1: 0, node2: 4 }, { node1: 1, node2: 4 },
        { node1: 1, node2: 5 }, { node1: 2, node2: 5 }, { node1: 3, node2: 5 }
    ],
    supports: [
        { node: 0, type: 'pin' },
        { node: 3, type: 'roller' }
    ],
    loads: [
        { node: 1, fx: 0, fy: -30000 },
        { node: 2, fx: 0, fy: -30000 }
    ]
};

let centroidShapes = [
    { type: 'rectangle', x: 40, y: 0, w: 20, h: 120, subtract: false },
    { type: 'rectangle', x: 0, y: 120, w: 100, h: 20, subtract: false },
    { type: 'circle', xc: 50, yc: 60, r: 15, subtract: true }
];

let inertiaShapes = [
    { type: 'rectangle', x: 0, y: 0, w: 100, h: 20, subtract: false },
    { type: 'rectangle', x: 0, y: 20, w: 20, h: 130, subtract: false }
];

// PWA Installation Deferred Prompt
let deferredPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const installBtn = document.getElementById('btnInstallPwa');
    if (installBtn) installBtn.style.display = 'inline-flex';
});

// Document Ready
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initPresets();
    initMobileControls();
    initPwa();
    renderBeamUI();
    renderTrussUI();
    renderCentroidUI();
    renderInertiaUI();

    // Auto solve initial beam on startup
    solveBeam();

    document.getElementById('btnSolve').addEventListener('click', runActiveTabSolver);
    document.getElementById('btnExport').addEventListener('click', copyResultsToClipboard);
    document.getElementById('btnLoadPreset').addEventListener('click', loadSelectedPreset);
});

// Register Service Worker for PWA (Android & Desktop)
function initPwa() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(err => {
            console.log('ServiceWorker registration failed: ', err);
        });
    }

    const installBtn = document.getElementById('btnInstallPwa');
    if (installBtn) {
        installBtn.addEventListener('click', async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') {
                    installBtn.style.display = 'none';
                }
                deferredPrompt = null;
            }
        });
    }
}

// Mobile sidebar & QR Modal
function initMobileControls() {
    const toggleBtn = document.getElementById('btnToggleSidebar');
    const sidebar = document.querySelector('.sidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });

        // Close sidebar when a nav item is clicked on mobile
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                sidebar.classList.remove('open');
            });
        });
    }

    const connectBtn = document.getElementById('btnConnectMobile');
    if (connectBtn) {
        connectBtn.addEventListener('click', openMobileModal);
    }
}

async function openMobileModal() {
    const modal = document.getElementById('mobileModal');
    if (!modal) return;
    modal.style.display = 'flex';

    try {
        const res = await fetch('/api/network-info');
        const data = await res.json();
        const img = document.getElementById('qrCodeImg');
        const txt = document.getElementById('mobileUrlText');
        if (img) img.src = data.qr_code;
        if (txt) txt.textContent = data.url;
    } catch (err) {
        console.error("Failed to load network info:", err);
    }
}

window.closeMobileModal = () => {
    const modal = document.getElementById('mobileModal');
    if (modal) modal.style.display = 'none';
};

window.copyMobileUrl = () => {
    const txt = document.getElementById('mobileUrlText').textContent;
    navigator.clipboard.writeText(txt).then(() => {
        alert("آدرس در کلیپ‌بورد کپی شد: " + txt);
    });
};

// --- Tab Navigation ---
function initTabs() {
    const navButtons = document.querySelectorAll('.nav-item');
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const tabId = btn.getAttribute('data-tab');
            currentTab = tabId;

            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            const targetPanel = document.getElementById(tabId);
            if (targetPanel) targetPanel.classList.add('active');

            // Trigger immediate render/calculation for newly active tab
            setTimeout(() => {
                if (tabId === 'tab-beams') drawBeamModel();
                else if (tabId === 'tab-trusses') solveTruss();
                else if (tabId === 'tab-centroids') solveCentroids();
                else if (tabId === 'tab-inertia') solveInertia();
                else if (tabId === 'tab-cables') solveParabolicCable();
                else if (tabId === 'tab-friction') solveFrictionSlipTip();
            }, 50);
        });
    });
}

// --- Presets Management ---
async function initPresets() {
    try {
        const res = await fetch('/api/presets');
        const data = await res.json();
        allPresets = data.presets;

        const dropdown = document.getElementById('presetDropdown');
        dropdown.innerHTML = '<option value="">انتخاب مسئله الگو از کتاب بیر جانسون...</option>';

        for (const [category, list] of Object.entries(allPresets)) {
            const optgroup = document.createElement('optgroup');
            optgroup.label = getCategoryTitle(category);

            list.forEach(p => {
                const opt = document.createElement('option');
                opt.value = `${category}:${p.id}`;
                opt.textContent = p.name;
                optgroup.appendChild(opt);
            });
            dropdown.appendChild(optgroup);
        }
    } catch (err) {
        console.error("Failed to load presets:", err);
    }
}

function getCategoryTitle(cat) {
    const map = {
        beams: 'فصل ۷: تیرها و قاب‌ها',
        trusses: 'فصل ۶: خرپاها',
        vectors: 'فصل ۲ و ۳: بردارها و ذره',
        centroids: 'فصل ۵: مرکز سطح',
        inertia: 'فصل ۹: ممان اینرسی',
        friction: 'فصل ۸: اصطکاک',
        cables: 'فصل ۷: کابل‌ها'
    };
    return map[cat] || cat;
}

function loadSelectedPreset() {
    const val = document.getElementById('presetDropdown').value;
    if (!val) return;
    const [category, presetId] = val.split(':');
    const preset = allPresets[category]?.find(p => p.id === presetId);
    if (!preset) return;

    if (category === 'beams') {
        beamModel = JSON.parse(JSON.stringify(preset.data));
        document.getElementById('beamLength').value = beamModel.length;
        renderBeamUI();
        switchTab('tab-beams');
        solveBeam();
    } else if (category === 'trusses') {
        trussModel = JSON.parse(JSON.stringify(preset.data));
        renderTrussUI();
        switchTab('tab-trusses');
        solveTruss();
    } else if (category === 'centroids') {
        centroidShapes = JSON.parse(JSON.stringify(preset.data.shapes));
        renderCentroidUI();
        switchTab('tab-centroids');
        solveCentroids();
    } else if (category === 'inertia') {
        inertiaShapes = JSON.parse(JSON.stringify(preset.data.shapes));
        renderInertiaUI();
        switchTab('tab-inertia');
        solveInertia();
    } else if (category === 'friction') {
        if (preset.data.weight_W !== undefined) {
            document.getElementById('fricW').value = preset.data.weight_W;
            document.getElementById('fricB').value = preset.data.width_b;
            document.getElementById('fricH').value = preset.data.height_h;
            document.getElementById('fricY').value = preset.data.force_height_y;
            document.getElementById('fricTheta').value = preset.data.incline_theta_deg;
            document.getElementById('fricMu').value = preset.data.mu_s;
            switchTab('tab-friction');
            solveFrictionSlipTip();
        }
    } else if (category === 'cables') {
        if (preset.data.span_L !== undefined) {
            document.getElementById('cableSpan').value = preset.data.span_L;
            document.getElementById('cableSag').value = preset.data.sag_h;
            document.getElementById('cableLoad').value = preset.data.w_per_m;
            switchTab('tab-cables');
            solveParabolicCable();
        }
    }
}

function switchTab(tabId) {
    const btn = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
    if (btn) btn.click();
}

function runActiveTabSolver() {
    if (currentTab === 'tab-beams') solveBeam();
    else if (currentTab === 'tab-trusses') solveTruss();
    else if (currentTab === 'tab-vectors') solveVectorMath();
    else if (currentTab === 'tab-rigid') solveRigidMoment();
    else if (currentTab === 'tab-centroids') solveCentroids();
    else if (currentTab === 'tab-inertia') solveInertia();
    else if (currentTab === 'tab-cables') solveParabolicCable();
    else if (currentTab === 'tab-friction') solveFrictionSlipTip();
    else if (currentTab === 'tab-virtual') solveVirtualWork();
}

// =========================================================================
// MODULE 1: BEAMS & SFD/BMD
// =========================================================================

function renderBeamUI() {
    // Supports list
    const supList = document.getElementById('beamSupportsList');
    supList.innerHTML = '';
    beamModel.supports.forEach((s, idx) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item-row';
        row.innerHTML = `
            <span>x:</span>
            <input type="number" class="form-control" style="width: 70px" value="${s.x}" step="0.5" onchange="updateBeamSupport(${idx}, 'x', this.value)">
            <select class="form-select" onchange="updateBeamSupport(${idx}, 'type', this.value)">
                <option value="pin" ${s.type === 'pin' ? 'selected' : ''}>مفصلی (Pin)</option>
                <option value="roller" ${s.type === 'roller' ? 'selected' : ''}>غلطکی (Roller)</option>
                <option value="fixed" ${s.type === 'fixed' ? 'selected' : ''}>گیردار (Fixed)</option>
            </select>
            <button class="btn btn-sm btn-danger" onclick="removeBeamSupport(${idx})">✕</button>
        `;
        supList.appendChild(row);
    });

    // Hinges list
    const hList = document.getElementById('beamHingesList');
    hList.innerHTML = '';
    beamModel.hinges.forEach((hx, idx) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item-row';
        row.innerHTML = `
            <span>x:</span>
            <input type="number" class="form-control" style="width: 80px" value="${hx}" step="0.5" onchange="updateBeamHinge(${idx}, this.value)">
            <button class="btn btn-sm btn-danger" onclick="removeBeamHinge(${idx})">✕</button>
        `;
        hList.appendChild(row);
    });

    // Point loads list
    const plList = document.getElementById('beamPointLoadsList');
    plList.innerHTML = '';
    beamModel.point_loads.forEach((p, idx) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item-row';
        row.innerHTML = `
            <span>x:</span>
            <input type="number" class="form-control" style="width: 65px" value="${p.x}" step="0.5" onchange="updateBeamPointLoad(${idx}, 'x', this.value)">
            <span>Fy (kN):</span>
            <input type="number" class="form-control" style="width: 75px" value="${p.fy}" step="5" onchange="updateBeamPointLoad(${idx}, 'fy', this.value)" title="منفی برای بار رو به پایین">
            <button class="btn btn-sm btn-danger" onclick="removeBeamPointLoad(${idx})">✕</button>
        `;
        plList.appendChild(row);
    });

    // Moments list
    const mList = document.getElementById('beamMomentsList');
    mList.innerHTML = '';
    beamModel.moments.forEach((m, idx) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item-row';
        row.innerHTML = `
            <span>x:</span>
            <input type="number" class="form-control" style="width: 65px" value="${m.x}" step="0.5" onchange="updateBeamMoment(${idx}, 'x', this.value)">
            <span>M (kN.m):</span>
            <input type="number" class="form-control" style="width: 75px" value="${m.m}" step="5" onchange="updateBeamMoment(${idx}, 'm', this.value)" title="مثبت برای پادساعت‌گرد">
            <button class="btn btn-sm btn-danger" onclick="removeBeamMoment(${idx})">✕</button>
        `;
        mList.appendChild(row);
    });

    // Distributed loads list
    const dlList = document.getElementById('beamDistLoadsList');
    dlList.innerHTML = '';
    beamModel.dist_loads.forEach((d, idx) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item-row';
        row.innerHTML = `
            <span>از:</span>
            <input type="number" class="form-control" style="width: 50px" value="${d.x1}" step="0.5" onchange="updateBeamDistLoad(${idx}, 'x1', this.value)">
            <span>تا:</span>
            <input type="number" class="form-control" style="width: 50px" value="${d.x2}" step="0.5" onchange="updateBeamDistLoad(${idx}, 'x2', this.value)">
            <span>w1:</span>
            <input type="number" class="form-control" style="width: 55px" value="${d.w1}" step="5" onchange="updateBeamDistLoad(${idx}, 'w1', this.value)">
            <span>w2:</span>
            <input type="number" class="form-control" style="width: 55px" value="${d.w2}" step="5" onchange="updateBeamDistLoad(${idx}, 'w2', this.value)">
            <button class="btn btn-sm btn-danger" onclick="removeBeamDistLoad(${idx})">✕</button>
        `;
        dlList.appendChild(row);
    });

    drawBeamModel();
}

// Add/Remove Helpers for Beams
window.addBeamSupportRow = () => { beamModel.supports.push({ x: 0, type: 'roller' }); renderBeamUI(); };
window.removeBeamSupport = (idx) => { beamModel.supports.splice(idx, 1); renderBeamUI(); };
window.updateBeamSupport = (idx, field, val) => { beamModel.supports[idx][field] = field === 'x' ? parseFloat(val) : val; drawBeamModel(); };

window.addBeamHingeRow = () => { beamModel.hinges.push(beamModel.length / 2); renderBeamUI(); };
window.removeBeamHinge = (idx) => { beamModel.hinges.splice(idx, 1); renderBeamUI(); };
window.updateBeamHinge = (idx, val) => { beamModel.hinges[idx] = parseFloat(val); drawBeamModel(); };

window.addBeamPointLoadRow = () => { beamModel.point_loads.push({ x: beamModel.length / 2, fy: -20, fx: 0 }); renderBeamUI(); };
window.removeBeamPointLoad = (idx) => { beamModel.point_loads.splice(idx, 1); renderBeamUI(); };
window.updateBeamPointLoad = (idx, field, val) => { beamModel.point_loads[idx][field] = parseFloat(val); drawBeamModel(); };

window.addBeamMomentRow = () => { beamModel.moments.push({ x: beamModel.length / 2, m: 20 }); renderBeamUI(); };
window.removeBeamMoment = (idx) => { beamModel.moments.splice(idx, 1); renderBeamUI(); };
window.updateBeamMoment = (idx, field, val) => { beamModel.moments[idx][field] = parseFloat(val); drawBeamModel(); };

window.addBeamDistLoadRow = () => { beamModel.dist_loads.push({ x1: 0, x2: beamModel.length, w1: -10, w2: -10 }); renderBeamUI(); };
window.removeBeamDistLoad = (idx) => { beamModel.dist_loads.splice(idx, 1); renderBeamUI(); };
window.updateBeamDistLoad = (idx, field, val) => { beamModel.dist_loads[idx][field] = parseFloat(val); drawBeamModel(); };

document.getElementById('beamLength').addEventListener('input', (e) => {
    beamModel.length = parseFloat(e.target.value) || 1.0;
    drawBeamModel();
});

async function solveBeam() {
    let data;
    try {
        const res = await fetch('/api/solve/beam', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(beamModel)
        });
        if (!res.ok) throw new Error();
        data = await res.json();
    } catch (err) {
        // 100% Offline Standalone Android Engine Fallback
        data = StatixEngine.solveBeam(beamModel);
    }

    lastBeamResults = data;

        // Update Badges
        document.getElementById('sfdExtremaBadge').textContent = `V_max = ${data.max_shear} kN | V_min = ${data.min_shear} kN`;
        document.getElementById('bmdExtremaBadge').textContent = `M_max = ${data.max_moment} kN.m | M_min = ${data.min_moment} kN.m`;

        // Update Reactions Table
        const tbody = document.querySelector('#beamReactionsTable tbody');
        tbody.innerHTML = '';
        data.supports.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${s.x} m</td>
                <td>${s.type === 'pin' ? 'مفصلی' : s.type === 'roller' ? 'غلطکی' : 'گیردار'}</td>
                <td style="color: ${s.Ry >= 0 ? '#10b981' : '#f43f5e'}">${s.Ry}</td>
                <td>${s.Rm !== 0 ? s.Rm : '0'}</td>
            `;
            tbody.appendChild(tr);
        });

        // Summary Box
        const critList = document.getElementById('beamCriticalPointsList');
        critList.innerHTML = `
            <li>بیشینه نیروی برشی: <strong>${Math.max(Math.abs(data.max_shear), Math.abs(data.min_shear))} kN</strong></li>
            <li>بیشینه لنگر خمشی: <strong>${Math.max(Math.abs(data.max_moment), Math.abs(data.min_moment))} kN.m</strong></li>
            <li>موقعیت‌های صفر شدن برش (بیشینه نسبی لنگر): <strong>${data.zero_shear_locations.length > 0 ? data.zero_shear_locations.join(' m , ') + ' m' : 'بدون نقطه عطف'}</strong></li>
        `;

        drawBeamModel();
        drawSFD(data.data_points);
        drawBMD(data.data_points);
    } catch (err) {
        alert("خطا: " + err.message);
    }
}

// Canvas Drawing for Beam Structural Model
function drawBeamModel() {
    const canvas = document.getElementById('beamCanvas');
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    const L = beamModel.length;
    const marginX = 80;
    const beamY = h / 2 + 10;
    const scaleX = (w - 2 * marginX) / L;

    // Beam Line (Thick high-contrast cyan-white)
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 8;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(marginX, beamY);
    ctx.lineTo(marginX + L * scaleX, beamY);
    ctx.stroke();

    // Supports
    beamModel.supports.forEach(s => {
        const sx = marginX + s.x * scaleX;
        ctx.fillStyle = '#fbbf24';
        ctx.strokeStyle = '#d97706';
        ctx.lineWidth = 2;

        if (s.type === 'pin') {
            // Triangle with ground hatch
            ctx.beginPath();
            ctx.moveTo(sx, beamY);
            ctx.lineTo(sx - 12, beamY + 22);
            ctx.lineTo(sx + 12, beamY + 22);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            // Ground hatch line
            ctx.strokeStyle = '#64748b';
            ctx.beginPath();
            ctx.moveTo(sx - 16, beamY + 23);
            ctx.lineTo(sx + 16, beamY + 23);
            ctx.stroke();
        } else if (s.type === 'roller') {
            // Triangle + roller circles
            ctx.beginPath();
            ctx.moveTo(sx, beamY);
            ctx.lineTo(sx - 12, beamY + 16);
            ctx.lineTo(sx + 12, beamY + 16);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            // Rollers
            ctx.beginPath();
            ctx.arc(sx - 6, beamY + 20, 3, 0, Math.PI * 2);
            ctx.arc(sx + 6, beamY + 20, 3, 0, Math.PI * 2);
            ctx.fillStyle = '#94a3b8';
            ctx.fill();
        } else if (s.type === 'fixed') {
            // Hatch wall
            ctx.fillStyle = '#475569';
            ctx.fillRect(sx - 8, beamY - 30, 8, 60);
        }

        // Support position label
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px JetBrains Mono';
        ctx.textAlign = 'center';
        ctx.fillText(`x=${s.x}m`, sx, beamY + 36);
    });

    // Internal Hinges
    beamModel.hinges.forEach(hx => {
        const h_canvas_x = marginX + hx * scaleX;
        ctx.fillStyle = '#090d16';
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(h_canvas_x, beamY, 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = '#ffffff';
        ctx.font = '10px Vazirmatn';
        ctx.textAlign = 'center';
        ctx.fillText('مفصل', h_canvas_x, beamY - 12);
    });

    // Distributed Loads (Shaded trapezoids + arrows)
    beamModel.dist_loads.forEach(d => {
        const x1 = marginX + d.x1 * scaleX;
        const x2 = marginX + d.x2 * scaleX;
        const h1 = (Math.abs(d.w1) / 30) * 40;
        const h2 = (Math.abs(d.w2) / 30) * 40;

        ctx.fillStyle = 'rgba(244, 63, 94, 0.2)';
        ctx.strokeStyle = '#f43f5e';
        ctx.lineWidth = 1.5;

        ctx.beginPath();
        ctx.moveTo(x1, beamY);
        ctx.lineTo(x1, beamY - h1);
        ctx.lineTo(x2, beamY - h2);
        ctx.lineTo(x2, beamY);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Downward arrows across distributed load
        const numArrows = Math.max(3, Math.floor((x2 - x1) / 25));
        for (let i = 0; i <= numArrows; i++) {
            const ax = x1 + (i / numArrows) * (x2 - x1);
            const loadH = h1 + (i / numArrows) * (h2 - h1);
            if (loadH > 5) {
                drawArrow(ctx, ax, beamY - loadH, ax, beamY - 2, '#f43f5e');
            }
        }
    });

    // Point Loads (Arrows)
    beamModel.point_loads.forEach(p => {
        const px = marginX + p.x * scaleX;
        const isDown = p.fy < 0;
        ctx.strokeStyle = '#f43f5e';
        ctx.fillStyle = '#f43f5e';
        const arrowLen = 50;

        if (isDown) {
            drawArrow(ctx, px, beamY - arrowLen, px, beamY - 4, '#f43f5e', 8);
            ctx.font = 'bold 11px JetBrains Mono';
            ctx.textAlign = 'center';
            ctx.fillText(`${Math.abs(p.fy)} kN`, px, beamY - arrowLen - 6);
        } else {
            drawArrow(ctx, px, beamY + arrowLen, px, beamY + 4, '#10b981', 8);
            ctx.font = 'bold 11px JetBrains Mono';
            ctx.textAlign = 'center';
            ctx.fillText(`${p.fy} kN`, px, beamY + arrowLen + 14);
        }
    });

    // Moments (Circular arrows)
    beamModel.moments.forEach(m => {
        const mx = marginX + m.x * scaleX;
        ctx.strokeStyle = '#a855f7';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.arc(mx, beamY - 15, 18, 0.2 * Math.PI, 1.8 * Math.PI, m.m < 0);
        ctx.stroke();
        ctx.fillStyle = '#a855f7';
        ctx.font = 'bold 11px JetBrains Mono';
        ctx.textAlign = 'center';
        ctx.fillText(`${m.m} kN.m`, mx, beamY - 38);
    });
}

function drawArrow(ctx, fromx, fromy, tox, toy, color = '#f43f5e', headlen = 7) {
    const angle = Math.atan2(toy - fromy, tox - fromx);
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(fromx, fromy);
    ctx.lineTo(tox, toy);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(tox, toy);
    ctx.lineTo(tox - headlen * Math.cos(angle - Math.PI / 6), toy - headlen * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(tox - headlen * Math.cos(angle + Math.PI / 6), toy - headlen * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fill();
}

// Draw SFD
function drawSFD(points) {
    const canvas = document.getElementById('sfdCanvas');
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const marginX = 80;
    const marginY = 30;
    const L = beamModel.length;
    const scaleX = (w - 2 * marginX) / L;

    const maxAbsV = Math.max(...points.V.map(Math.abs), 1.0);
    const zeroY = h / 2;
    const scaleY = (h / 2 - marginY) / maxAbsV;

    // Zero Baseline
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(marginX, zeroY);
    ctx.lineTo(marginX + L * scaleX, zeroY);
    ctx.stroke();

    // SFD Curve
    ctx.beginPath();
    ctx.moveTo(marginX, zeroY);
    points.x.forEach((x, i) => {
        const cx = marginX + x * scaleX;
        const cy = zeroY - points.V[i] * scaleY;
        ctx.lineTo(cx, cy);
    });
    ctx.lineTo(marginX + L * scaleX, zeroY);
    ctx.closePath();

    // Shading
    ctx.fillStyle = 'rgba(56, 189, 248, 0.2)';
    ctx.fill();
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Text labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px JetBrains Mono';
    ctx.textAlign = 'right';
    ctx.fillText(`+${maxAbsV.toFixed(1)} kN`, marginX - 10, marginY + 10);
    ctx.fillText(`-${maxAbsV.toFixed(1)} kN`, marginX - 10, h - marginY);
    ctx.fillText('0', marginX - 10, zeroY + 4);
}

// Draw BMD
function drawBMD(points) {
    const canvas = document.getElementById('bmdCanvas');
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const marginX = 80;
    const marginY = 30;
    const L = beamModel.length;
    const scaleX = (w - 2 * marginX) / L;

    const maxAbsM = Math.max(...points.M.map(Math.abs), 1.0);
    const zeroY = h / 2;
    const scaleY = (h / 2 - marginY) / maxAbsM;

    // Zero Baseline
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(marginX, zeroY);
    ctx.lineTo(marginX + L * scaleX, zeroY);
    ctx.stroke();

    // BMD Curve (Civil engineering: sagging positive plotted downwards or upwards, standard: + up)
    ctx.beginPath();
    ctx.moveTo(marginX, zeroY);
    points.x.forEach((x, i) => {
        const cx = marginX + x * scaleX;
        const cy = zeroY - points.M[i] * scaleY;
        ctx.lineTo(cx, cy);
    });
    ctx.lineTo(marginX + L * scaleX, zeroY);
    ctx.closePath();

    // Shading
    ctx.fillStyle = 'rgba(16, 185, 129, 0.2)';
    ctx.fill();
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Text labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px JetBrains Mono';
    ctx.textAlign = 'right';
    ctx.fillText(`+${maxAbsM.toFixed(1)} kN.m`, marginX - 10, marginY + 10);
    ctx.fillText(`-${maxAbsM.toFixed(1)} kN.m`, marginX - 10, h - marginY);
    ctx.fillText('0', marginX - 10, zeroY + 4);
}

// =========================================================================
// MODULE 2: TRUSSES
// =========================================================================

function renderTrussUI() {
    const nList = document.getElementById('trussNodesList');
    nList.innerHTML = '';
    trussModel.nodes.forEach((n, idx) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item-row';
        row.innerHTML = `
            <span>#${idx} x:</span>
            <input type="number" class="form-control" style="width:65px" value="${n.x}" step="0.5" onchange="trussModel.nodes[${idx}].x=parseFloat(this.value)">
            <span>y:</span>
            <input type="number" class="form-control" style="width:65px" value="${n.y}" step="0.5" onchange="trussModel.nodes[${idx}].y=parseFloat(this.value)">
        `;
        nList.appendChild(row);
    });

    const elList = document.getElementById('trussElementsList');
    elList.innerHTML = '';
    trussModel.elements.forEach((el, idx) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item-row';
        row.innerHTML = `
            <span>عضو ${idx}: گره</span>
            <input type="number" class="form-control" style="width:50px" value="${el.node1}" onchange="trussModel.elements[${idx}].node1=parseInt(this.value)">
            <span>به گره</span>
            <input type="number" class="form-control" style="width:50px" value="${el.node2}" onchange="trussModel.elements[${idx}].node2=parseInt(this.value)">
        `;
        elList.appendChild(row);
    });

    const supList = document.getElementById('trussSupportsList');
    supList.innerHTML = '';
    trussModel.supports.forEach((s, idx) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item-row';
        row.innerHTML = `
            <span>گره #${s.node}:</span>
            <select class="form-select" onchange="trussModel.supports[${idx}].type=this.value">
                <option value="pin" ${s.type === 'pin' ? 'selected' : ''}>مفصلی (Pin)</option>
                <option value="roller" ${s.type === 'roller' ? 'selected' : ''}>غلطکی (Roller)</option>
            </select>
        `;
        supList.appendChild(row);
    });

    const ldList = document.getElementById('trussLoadsList');
    ldList.innerHTML = '';
    trussModel.loads.forEach((ld, idx) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item-row';
        row.innerHTML = `
            <span>گره #${ld.node} Fy(N):</span>
            <input type="number" class="form-control" style="width:85px" value="${ld.fy}" step="1000" onchange="trussModel.loads[${idx}].fy=parseFloat(this.value)">
        `;
        ldList.appendChild(row);
    });
}

window.addTrussNodeRow = () => { trussModel.nodes.push({ x: 0, y: 0 }); renderTrussUI(); };
window.addTrussElementRow = () => { trussModel.elements.push({ node1: 0, node2: 1 }); renderTrussUI(); };
window.addTrussSupportRow = () => { trussModel.supports.push({ node: 0, type: 'roller' }); renderTrussUI(); };
window.addTrussLoadRow = () => { trussModel.loads.push({ node: 0, fx: 0, fy: -10000 }); renderTrussUI(); };

async function solveTruss() {
    let data;
    try {
        const res = await fetch('/api/solve/truss', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(trussModel)
        });
        if (!res.ok) throw new Error();
        data = await res.json();
    } catch (err) {
        data = StatixEngine.solveTruss(trussModel);
    }

    lastTrussResults = data;

        document.getElementById('trussDeterminacyBadge').textContent =
            data.determinacy === 'determinate' ? 'معین استاتیکی' : data.determinacy;

        // Populate table
        const tbody = document.querySelector('#trussMembersTable tbody');
        tbody.innerHTML = '';
        data.members.forEach(m => {
            const tr = document.createElement('tr');
            const color = m.type === 'T' ? '#38bdf8' : m.type === 'C' ? '#f43f5e' : '#94a3b8';
            tr.innerHTML = `
                <td>${m.element_id}</td>
                <td>گره ${m.node1} - گره ${m.node2}</td>
                <td>${m.length}</td>
                <td style="color:${color}; font-weight:bold;">${m.force}</td>
                <td style="color:${color}">${m.state}</td>
                <td>${m.stress_MPa}</td>
            `;
            tbody.appendChild(tr);
        });

        drawTrussModel(data);
    } catch (err) {
        alert("خطا در خرپا: " + err.message);
    }
}

function drawTrussModel(res) {
    const canvas = document.getElementById('trussCanvas');
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const nodes = trussModel.nodes;
    const minX = Math.min(...nodes.map(n => n.x));
    const maxX = Math.max(...nodes.map(n => n.x));
    const minY = Math.min(...nodes.map(n => n.y));
    const maxY = Math.max(...nodes.map(n => n.y));

    const spanX = Math.max(maxX - minX, 1.0);
    const spanY = Math.max(maxY - minY, 1.0);

    const margin = 70;
    const scale = Math.min((w - 2 * margin) / spanX, (h - 2 * margin) / spanY);

    const toScreen = (x, y) => ({
        x: margin + (x - minX) * scale,
        y: h - margin - (y - minY) * scale
    });

    // Draw Elements
    res.members.forEach(m => {
        const n1 = nodes[m.node1];
        const n2 = nodes[m.node2];
        const p1 = toScreen(n1.x, n1.y);
        const p2 = toScreen(n2.x, n2.y);

        ctx.strokeStyle = m.type === 'T' ? '#38bdf8' : m.type === 'C' ? '#f43f5e' : '#64748b';
        ctx.lineWidth = m.type === 'ZERO' ? 2 : 4;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();

        // Label Force
        const midX = (p1.x + p2.x) / 2;
        const midY = (p1.y + p2.y) / 2;
        ctx.fillStyle = '#ffffff';
        ctx.font = '10px JetBrains Mono';
        ctx.textAlign = 'center';
        ctx.fillText(`${(m.force / 1000).toFixed(1)}k`, midX, midY - 6);
    });

    // Draw Nodes
    nodes.forEach((n, idx) => {
        const p = toScreen(n.x, n.y);
        ctx.fillStyle = '#fbbf24';
        ctx.strokeStyle = '#090d16';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 7, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px Vazirmatn';
        ctx.fillText(`#${idx}`, p.x, p.y - 12);
    });
}

// =========================================================================
// MODULE 3: VECTORS & PARTICLES
// =========================================================================

async function solveVectorMath() {
    const v1 = {
        x: parseFloat(document.getElementById('vecA_x').value),
        y: parseFloat(document.getElementById('vecA_y').value),
        z: parseFloat(document.getElementById('vecA_z').value)
    };
    const v2 = {
        x: parseFloat(document.getElementById('vecB_x').value),
        y: parseFloat(document.getElementById('vecB_y').value),
        z: parseFloat(document.getElementById('vecB_z').value)
    };

    try {
        const res = await fetch('/api/solve/vectors/dot-cross', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ v1, v2 })
        });
        const data = await res.json();
        const box = document.getElementById('vectorResultsBox');
        box.textContent =
`==============================================
تحلیل برداری سیستم (Beer & Johnston Ch 2 & 3)
==============================================
ضرب داخلی (Dot Product) A · B:
  ${data.dot_product}

زاویه بین دو بردار:
  θ = ${data.angle_deg}°

ضرب خارجی (Cross Product) A × B:
  Vector: (${data.cross_product.x})i + (${data.cross_product.y})j + (${data.cross_product.z})k
  Magnitude: |A × B| = ${data.cross_product.magnitude}

تصویر بردار A روی امتداد B:
  Proj_B(A) = ${data.projection_a_on_b}
`;
    } catch (err) {
        alert("خطا: " + err.message);
    }
}

async function solveParticleCables() {
    const w = parseFloat(document.getElementById('partLoadY').value);
    const cables = [
        { name: "کابل AB", origin: [0, 0, 0], target: [-1.2, 2.0, -0.8] },
        { name: "کابل AC", origin: [0, 0, 0], target: [1.5, 2.0, -0.6] },
        { name: "کابل AD", origin: [0, 0, 0], target: [0.0, 2.0, 1.2] }
    ];

    try {
        const res = await fetch('/api/solve/vectors/particle-equilibrium', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cables, applied_load: { fx: 0, fy: -w, fz: 0 } })
        });
        const data = await res.json();
        const box = document.getElementById('vectorResultsBox');
        let txt = `==============================================\nتعادل ذره در فضا ۳D (کابل‌ها)\n==============================================\n`;
        data.results.forEach(c => {
            txt += `• ${c.name}: کشش T = ${c.tension} N [${c.state}]\n`;
        });
        txt += `\nبررسی تعادل: ΣFx=${data.equilibrium_check.sum_fx} , ΣFy=${data.equilibrium_check.sum_fy} , ΣFz=${data.equilibrium_check.sum_fz}\n`;
        box.textContent = txt;
    } catch (err) {
        alert("خطا: " + err.message);
    }
}

// =========================================================================
// MODULE 4: RIGID BODY & MOMENTS
// =========================================================================

async function solveRigidMoment() {
    const point_o = [parseFloat(document.getElementById('pointO_x').value), parseFloat(document.getElementById('pointO_y').value), parseFloat(document.getElementById('pointO_z').value)];
    const point_a = [parseFloat(document.getElementById('pointA_x').value), parseFloat(document.getElementById('pointA_y').value), parseFloat(document.getElementById('pointA_z').value)];
    const force = [parseFloat(document.getElementById('forceF_x').value), parseFloat(document.getElementById('forceF_y').value), parseFloat(document.getElementById('forceF_z').value)];

    try {
        const res = await fetch('/api/solve/rigid-body/moment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ point_o, point_a, force })
        });
        const data = await res.json();
        const box = document.getElementById('rigidResultsBox');
        box.textContent =
`==============================================
لنگر نیرو حول نقطه (Beer & Johnston Ch 3)
==============================================
بردار موقعیت r = A - O:
  r = (${data.r_vector[0]})i + (${data.r_vector[1]})j + (${data.r_vector[2]})k

بردار لنگر Mo = r × F:
  Mx = ${data.moment_vector.Mx} N.m
  My = ${data.moment_vector.My} N.m
  Mz = ${data.moment_vector.Mz} N.m
  بزرگی لنگر: |Mo| = ${data.moment_vector.magnitude} N.m
`;
    } catch (err) {
        alert("خطا: " + err.message);
    }
}

// =========================================================================
// MODULE 5: CENTROIDS
// =========================================================================

function renderCentroidUI() {
    const list = document.getElementById('centroidShapesList');
    list.innerHTML = '';
    centroidShapes.forEach((s, idx) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item-row';
        row.innerHTML = `
            <span>#${idx+1} ${s.type === 'rectangle' ? 'مستطیل' : 'دایره'}:</span>
            ${s.type === 'rectangle' ? `w:${s.w} h:${s.h}` : `r:${s.r}`}
            <span style="color:${s.subtract ? '#f43f5e' : '#10b981'}">${s.subtract ? '(توخالی)' : '(توپر)'}</span>
        `;
        list.appendChild(row);
    });
}

window.addCentroidShapeRow = () => {
    centroidShapes.push({ type: 'rectangle', x: 20, y: 20, w: 40, h: 40, subtract: false });
    renderCentroidUI();
};

async function solveCentroids() {
    let data;
    try {
        const res = await fetch('/api/solve/centroids', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ shapes: centroidShapes })
        });
        if (!res.ok) throw new Error();
        data = await res.json();
    } catch (err) {
        data = StatixEngine.solveCentroids(centroidShapes);
    }

        document.getElementById('centroidBadge').textContent = `x̄ = ${data.x_bar} , ȳ = ${data.y_bar}`;

        const tbody = document.querySelector('#centroidTable tbody');
        tbody.innerHTML = '';
        data.breakdown_table.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${r.part_id}</td>
                <td>${r.type} ${r.is_subtracted ? '(کاسته)' : ''}</td>
                <td>${r.area}</td>
                <td>${r.x_bar}</td>
                <td>${r.y_bar}</td>
                <td>${r.Qx}</td>
                <td>${r.Qy}</td>
            `;
            tbody.appendChild(tr);
        });

        drawCentroidCanvas(data);
    } catch (err) {
        alert("خطا در مرکز سطح: " + err.message);
    }
}

function drawCentroidCanvas(data) {
    const canvas = document.getElementById('centroidCanvas');
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const margin = 50;
    const scale = 2.0;
    const originX = w / 2 - 50;
    const originY = h - 60;

    // Draw Axes
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(originX - 100, originY);
    ctx.lineTo(originX + 250, originY);
    ctx.moveTo(originX, originY + 50);
    ctx.lineTo(originX, originY - 250);
    ctx.stroke();

    // Draw Shapes
    centroidShapes.forEach(s => {
        if (s.type === 'rectangle') {
            const sx = originX + s.x * scale;
            const sy = originY - (s.y + s.h) * scale;
            const sw = s.w * scale;
            const sh = s.h * scale;

            ctx.fillStyle = s.subtract ? '#090d16' : 'rgba(56, 189, 248, 0.3)';
            ctx.strokeStyle = s.subtract ? '#f43f5e' : '#38bdf8';
            ctx.lineWidth = 2;
            ctx.fillRect(sx, sy, sw, sh);
            ctx.strokeRect(sx, sy, sw, sh);
        } else if (s.type === 'circle') {
            const scx = originX + s.xc * scale;
            const scy = originY - s.yc * scale;
            const sr = s.r * scale;

            ctx.fillStyle = s.subtract ? '#090d16' : 'rgba(56, 189, 248, 0.3)';
            ctx.strokeStyle = s.subtract ? '#f43f5e' : '#38bdf8';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(scx, scy, sr, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
        }
    });

    // Draw Centroid Target crosshair
    const cx = originX + data.x_bar * scale;
    const cy = originY - data.y_bar * scale;

    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.arc(cx, cy, 10, 0, Math.PI * 2);
    ctx.moveTo(cx - 15, cy); ctx.lineTo(cx + 15, cy);
    ctx.moveTo(cx, cy - 15); ctx.lineTo(cx, cy + 15);
    ctx.stroke();

    ctx.fillStyle = '#fbbf24';
    ctx.font = 'bold 12px JetBrains Mono';
    ctx.fillText(`C(${data.x_bar}, ${data.y_bar})`, cx + 18, cy - 8);
}

// =========================================================================
// MODULE 6: INERTIA & MOHR'S CIRCLE
// =========================================================================

function renderInertiaUI() {
    const list = document.getElementById('inertiaShapesList');
    list.innerHTML = '';
    inertiaShapes.forEach((s, idx) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item-row';
        row.innerHTML = `<span>#${idx+1} مستطیل: w=${s.w} , h=${s.h}</span>`;
        list.appendChild(row);
    });
}

async function solveInertia() {
    let data;
    try {
        const res = await fetch('/api/solve/inertia', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ shapes: inertiaShapes })
        });
        if (!res.ok) throw new Error();
        data = await res.json();
    } catch (err) {
        data = StatixEngine.solveInertia(inertiaShapes);
    }

        document.getElementById('mohrBadge').textContent =
            `I_max = ${data.principal_moments.I_max.toLocaleString()} | I_min = ${data.principal_moments.I_min.toLocaleString()}`;

        const box = document.getElementById('inertiaResultsBox');
        box.textContent =
`==============================================
ممان‌های اینرسی مقطع (Beer & Johnston Ch 9)
==============================================
ممان اینرسی نسبت به محورهای مرکزی (Centroidal):
  I_x_bar = ${data.centroidal_moments.I_x_bar.toLocaleString()}
  I_y_bar = ${data.centroidal_moments.I_y_bar.toLocaleString()}
  I_xy_bar = ${data.centroidal_moments.I_xy_bar.toLocaleString()}
  ممان اینرسی قطبی Jc = ${data.centroidal_moments.J_c.toLocaleString()}

ممان‌های اینرسی اصلی (Principal Moments):
  I_max = ${data.principal_moments.I_max.toLocaleString()}
  I_min = ${data.principal_moments.I_min.toLocaleString()}
  زاویه محورهای اصلی: θp = ${data.principal_moments.theta_p_deg}°

شعاع‌های ژیراسیون:
  kx = ${data.radii_of_gyration.kx} , ky = ${data.radii_of_gyration.ky}
`;

        drawMohrCanvas(data.mohr_circle);
    } catch (err) {
        alert("خطا: " + err.message);
    }
}

function drawMohrCanvas(mohr) {
    const canvas = document.getElementById('mohrCanvas');
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const centerX = w / 2;
    const centerY = h / 2;
    const R_canvas = 110;

    // Draw Axes
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(50, centerY); ctx.lineTo(w - 50, centerY);
    ctx.moveTo(centerX, 40); ctx.lineTo(centerX, h - 40);
    ctx.stroke();

    // Mohr Circle
    ctx.strokeStyle = '#38bdf8';
    ctx.fillStyle = 'rgba(56, 189, 248, 0.1)';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(centerX, centerY, R_canvas, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Center point C
    ctx.fillStyle = '#fbbf24';
    ctx.beginPath();
    ctx.arc(centerX, centerY, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillText(`C (${mohr.center.toFixed(0)})`, centerX + 10, centerY - 10);

    // Points X and Y
    ctx.fillStyle = '#f43f5e';
    ctx.beginPath();
    ctx.arc(centerX + R_canvas * 0.7, centerY - R_canvas * 0.7, 5, 0, Math.PI * 2);
    ctx.arc(centerX - R_canvas * 0.7, centerY + R_canvas * 0.7, 5, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = '#f43f5e';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(centerX + R_canvas * 0.7, centerY - R_canvas * 0.7);
    ctx.lineTo(centerX - R_canvas * 0.7, centerY + R_canvas * 0.7);
    ctx.stroke();
    ctx.setLineDash([]);
}

// =========================================================================
// MODULE 7: CABLES
// =========================================================================

async function solveParabolicCable() {
    const span_L = parseFloat(document.getElementById('cableSpan').value);
    const sag_h = parseFloat(document.getElementById('cableSag').value);
    const w_per_m = parseFloat(document.getElementById('cableLoad').value);

    let data;
    try {
        const res = await fetch('/api/solve/cables/parabolic', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ span_L, sag_h, w_per_m })
        });
        if (!res.ok) throw new Error();
        data = await res.json();
    } catch (err) {
        data = StatixEngine.solveParabolicCable(span_L, sag_h, w_per_m);
    }

        document.getElementById('cableBadge').textContent = `T_max = ${data.max_tension_Tmax} kN`;

        const box = document.getElementById('cableResultsBox');
        box.textContent =
`==============================================
تحلیل کابل سهموی پل معلق (Beer & Johnston Ch 7)
==============================================
کشش حداقل در مرکز کابل (کمترین کشش):
  T0 = ${data.min_tension_T0} kN

واکنش قائم تکیه‌گاه‌ها:
  Vy = ${data.max_vertical_reaction} kN

کشش حداکثر در تکیه‌گاه‌ها:
  T_max = ${data.max_tension_Tmax} kN

طول واقعی کابل منحنی:
  S = ${data.cable_length} متر (افزایش ${(data.cable_length - span_L).toFixed(2)} متری نسبت به دهانه)
`;

        drawCableCanvas(data);
    } catch (err) {
        alert("خطا در کابل: " + err.message);
    }
}

function drawCableCanvas(data) {
    const canvas = document.getElementById('cableCanvas');
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const marginX = 90;
    const topY = 60;
    const L = data.span;
    const scaleX = (w - 2 * marginX) / L;
    const scaleY = 160 / data.sag;

    // Draw Cable Towers
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(marginX, topY); ctx.lineTo(marginX, h - 30);
    ctx.moveTo(w - marginX, topY); ctx.lineTo(w - marginX, h - 30);
    ctx.stroke();

    // Draw Cable Curve
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 4;
    ctx.beginPath();
    data.profile.x.forEach((x, i) => {
        const cx = marginX + x * scaleX;
        const cy = topY + data.profile.y_sag[i] * scaleY;
        if (i === 0) ctx.moveTo(cx, cy);
        else ctx.lineTo(cx, cy);
    });
    ctx.stroke();

    // Max Sag label
    ctx.fillStyle = '#fbbf24';
    ctx.font = '11px JetBrains Mono';
    ctx.textAlign = 'center';
    ctx.fillText(`Sag h = ${data.sag}m`, w / 2, topY + data.sag * scaleY + 22);
}

// =========================================================================
// MODULE 8: FRICTION
// =========================================================================

async function solveFrictionSlipTip() {
    const payload = {
        weight_W: parseFloat(document.getElementById('fricW').value),
        width_b: parseFloat(document.getElementById('fricB').value),
        height_h: parseFloat(document.getElementById('fricH').value),
        force_height_y: parseFloat(document.getElementById('fricY').value),
        incline_theta_deg: parseFloat(document.getElementById('fricTheta').value),
        mu_s: parseFloat(document.getElementById('fricMu').value)
    };

    let data;
    try {
        const res = await fetch('/api/solve/friction/slip-tip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error();
        data = await res.json();
    } catch (err) {
        data = StatixEngine.solveFrictionSlipTip(payload);
    }

        document.getElementById('frictionGoverningBadge').textContent = `حالت حاکم: ${data.governing_mode}`;

        const box = document.getElementById('frictionResultsBox');
        box.textContent =
`==============================================
تحلیل اصطکاک: لغزش در برابر واژگونی (Slip vs Tip)
==============================================
نیروی بحرانی لغزش (P_slip):
  ${data.P_slip_critical ? data.P_slip_critical + ' N' : 'ناممکن'}

نیروی بحرانی واژگونی (P_tip):
  ${data.P_tip_critical ? data.P_tip_critical + ' N' : 'ناممکن'}

زاویه اصطکاک ایستا:
  φs = ${data.friction_angle_deg}°

نتیجه‌گیری مهندسی بیر جانسون:
  ${data.comparison_note}
`;

        drawFrictionCanvas(payload, data);
    } catch (err) {
        alert("خطا: " + err.message);
    }
}

function drawFrictionCanvas(params, res) {
    const canvas = document.getElementById('frictionCanvas');
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const thetaRad = (params.incline_theta_deg * Math.PI) / 180;
    const cx = w / 2;
    const cy = h / 2 + 30;

    // Draw Incline Plane
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(-thetaRad);

    // Plane line
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(-200, 0); ctx.lineTo(200, 0);
    ctx.stroke();

    // Block
    const scale = 140;
    const bw = params.width_b * scale;
    const bh = params.height_h * scale;
    ctx.fillStyle = 'rgba(56, 189, 248, 0.2)';
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 3;
    ctx.fillRect(-bw / 2, -bh, bw, bh);
    ctx.strokeRect(-bw / 2, -bh, bw, bh);

    // Force P arrow
    const py = -params.force_height_y * scale;
    drawArrow(ctx, -bw / 2 - 60, py, -bw / 2 - 5, py, '#f43f5e', 8);

    ctx.restore();
}

// =========================================================================
// MODULE 9: VIRTUAL WORK
// =========================================================================

async function solveVirtualWork() {
    const expr = document.getElementById('vwExpr').value;
    try {
        const res = await fetch('/api/solve/virtual-work', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ expression_str: expr })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail);

        const box = document.getElementById('virtualResultsBox');
        let txt =
`==============================================
کار مجازی و پایداری تعادل (Beer & Johnston Ch 10)
==============================================
تابع انرژی پتانسیل V(θ):
  ${data.potential_energy_function}

مشتق اول dV/dθ (شرط تعادل dV/dθ = 0):
  ${data.first_derivative}

مشتق دوم d²V/dθ² (تعیین وضعیت پایداری):
  ${data.second_derivative}

نقاط تعادل به دست آمده:
`;
        data.equilibrium_points.forEach((pt, i) => {
            txt += `\nنقطه تعادل #${i+1}: θ = ${pt.q_value} rad (${pt.q_deg}°)\n  • انرژی پتانسیل: V = ${pt.potential_energy}\n  • مشتق دوم d²V/dθ² = ${pt.d2V_dq2}\n  • وضعیت: ${pt.stability}\n`;
        });

        box.textContent = txt;
    } catch (err) {
        alert("خطا: " + err.message);
    }
}

// =========================================================================
// EXPORT REPORT
// =========================================================================

function copyResultsToClipboard() {
    let report = `STATIX PRO - گزارش نتایج تحلیل استاتیک مهندسی عمران\n`;
    report += `زمان تولید گزارش: ${new Date().toLocaleString('fa-IR')}\n`;
    report += `ماژول فعال: ${currentTab}\n\n`;

    if (currentTab === 'tab-beams' && lastBeamResults) {
        report += `[نتایج تحلیل تیر]:\nطول: ${lastBeamResults.length} m\n`;
        report += `بیشینه برش: ${lastBeamResults.max_shear} kN\nبیشینه لنگر: ${lastBeamResults.max_moment} kN.m\n`;
        report += `عکس‌العمل‌های تکیه‌گاهی:\n`;
        lastBeamResults.supports.forEach(s => {
            report += `  x=${s.x}m (${s.type}): Ry=${s.Ry} kN , Rm=${s.Rm} kN.m\n`;
        });
    } else if (currentTab === 'tab-trusses' && lastTrussResults) {
        report += `[نتایج تحلیل خرپا]:\nتعداد اعضا: ${lastTrussResults.num_elements}\nوضعیت: ${lastTrussResults.determinacy}\n`;
        lastTrussResults.members.forEach(m => {
            report += `  عضو ${m.node1}-${m.node2}: Force=${m.force} N (${m.state})\n`;
        });
    } else {
        report += `نتایج ماژول در صفحه قابل مشاهده است.\n`;
    }

    navigator.clipboard.writeText(report).then(() => {
        alert("گزارش نتایج با موفقیت در کلیپ‌بورد کپی شد!");
    }).catch(() => {
        alert("خطا در کپی کردن.");
    });
}
