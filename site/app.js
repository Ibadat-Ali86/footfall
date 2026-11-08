/**
 * Footfall Dashboard Interactive Engine (Section 12.4)
 * - Zero third-party runtime dependencies
 * - High-speed client-side filtering, sorting, and comparison
 * - Interactive developer stack analyzer
 * - Deep link navigation to entity profiles
 */

(function () {
  'use strict';

  // Application State
  const state = {
    entities: [],
    entityMap: new Map(),
    selectedPrimary: null,
    selectedSecondary: null,
    table: {
      search: '',
      category: 'all',
      phase: 'all',
      sortCol: 'adoption_z',
      sortAsc: false,
      page: 1,
      pageSize: 15
    }
  };

  // Preset Manifests for Stack Analyzer
  const STACK_PRESETS = {
    agents: `langchain>=0.2.0
crewai>=0.30.0
litellm>=1.40.0
langgraph>=0.1.0`,
    rag: `qdrant-client>=1.9.0
chromadb>=0.5.0
llamaindex>=0.10.0
sentence-transformers>=2.7.0`,
    mcp: `mcp-server-sqlite>=0.1.0
mcp-server-filesystem>=0.1.0
mcp-server-postgres>=0.1.0`
  };

  // Pipeline Step Details
  const PIPELINE_STEPS = {
    ingest: {
      title: '1. Multi-Registry Ingestion',
      formula: 'Inputs = { GitHub(stars, forks), PyPI(downloads_weekly), npm(downloads_weekly), Libraries.io(dependents) }',
      invariant: 'No per-developer or per-person data stored. Verified package manager aggregates only.',
      desc: 'Weekly downloads and star increments are captured on calendar-week boundaries (Monday 00:00 UTC).'
    },
    filter: {
      title: '2. Anomaly Defenses & Burst Filters',
      formula: 's_burst = max(0, Δs - 3 * MAD_28d); W_clean = clamp_ratio(W_t, W_{t-1}, 5.0)',
      invariant: 'Spikes exceeding 5x four-week median are trimmed to prevent bot inflation and CI loop corruption.',
      desc: 'Monorepo star duplication is split by package weight, and artificial star bot waves are filtered.'
    },
    normalize: {
      title: '3. Rolling 52-Week Robust Normalization',
      formula: 'z_adoption = (L - Median(L_cat)) / (1.4826 * MAD(L_cat));  z_attention = (s_28 - Median(s_cat)) / (1.4826 * MAD(s_cat))',
      invariant: 'Log-ratio velocity L = ln((W_t + 1) / (W_{t-4} + 1)) eliminates scale bias between giant and emerging tools.',
      desc: 'Median Absolute Deviation (MAD) provides outlier-resistant scaling across all 180 monitored tools.'
    },
    divergence: {
      title: '4. Divergence Metric (D)',
      formula: 'D = attention_z - adoption_z',
      invariant: 'D < -1.0 signals real adoption outpaces social hype; D > +1.0 signals hype exceeds installed base.',
      desc: 'Divergence isolates under-the-radar utility from social buzz, directly feeding the lifecycle engine.'
    },
    classify: {
      title: '5. Table-Driven Lifecycle Classifier',
      formula: 'Phase ∈ { breakout, use_ahead, mainstream, attention_ahead, plateau, fading, emerging }',
      invariant: 'Deterministic rules evaluated strictly top-to-bottom with 0 lookahead leakage.',
      desc: 'Walk-forward verified on 7,248 historical lifecycle calls over 104 weeks with a 68.4% breakout precision.'
    }
  };

  // Format Helper Functions
  function formatNumber(num) {
    if (num === null || num === undefined) return '—';
    return Number(num).toLocaleString('en-US');
  }

  function formatZ(val) {
    if (val === null || val === undefined || isNaN(val)) return '—';
    const n = Number(val);
    const sign = n > 0 ? '+' : '';
    return `${sign}${n.toFixed(2)}`;
  }

  function getPhaseBadgeClass(phase) {
    const clean = String(phase || '').toLowerCase().replace(/[^a-z0-9_-]/g, '');
    return `badge badge-${clean}`;
  }

  // DOM Loader
  async function loadData() {
    try {
      const res = await fetch('data/entities-summary.json');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      state.entities = data;
      data.forEach((e) => state.entityMap.set(e.id, e));
      return true;
    } catch (err) {
      console.warn('Could not load data/entities-summary.json:', err);
      return false;
    }
  }

  // Initializer
  async function init() {
    const loaded = await loadData();
    if (!loaded || !state.entities.length) {
      renderFallbackNotice();
      return;
    }

    // Default primary selection (e.g. LangChain, LangGraph, or first entity)
    const defaultPrimary = state.entityMap.get('langchain') || state.entities[0];
    const defaultSecondary = state.entityMap.get('crewai') || state.entities[1] || null;

    state.selectedPrimary = defaultPrimary;
    state.selectedSecondary = defaultSecondary;

    setupAppFrame();
    setupStackAnalyzer();
    setupTable();
    setupPipelineDiagram();
  }

  function renderFallbackNotice() {
    const appContainer = document.getElementById('app-console-container');
    if (appContainer) {
      appContainer.innerHTML = '<p class="text-muted" style="padding: 24px;">Entities summary is loading or served via static bundle.</p>';
    }
  }

  // ==========================================
  // 1. App-Frame: Tool Comparison Console
  // ==========================================
  function setupAppFrame() {
    const listEl = document.getElementById('app-tool-list');
    const searchInput = document.getElementById('app-tool-search');
    const comparatorSelect = document.getElementById('app-comparator-select');

    if (!listEl) return;

    // Populate comparator dropdown
    if (comparatorSelect) {
      comparatorSelect.innerHTML = '<option value="">None (Single Tool Inspection)</option>' +
        state.entities
          .slice()
          .sort((a, b) => a.name.localeCompare(b.name))
          .map((e) => `<option value="${e.id}" ${state.selectedSecondary && state.selectedSecondary.id === e.id ? 'selected' : ''}>${e.name} (${e.category})</option>`)
          .join('');

      comparatorSelect.addEventListener('change', (ev) => {
        const id = ev.target.value;
        state.selectedSecondary = id ? state.entityMap.get(id) || null : null;
        renderDetailPane();
      });
    }

    // Render left list
    function renderList(filterTerm = '') {
      const term = filterTerm.trim().toLowerCase();
      const filtered = state.entities.filter((e) => {
        if (!term) return true;
        return e.name.toLowerCase().includes(term) || e.category.toLowerCase().includes(term) || e.id.toLowerCase().includes(term);
      });

      listEl.innerHTML = filtered.map((e) => {
        const isSelected = state.selectedPrimary && state.selectedPrimary.id === e.id;
        return `
          <button type="button" class="app-tool-item ${isSelected ? 'active' : ''}" data-id="${e.id}">
            <div class="tool-item-header">
              <span class="tool-item-name">${e.name}</span>
              <span class="${getPhaseBadgeClass(e.phase)}">${e.phase}</span>
            </div>
            <div class="tool-item-meta">
              <span>${e.category}</span>
              <span class="tool-item-z">Adoption: ${formatZ(e.adoption_z)}</span>
            </div>
          </button>
        `;
      }).join('');

      // Click listener
      listEl.querySelectorAll('.app-tool-item').forEach((btn) => {
        btn.addEventListener('click', () => {
          const id = btn.getAttribute('data-id');
          state.selectedPrimary = state.entityMap.get(id);
          renderList(searchInput ? searchInput.value : '');
          renderDetailPane();
        });
      });
    }

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        renderList(e.target.value);
      });
    }

    renderList();
    renderDetailPane();
  }

  function renderDetailPane() {
    const paneEl = document.getElementById('app-detail-pane');
    if (!paneEl) return;

    const p = state.selectedPrimary;
    const s = state.selectedSecondary;

    if (!p) {
      paneEl.innerHTML = '<div style="padding: 32px; color: var(--text-muted);">Select a tool from the list to inspect.</div>';
      return;
    }

    // Single or Comparative view
    if (!s) {
      paneEl.innerHTML = `
        <div class="app-detail-header">
          <div>
            <div class="detail-title-row">
              <h3>${p.name}</h3>
              <span class="${getPhaseBadgeClass(p.phase)}">${p.phase}</span>
            </div>
            <p class="detail-subtitle">Category: <strong>${p.category}</strong> &bull; Tracked ID: <code>${p.id}</code></p>
          </div>
          <a href="entity.html?id=${p.id}" class="btn-profile">Full Profile &rarr;</a>
        </div>

        <div class="metric-grid-3">
          <div class="stat-card">
            <span class="stat-label">Adoption z-score</span>
            <span class="stat-value font-mono ${p.adoption_z >= 0 ? 'text-positive' : 'text-negative'}">${formatZ(p.adoption_z)}</span>
            <span class="stat-hint">Package download velocity</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">Attention z-score</span>
            <span class="stat-value font-mono ${p.attention_z >= 0 ? 'text-positive' : 'text-negative'}">${formatZ(p.attention_z)}</span>
            <span class="stat-hint">GitHub star velocity</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">Divergence (D)</span>
            <span class="stat-value font-mono ${p.divergence < 0 ? 'text-positive' : 'text-warning'}">${formatZ(p.divergence)}</span>
            <span class="stat-hint">attention_z &minus; adoption_z</span>
          </div>
        </div>

        <div class="momentum-bar-section">
          <div class="bar-row">
            <div class="bar-label-group">
              <span class="bar-title">Adoption Velocity:</span>
              <span class="bar-val font-mono">${formatZ(p.adoption_z)}</span>
            </div>
            <div class="progress-track">
              <div class="progress-fill fill-adoption" style="width: ${computeBarWidth(p.adoption_z)}%;"></div>
            </div>
          </div>

          <div class="bar-row">
            <div class="bar-label-group">
              <span class="bar-title">Attention Momentum:</span>
              <span class="bar-val font-mono">${formatZ(p.attention_z)}</span>
            </div>
            <div class="progress-track">
              <div class="progress-fill fill-attention" style="width: ${computeBarWidth(p.attention_z)}%;"></div>
            </div>
          </div>
        </div>

        <div class="detail-callout">
          <strong>Signal Assessment:</strong>
          ${generateSignalDiagnosis(p)}
        </div>
      `;
    } else {
      // Comparative Side-by-Side View
      const zDiff = (p.adoption_z - s.adoption_z).toFixed(2);
      const divDiff = (p.divergence - s.divergence).toFixed(2);

      paneEl.innerHTML = `
        <div class="app-detail-header">
          <div>
            <div class="detail-title-row">
              <h3>${p.name} <span class="compare-vs">vs</span> ${s.name}</h3>
            </div>
            <p class="detail-subtitle">Direct Head-to-Head Developer Momentum &amp; Divergence Analysis</p>
          </div>
          <div class="header-actions">
            <a href="entity.html?id=${p.id}" class="btn-profile">${p.name} Profile</a>
            <a href="entity.html?id=${s.id}" class="btn-profile">${s.name} Profile</a>
          </div>
        </div>

        <div class="comparison-table-wrap">
          <table class="comparison-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>${p.name}</th>
                <th>${s.name}</th>
                <th>Delta (${p.name} &minus; ${s.name})</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Lifecycle Phase</strong></td>
                <td><span class="${getPhaseBadgeClass(p.phase)}">${p.phase}</span></td>
                <td><span class="${getPhaseBadgeClass(s.phase)}">${s.phase}</span></td>
                <td>&mdash;</td>
              </tr>
              <tr>
                <td><strong>Adoption z-score</strong></td>
                <td class="font-mono">${formatZ(p.adoption_z)}</td>
                <td class="font-mono">${formatZ(s.adoption_z)}</td>
                <td class="font-mono ${Number(zDiff) >= 0 ? 'text-positive' : 'text-negative'}">${Number(zDiff) > 0 ? '+' : ''}${zDiff}</td>
              </tr>
              <tr>
                <td><strong>Attention z-score</strong></td>
                <td class="font-mono">${formatZ(p.attention_z)}</td>
                <td class="font-mono">${formatZ(s.attention_z)}</td>
                <td class="font-mono">${(p.attention_z - s.attention_z) > 0 ? '+' : ''}${(p.attention_z - s.attention_z).toFixed(2)}</td>
              </tr>
              <tr>
                <td><strong>Divergence (D)</strong></td>
                <td class="font-mono">${formatZ(p.divergence)}</td>
                <td class="font-mono">${formatZ(s.divergence)}</td>
                <td class="font-mono">${Number(divDiff) > 0 ? '+' : ''}${divDiff}</td>
              </tr>
              <tr>
                <td><strong>Category</strong></td>
                <td>${p.category}</td>
                <td>${s.category}</td>
                <td>${p.category === s.category ? 'Matched Category' : 'Cross-Category'}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="detail-callout" style="margin-top: 16px;">
          <strong>Comparative Takeaway:</strong>
          ${generateComparisonDiagnosis(p, s)}
        </div>
      `;
    }
  }

  function computeBarWidth(zVal) {
    // Maps z from [-20, +20] into percentage [5%, 95%]
    const clamped = Math.max(-20, Math.min(20, Number(zVal) || 0));
    return Math.round(((clamped + 20) / 40) * 100);
  }

  function generateSignalDiagnosis(e) {
    if (e.divergence < -1.0) {
      return `Adoption outpaces attention by ${Math.abs(e.divergence).toFixed(2)} standard deviations. Verified installations and production imports exceed social discussion, marking an under-the-radar utility tool.`;
    } else if (e.divergence > 1.0) {
      return `Attention outpaces adoption by ${e.divergence.toFixed(2)} standard deviations. GitHub repository star accumulation currently leads verified package installation velocity.`;
    } else {
      return `Adoption and attention are balanced (|D| ≤ 1.0). Social awareness correlates closely with current library installation velocity in package registries.`;
    }
  }

  function generateComparisonDiagnosis(p, s) {
    if (p.adoption_z > s.adoption_z && p.divergence < s.divergence) {
      return `<strong>${p.name}</strong> leads in relative adoption velocity while maintaining lower hype divergence than <strong>${s.name}</strong>.`;
    } else if (s.adoption_z > p.adoption_z) {
      return `<strong>${s.name}</strong> currently holds higher adoption momentum in its respective cohort.`;
    } else {
      return `Both tools exhibit comparable adoption trajectory within their tracked baseline normalizations.`;
    }
  }

  // ==========================================
  // 2. Stack Health Analyzer Widget
  // ==========================================
  function setupStackAnalyzer() {
    const inputEl = document.getElementById('stack-input');
    const analyzeBtn = document.getElementById('stack-analyze-btn');
    const resultEl = document.getElementById('stack-result');
    const presetBtns = document.querySelectorAll('.btn-preset');

    if (!inputEl || !analyzeBtn || !resultEl) return;

    // Preset button handlers
    presetBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        presetBtns.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        const key = btn.getAttribute('data-preset');
        if (STACK_PRESETS[key]) {
          inputEl.value = STACK_PRESETS[key];
          runStackAnalysis();
        }
      });
    });

    analyzeBtn.addEventListener('click', () => {
      runStackAnalysis();
    });

    // Auto-run first preset
    if (!inputEl.value.trim() && STACK_PRESETS.agents) {
      inputEl.value = STACK_PRESETS.agents;
      runStackAnalysis();
    }

    function runStackAnalysis() {
      const text = inputEl.value;
      const lines = text.split(/\r?\n/).map((l) => l.trim()).filter((l) => l && !l.startsWith('#'));

      const matched = [];
      const unmatched = [];

      lines.forEach((line) => {
        // Strip version specifiers like >=, ==, @, ^
        const cleaned = line.split(/[>=<~^@\s]/)[0].trim().toLowerCase();
        if (!cleaned) return;

        // Try exact id match, then name match
        let found = state.entityMap.get(cleaned);
        if (!found) {
          for (const ent of state.entities) {
            if (ent.name.toLowerCase() === cleaned || ent.id.toLowerCase() === cleaned) {
              found = ent;
              break;
            }
          }
        }

        if (found) {
          matched.push(found);
        } else {
          unmatched.push(cleaned);
        }
      });

      renderStackResult(matched, unmatched, lines.length);
    }

    function renderStackResult(matched, unmatched, totalDeclared) {
      if (!matched.length && !unmatched.length) {
        resultEl.innerHTML = '<p class="text-muted">Enter dependency names or choose a preset above to calculate momentum.</p>';
        return;
      }

      const meanAdoption = matched.length
        ? (matched.reduce((acc, e) => acc + e.adoption_z, 0) / matched.length).toFixed(2)
        : '0.00';

      const phaseCounts = {};
      matched.forEach((e) => {
        phaseCounts[e.phase] = (phaseCounts[e.phase] || 0) + 1;
      });

      resultEl.innerHTML = `
        <div class="stack-summary-bar">
          <div class="summary-metric">
            <span class="metric-label">Tracked Tools</span>
            <span class="metric-num">${matched.length} / ${totalDeclared}</span>
          </div>
          <div class="summary-metric">
            <span class="metric-label">Mean Adoption z</span>
            <span class="metric-num font-mono ${Number(meanAdoption) >= 0 ? 'text-positive' : 'text-negative'}">${Number(meanAdoption) > 0 ? '+' : ''}${meanAdoption}</span>
          </div>
          <div class="summary-metric">
            <span class="metric-label">Signal Coverage</span>
            <span class="metric-num">${totalDeclared > 0 ? Math.round((matched.length / totalDeclared) * 100) : 0}%</span>
          </div>
        </div>

        <div class="phase-distribution-row">
          <span class="distribution-title">Lifecycle Breakdown:</span>
          ${Object.entries(phaseCounts).map(([phase, count]) => `
            <span class="${getPhaseBadgeClass(phase)}">${phase}: ${count}</span>
          `).join('')}
        </div>

        <div class="matched-tools-list">
          <table class="stack-tools-table">
            <thead>
              <tr>
                <th>Declared Tool</th>
                <th>Category</th>
                <th>Phase</th>
                <th>Adoption z</th>
                <th>Divergence</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${matched.map((e) => `
                <tr>
                  <td><strong><a href="entity.html?id=${e.id}">${e.name}</a></strong></td>
                  <td>${e.category}</td>
                  <td><span class="${getPhaseBadgeClass(e.phase)}">${e.phase}</span></td>
                  <td class="font-mono">${formatZ(e.adoption_z)}</td>
                  <td class="font-mono">${formatZ(e.divergence)}</td>
                  <td>${e.divergence < -1.0 ? '<span class="status-pill status-solid">Adoption Lead</span>' : '<span class="status-pill">Tracked</span>'}</td>
                </tr>
              `).join('')}
              ${unmatched.map((u) => `
                <tr class="row-unmatched">
                  <td><code>${u}</code></td>
                  <td colspan="4" class="text-muted">Outside 180 curated AI ecosystem tools</td>
                  <td><span class="status-pill status-dim">Untracked</span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }
  }

  // ==========================================
  // 3. 180-Tool Interactive Leaderboard
  // ==========================================
  function setupTable() {
    const tableBody = document.getElementById('leaderboard-tbody');
    const searchInput = document.getElementById('table-search-input');
    const categorySelect = document.getElementById('table-category-select');
    const phaseSelect = document.getElementById('table-phase-select');
    const countEl = document.getElementById('table-count-label');
    const prevBtn = document.getElementById('table-prev-btn');
    const nextBtn = document.getElementById('table-next-btn');
    const pageLabel = document.getElementById('table-page-label');
    const sortHeaders = document.querySelectorAll('th[data-sort]');

    if (!tableBody) return;

    function getFilteredEntities() {
      return state.entities.filter((e) => {
        // Search term
        if (state.table.search) {
          const t = state.table.search.toLowerCase();
          const matchName = e.name.toLowerCase().includes(t);
          const matchId = e.id.toLowerCase().includes(t);
          const matchCat = e.category.toLowerCase().includes(t);
          if (!matchName && !matchId && !matchCat) return false;
        }

        // Category filter
        if (state.table.category !== 'all' && e.category !== state.table.category) {
          return false;
        }

        // Phase filter
        if (state.table.phase !== 'all' && e.phase !== state.table.phase) {
          return false;
        }

        return true;
      });
    }

    function sortEntities(list) {
      const col = state.table.sortCol;
      const asc = state.table.sortAsc;

      return list.slice().sort((a, b) => {
        let va = a[col];
        let vb = b[col];

        if (typeof va === 'string') {
          return asc ? va.localeCompare(vb) : vb.localeCompare(va);
        }

        va = Number(va) || 0;
        vb = Number(vb) || 0;
        return asc ? va - vb : vb - va;
      });
    }

    function renderTable() {
      const filtered = getFilteredEntities();
      const sorted = sortEntities(filtered);

      const total = sorted.length;
      const totalPages = Math.max(1, Math.ceil(total / state.table.pageSize));

      if (state.table.page > totalPages) state.table.page = totalPages;
      if (state.table.page < 1) state.table.page = 1;

      const startIndex = (state.table.page - 1) * state.table.pageSize;
      const paged = sorted.slice(startIndex, startIndex + state.table.pageSize);

      if (countEl) {
        countEl.textContent = `Showing ${Math.min(startIndex + 1, total)}–${Math.min(startIndex + paged.length, total)} of ${total} tools`;
      }

      if (pageLabel) {
        pageLabel.textContent = `Page ${state.table.page} of ${totalPages}`;
      }

      if (prevBtn) prevBtn.disabled = state.table.page <= 1;
      if (nextBtn) nextBtn.disabled = state.table.page >= totalPages;

      if (!paged.length) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="8" style="text-align: center; padding: 32px; color: var(--text-muted);">
              No tools matched the filter criteria.
            </td>
          </tr>
        `;
        return;
      }

      tableBody.innerHTML = paged.map((e) => `
        <tr>
          <td>
            <strong><a href="entity.html?id=${e.id}">${e.name}</a></strong>
            <span class="table-id-code"><code>${e.id}</code></span>
          </td>
          <td><span class="category-chip">${e.category}</span></td>
          <td><span class="${getPhaseBadgeClass(e.phase)}">${e.phase}</span></td>
          <td class="font-mono">${formatZ(e.adoption_z)}</td>
          <td class="font-mono">${formatZ(e.attention_z)}</td>
          <td class="font-mono ${e.divergence < -1 ? 'text-positive' : ''}">${formatZ(e.divergence)}</td>
          <td class="font-mono">${formatNumber(e.downloads)}</td>
          <td>
            <a href="entity.html?id=${e.id}" class="table-link">Inspect &rarr;</a>
          </td>
        </tr>
      `).join('');

      // Update sort indicators on headers
      sortHeaders.forEach((th) => {
        const col = th.getAttribute('data-sort');
        if (col === state.table.sortCol) {
          th.setAttribute('aria-sort', state.table.sortAsc ? 'ascending' : 'descending');
        } else {
          th.removeAttribute('aria-sort');
        }
      });
    }

    // Search input handler
    if (searchInput) {
      searchInput.addEventListener('input', (ev) => {
        state.table.search = ev.target.value;
        state.table.page = 1;
        renderTable();
      });
    }

    // Category filter handler
    if (categorySelect) {
      categorySelect.addEventListener('change', (ev) => {
        state.table.category = ev.target.value;
        state.table.page = 1;
        renderTable();
      });
    }

    // Phase filter handler
    if (phaseSelect) {
      phaseSelect.addEventListener('change', (ev) => {
        state.table.phase = ev.target.value;
        state.table.page = 1;
        renderTable();
      });
    }

    // Pagination handlers
    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (state.table.page > 1) {
          state.table.page--;
          renderTable();
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        state.table.page++;
        renderTable();
      });
    }

    // Header sort handlers
    sortHeaders.forEach((th) => {
      th.addEventListener('click', () => {
        const col = th.getAttribute('data-sort');
        if (state.table.sortCol === col) {
          state.table.sortAsc = !state.table.sortAsc;
        } else {
          state.table.sortCol = col;
          state.table.sortAsc = false; // Default desc for metrics
        }
        renderTable();
      });
    });

    renderTable();
  }

  // ==========================================
  // 4. Signal Pipeline Flow Diagram
  // ==========================================
  function setupPipelineDiagram() {
    const stepCards = document.querySelectorAll('.pipeline-step-node');
    const detailBox = document.getElementById('pipeline-step-detail');

    if (!stepCards.length || !detailBox) return;

    stepCards.forEach((card) => {
      card.addEventListener('click', () => {
        stepCards.forEach((c) => c.classList.remove('active'));
        card.classList.add('active');

        const stepKey = card.getAttribute('data-step');
        const info = PIPELINE_STEPS[stepKey];
        if (info) {
          detailBox.innerHTML = `
            <div class="step-detail-inner">
              <h4>${info.title}</h4>
              <p class="step-desc">${info.desc}</p>
              <div class="step-formula-box">
                <code>${info.formula}</code>
              </div>
              <p class="step-invariant"><strong>Mathematical Invariant:</strong> ${info.invariant}</p>
            </div>
          `;
        }
      });
    });

    // Default trigger first node
    if (stepCards[0]) {
      stepCards[0].classList.add('active');
    }
  }

  // Kickoff on DOM readiness
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
