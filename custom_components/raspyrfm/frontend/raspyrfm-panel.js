const { LitElement, html, css } = window;

const MAX_SIGNAL_HISTORY = 200;

class RaspyRFMPanel extends LitElement {
  static get properties() {
    return {
      hass: {},
      learning: { type: Boolean },
      signals: { state: true },
      devices: { state: true },
      signalMappings: { state: true },
      formType: { state: true },
      formName: { state: true },
      formSignals: { state: true },
      formActions: { state: true },
      formCustomAction: { state: true },
      error: { state: true },
      successMessage: { state: true },
      infoMessage: { state: true },
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        min-height: 100%;
        padding: 24px;
        background: linear-gradient(135deg, var(--primary-background-color), rgba(0, 0, 0, 0))
          no-repeat;
      }

      h2.section-title {
        font-size: 1.4rem;
        font-weight: 600;
        margin: 0 0 12px;
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .layout {
        display: grid;
        gap: 24px;
      }

      .split-columns {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 24px;
      }

      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 24px;
      }

      ha-card {
        border-radius: 18px;
        box-shadow: var(--ha-card-box-shadow, 0 10px 30px rgba(0, 0, 0, 0.12));
        overflow: hidden;
      }

      ha-card .card-content {
        padding: 20px;
      }

      table {
        width: 100%;
        border-collapse: collapse;
      }

      th,
      td {
        padding: 10px;
        border-bottom: 1px solid var(--divider-color);
        font-size: 0.95rem;
      }

      tbody tr:last-child td {
        border-bottom: none;
      }

      .signal-list {
        max-height: 320px;
        overflow-y: auto;
        display: grid;
        gap: 12px;
      }

      .signal-entry {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px;
        border-radius: 12px;
        background: rgba(0, 0, 0, 0.04);
      }

      .meta-block {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .signal-meta {
        font-size: 12px;
        color: var(--secondary-text-color);
      }

      .form-grid {
        display: grid;
        gap: 16px;
      }

      .form-row {
        display: flex;
        gap: 12px;
        align-items: center;
        flex-wrap: wrap;
      }

      .pill {
        padding: 2px 8px;
        border-radius: 12px;
        background-color: var(--accent-color);
        color: var(--text-primary-color);
        font-size: 12px;
      }

      .chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 14px;
        background: rgba(0, 0, 0, 0.08);
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }

      .chip.primary {
        background: rgba(25, 118, 210, 0.16);
        color: var(--primary-color);
      }

      .signal-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      .signal-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 6px;
      }

      .signal-chip {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 10px;
        border-radius: 12px;
        background: rgba(0, 0, 0, 0.03);
      }

      .error {
        color: var(--error-color);
        margin-bottom: 12px;
        padding: 12px 16px;
        background: rgba(244, 67, 54, 0.1);
        border-radius: 8px;
        border-left: 4px solid var(--error-color);
      }

      .success {
        color: var(--success-color, #4caf50);
        margin-bottom: 12px;
        padding: 12px 16px;
        background: rgba(76, 175, 80, 0.1);
        border-radius: 8px;
        border-left: 4px solid var(--success-color, #4caf50);
      }

      .info {
        color: var(--info-color, #2196f3);
        margin-bottom: 12px;
        padding: 12px 16px;
        background: rgba(33, 150, 243, 0.1);
        border-radius: 8px;
        border-left: 4px solid var(--info-color, #2196f3);
      }

      .required {
        margin-left: 4px;
        color: var(--error-color);
      }

      .mapping-grid {
        display: grid;
        gap: 18px;
      }

      .mapping-item {
        display: grid;
        gap: 12px;
        padding: 16px;
        border-radius: 12px;
        background: rgba(0, 0, 0, 0.04);
      }

      .mapping-actions {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }

      mwc-button.danger,
      mwc-button.danger[unelevated] {
        --mdc-theme-primary: var(--error-color);
      }

      .device-checkboxes {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      .map-canvas {
        position: relative;
        border-radius: 16px;
        background: linear-gradient(135deg, rgba(0, 150, 136, 0.12), rgba(30, 136, 229, 0.12));
        padding: 12px;
        overflow: hidden;
      }

      svg.mapping {
        width: 100%;
        min-height: 260px;
      }

      .category-label {
        font-size: 0.8rem;
        font-weight: 600;
        fill: var(--primary-text-color);
      }

      .category-column {
        fill: rgba(255, 255, 255, 0.35);
      }

      .node-label {
        font-size: 0.75rem;
        fill: var(--primary-text-color);
      }

      .node-circle {
        fill: var(--accent-color);
        stroke: rgba(0, 0, 0, 0.2);
        stroke-width: 1;
      }

      @media (max-width: 768px) {
        :host {
          padding: 16px;
        }

        .actions {
          justify-content: stretch;
          flex-direction: column;
        }

        .actions mwc-button {
          width: 100%;
        }

        .signal-entry {
          flex-direction: column;
          align-items: stretch;
          gap: 12px;
        }

        .split-columns {
          grid-template-columns: 1fr;
        }

        h2.section-title {
          font-size: 1.2rem;
        }
      }

      .help-text {
        font-size: 0.85rem;
        color: var(--secondary-text-color);
        margin-top: 8px;
        padding: 8px;
        background: rgba(0, 0, 0, 0.02);
        border-radius: 6px;
      }

      .help-icon {
        cursor: help;
        opacity: 0.6;
        transition: opacity 0.2s;
      }

      .help-icon:hover {
        opacity: 1;
      }

      .button-group {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }

      @media (prefers-reduced-motion: reduce) {
        * {
          animation: none !important;
          transition: none !important;
        }
      }
    `;
  }

  constructor() {
    super();
    this.learning = false;
    this.signals = [];
    this.devices = [];
    this.signalMappings = {};
    this.formType = "switch";
    this.formName = "";
    this.formSignals = {};
    this.formActions = [];
    this._configureActionsForType(this.formType);
    this.formCustomAction = "";
    this.error = null;
    this.successMessage = null;
    this.infoMessage = null;
    this._signalUnsub = null;
    this._learningUnsub = null;
    this._persistedMappings = {};
  }

  connectedCallback() {
    super.connectedCallback();
    this._initialize();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    if (this._signalUnsub) {
      this._signalUnsub();
      this._signalUnsub = null;
    }
    if (this._learningUnsub) {
      this._learningUnsub();
      this._learningUnsub = null;
    }
  }

  async _initialize() {
    await this._loadState();
    await this._subscribeSignals();
    await this._subscribeLearning();
    await this._refreshDevices();
  }

  async _loadState() {
    const status = await this.hass.callWS({ type: "raspyrfm/learning/status" });
    this.learning = status.active;
    const signals = await this.hass.callWS({ type: "raspyrfm/signals/list" });
    this.signals = this._normaliseSignals(signals.signals || []);
  }

  async _loadMappings() {
    try {
      const response = await this.hass.callWS({ type: "raspyrfm/signals/map/list" });
      const next = {};
      (response.mappings || []).forEach((entry) => {
        next[entry.payload] = entry;
      });
      this.signalMappings = next;
      this._persistedMappings = JSON.parse(JSON.stringify(next));
      if (this.error === "Signal mapping is temporarily unavailable.") {
        this.error = null;
      }
    } catch (err) {
      // Older backends might not expose the mapping API yet – degrade gracefully.
      console.warn("Unable to load RaspyRFM signal mappings", err);
      if (Object.keys(this.signalMappings || {}).length) {
        this.signalMappings = {};
      }
      if (!this.error) {
        this.error = "Signal mapping is temporarily unavailable.";
      }
    }
  }

  async _subscribeSignals() {
    this._signalUnsub = await this.hass.connection.subscribeMessage((message) => {
      if (message.type !== "event") {
        return;
      }
      const signal = message.event;
      this.signals = this._normaliseSignals([...this.signals, signal]);
    }, {
      type: "raspyrfm/signals/subscribe"
    });
  }

  async _subscribeLearning() {
    this._learningUnsub = await this.hass.connection.subscribeMessage((message) => {
      if (message.type !== "event") {
        return;
      }
      this.learning = message.event.active;
    }, {
      type: "raspyrfm/learning/subscribe"
    });
  }

  async _refreshDevices() {
    const response = await this.hass.callWS({ type: "raspyrfm/devices/list" });
    this.devices = response.devices || [];
    await this._loadMappings();
  }

  render() {
    return html`
      <div class="layout">
        <div class="actions">
          <mwc-button raised icon="mdi:play" @click=${this._handleStartLearning} ?disabled=${this.learning}
            >Start learning</mwc-button
          >
          <mwc-button icon="mdi:stop" @click=${this._handleStopLearning} ?disabled=${!this.learning}
            >Stop learning</mwc-button
          >
          <mwc-button icon="mdi:refresh" @click=${this._refreshDevices}>Refresh devices</mwc-button>
          <mwc-button icon="mdi:chart-bubble" @click=${this._loadMappings}>Reload mapping</mwc-button>
        </div>
        ${this.error ? html`<div class="error">⚠️ ${this.error}</div>` : ""}
        ${this.successMessage ? html`<div class="success">✓ ${this.successMessage}</div>` : ""}
        ${this.infoMessage ? html`<div class="info">ℹ️ ${this.infoMessage}</div>` : ""}
        ${!this.learning && !this.signals.length ? html`
          <div class="info">
            <strong>Getting Started:</strong> Click "Start learning" to begin capturing RF signals from your remotes and devices. 
            For Raspberry Pi 4/5 with HAOS, ensure your RaspyRFM gateway is connected and accessible on the network.
          </div>
        ` : ""}
        <div class="split-columns">
          ${this._renderSignals()} ${this._renderForm()}
        </div>
        ${this._renderMappingWorkspace()}
        ${this._renderDevices()}
      </div>
    `;
  }

  _renderSignals() {
    if (!this.signals.length) {
      return html`
        <ha-card header="Captured signals">
          <div class="card-content">No signals received yet. Use the start learning button and trigger your remotes or sensors.</div>
        </ha-card>
      `;
    }
    return html`
      <ha-card header="Captured signals">
        <div class="card-content signal-list">
          ${this.signals.map((signal) => this._renderSignal(signal))}
        </div>
      </ha-card>
    `;
  }

  _renderSignal(signal) {
    const actions = Array.isArray(this.formActions) ? this.formActions : [];
    const classification = signal?.metadata?.classification;
    const classificationActions = Array.isArray(classification?.actions)
      ? classification.actions.map((action) => this._labelForAction(this._normaliseActionKey(action)))
      : [];

    return html`
      <div class="signal-entry">
        <div class="meta-block">
          <div>${signal.payload}</div>
          <div class="signal-meta">${signal.received}</div>
          ${classification
            ? html`
                <div class="signal-chips">
                  <span class="chip primary">${classification.suggested_type}</span>
                  ${classificationActions.map((label) => html`<span class="chip">${label}</span>`) }
                </div>
              `
            : ""}
        </div>
        <div class="signal-actions">
          ${actions.length
            ? actions.map(
                (action) => html`
                  <mwc-button
                    dense
                    outlined
                    @click=${() => this._assignSignal(action.key, signal.payload)}
                    >Set as ${action.label}</mwc-button
                  >
                `,
              )
            : html`<span class="signal-meta">Add an action to the form to assign this payload.</span>`}
        </div>
        ${classification
          ? html`
              <div class="signal-actions">
                <mwc-button
                  dense
                  icon="mdi:auto-fix"
                  @click=${() => this._applyClassification(signal)}
                  >Use ${classification.suggested_type} template</mwc-button
                >
              </div>
            `
          : ""}
      </div>
    `;
  }

  _normaliseActionKey(value) {
    if (!value) {
      return "";
    }
    const normalized = value
      .toString()
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "");
    if (normalized === "dimm") {
      return "dim";
    }
    return normalized;
  }

  _labelForAction(key) {
    const map = {
      on: "On",
      off: "Off",
      trigger: "Trigger",
      bright: "Brighten",
      dim: "Dim",
      pair: "Pair",
      unpair: "Unpair",
      press: "Press",
    };
    if (map[key]) {
      return map[key];
    }
    return key
      .split("_")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  _makeActionEntry(key, required = false) {
    const normalised = this._normaliseActionKey(key);
    return {
      key: normalised,
      label: this._labelForAction(normalised),
      required,
    };
  }

  _defaultActionsForType(type) {
    switch (type) {
      case "switch":
        return [this._makeActionEntry("on", true), this._makeActionEntry("off", true)];
      case "binary_sensor":
        return [this._makeActionEntry("trigger", true)];
      case "light":
        return [
          this._makeActionEntry("on", true),
          this._makeActionEntry("off", false),
          this._makeActionEntry("bright", false),
          this._makeActionEntry("dim", false),
        ];
      default:
        return [];
    }
  }

  _configureActionsForType(type) {
    const defaults = this._defaultActionsForType(type);
    const nextSignals = {};
    defaults.forEach((entry) => {
      if (this.formSignals && this.formSignals[entry.key]) {
        nextSignals[entry.key] = this.formSignals[entry.key];
      }
    });
    this.formActions = defaults;
    this.formSignals = nextSignals;
  }

  _assignSignal(actionKey, payload) {
    if (!actionKey) {
      this.error = "Add an action before assigning signals.";
      return;
    }
    this.formSignals = {
      ...this.formSignals,
      [actionKey]: payload,
    };
    this.error = null;
  }

  _clearSignal(actionKey) {
    if (!actionKey || !this.formSignals) {
      return;
    }
    const next = { ...this.formSignals };
    delete next[actionKey];
    this.formSignals = next;
  }

  _applyClassification(signal) {
    const classification = signal?.metadata?.classification;
    if (!classification) {
      return;
    }
    const nextType = classification.suggested_type || this.formType;
    this.formType = nextType;
    this._configureActionsForType(nextType);
    const actions = Array.isArray(classification.actions) ? classification.actions : [];
    let assigned = false;
    actions.forEach((actionName) => {
      const key = this._normaliseActionKey(actionName);
      if (!this.formActions.some((entry) => entry.key === key) && (nextType === "button" || nextType === "universal")) {
        this.formActions = [...this.formActions, this._makeActionEntry(key, false)];
      }
      if (!assigned && this.formActions.some((entry) => entry.key === key)) {
        this._assignSignal(key, signal.payload);
        assigned = true;
      }
    });
    if (!assigned && actions.length) {
      const fallback = this._normaliseActionKey(actions[0]);
      if (fallback) {
        this._assignSignal(fallback, signal.payload);
      }
    }
    this.requestUpdate();
  }

  _removeAction(actionKey) {
    if (!actionKey || !Array.isArray(this.formActions)) {
      return;
    }
    this.formActions = this.formActions.filter((entry) => entry.key !== actionKey);
    this._clearSignal(actionKey);
  }

  _updateCustomAction(value) {
    this.formCustomAction = value;
  }

  _addCustomAction() {
    const label = (this.formCustomAction || "").trim();
    if (!label) {
      this.error = "Provide a label for the new action.";
      return;
    }
    const key = this._normaliseActionKey(label);
    if (!key) {
      this.error = "Unable to derive an action name.";
      return;
    }
    if (this.formActions?.some((entry) => entry.key === key)) {
      this.error = "This action is already present.";
      return;
    }
    this.formActions = [...(this.formActions || []), this._makeActionEntry(key, false)];
    this.formCustomAction = "";
    this.error = null;
  }

  _renderForm() {
    return html`
      <ha-card header="Create Home Assistant device">
        <div class="card-content form-grid">
          <div class="form-row">
            <ha-textfield label="Name" .value=${this.formName} @input=${(ev) => this._updateName(ev.target.value)}></ha-textfield>
            <ha-select label="Type" .value=${this.formType} @selected=${(ev) => this._updateType(this._extractSelectValue(ev))}>
              <mwc-list-item value="switch">Switch</mwc-list-item>
              <mwc-list-item value="binary_sensor">Binary sensor</mwc-list-item>
              <mwc-list-item value="light">Light</mwc-list-item>
              <mwc-list-item value="button">Button group</mwc-list-item>
              <mwc-list-item value="universal">Universal</mwc-list-item>
            </ha-select>
          </div>
          ${Array.isArray(this.formActions) && this.formActions.length
            ? this.formActions.map((action) => {
                const payload = this.formSignals?.[action.key];
                return html`
                  <div class="form-row">
                    <span class="pill">
                      ${action.label}${action.required ? html`<span class="required">*</span>` : ""}
                    </span>
                    <span>${payload || "Choose a captured signal"}</span>
                    ${payload
                      ? html`<mwc-button dense icon="mdi:backspace" @click=${() => this._clearSignal(action.key)}>Clear</mwc-button>`
                      : ""}
                    ${!action.required
                      ? html`<mwc-button dense icon="mdi:delete-outline" @click=${() => this._removeAction(action.key)}>Remove</mwc-button>`
                      : ""}
                  </div>
                `;
              })
            : html`<div class="form-row"><span class="signal-meta">Add an action to begin assigning payloads.</span></div>`}
          ${this.formType === "button" || this.formType === "universal"
            ? html`
                <div class="form-row">
                  <ha-textfield
                    label="Add action"
                    .value=${this.formCustomAction}
                    @input=${(ev) => this._updateCustomAction(ev.target.value)}
                  ></ha-textfield>
                  <mwc-button icon="mdi:plus" @click=${this._addCustomAction}>Add</mwc-button>
                </div>
              `
            : ""}
          <div class="form-row">
            <mwc-button raised icon="mdi:plus-box" @click=${this._createDevice}>Create device</mwc-button>
          </div>
        </div>
      </ha-card>
    `;
  }

  _renderMappingWorkspace() {
    const categories = [
      { key: "sensor", title: "Sensors", icon: "mdi:motion-sensor" },
      { key: "actuator", title: "Actuators", icon: "mdi:toggle-switch" },
      { key: "other", title: "Other", icon: "mdi:radio-tower" },
    ];

    const timeline = new Map();
    (this.signals || []).forEach((signal) => {
      timeline.set(signal.payload, signal);
    });
    Object.values(this.signalMappings || {}).forEach((entry) => {
      if (!timeline.has(entry.payload)) {
        timeline.set(entry.payload, {
          payload: entry.payload,
          received: "Persisted mapping",
        });
      }
    });
    const editableSignals = Array.from(timeline.values());

    return html`
      <ha-card>
        <div class="card-content mapping-grid">
          <h2 class="section-title"><ha-icon icon="mdi:map-marker-path"></ha-icon>Signal mapping workspace</h2>
          <p>
            Organise captured payloads into semantic groups and link them to configured devices. The canvas updates in real
            time to provide an at-a-glance topology of your RaspyRFM environment.
          </p>
          <div class="map-canvas">${this._renderMappingCanvas(categories)}</div>
          <div class="mapping-grid">
            ${editableSignals.length === 0
              ? html`<p>No signals captured yet. Start a learning session to populate the workspace.</p>`
              : html`${editableSignals.map((signal) => this._renderMappingEditor(signal, categories))}`}
          </div>
        </div>
      </ha-card>
    `;
  }

  _renderMappingCanvas(categories) {
    const width = 900;
    const height = 260;
    const columnWidth = width / categories.length;
    const nodes = categories.map((category, index) => {
      const payloads = Object.values(this.signalMappings).filter((entry) => entry.category === category.key);
      return { category, index, payloads };
    });

    return html`
      <svg class="mapping" viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid meet">
        ${nodes.map(({ category, index, payloads }) => {
          const x = index * columnWidth;
          const columnPadding = 24;
          const circleRadius = 18;
          const verticalSpace = (height - columnPadding * 2) / Math.max(payloads.length, 1);

          return html`
            <g>
              <rect class="category-column" x="${x + 8}" y="12" width="${columnWidth - 16}" height="${height - 24}" rx="18"></rect>
              <text class="category-label" x="${x + columnWidth / 2}" y="40" text-anchor="middle">${category.title}</text>
              ${payloads.length === 0
                ? html`<text class="node-label" x="${x + columnWidth / 2}" y="120" text-anchor="middle">No mappings yet</text>`
                : payloads.map((entry, position) => {
                    const cx = x + columnWidth / 2;
                    const cy = columnPadding + circleRadius + position * verticalSpace;
                    return html`
                      <g>
                        <circle class="node-circle" cx="${cx}" cy="${cy}" r="${circleRadius}"></circle>
                        <text class="node-label" x="${cx}" y="${cy + 4}" text-anchor="middle">${entry.label || entry.payload}</text>
                      </g>
                    `;
                  })}
            </g>
          `;
        })}
      </svg>
    `;
  }

  _renderMappingEditor(signal, categories) {
    const mapping = this.signalMappings[signal.payload] || {
      payload: signal.payload,
      label: signal.payload,
      category: "other",
      linked_devices: [],
    };

    const handleLabelInput = (value) => {
      this._updateMappingDraft(signal.payload, { label: value });
    };

    const handleCategoryChange = (value) => {
      this._updateMappingDraft(signal.payload, { category: value });
    };

    return html`
      <div class="mapping-item">
        <div class="form-row">
          <ha-icon icon="mdi:radio-frequency"></ha-icon>
          <div>
            <strong>${signal.payload}</strong>
            <div class="signal-meta">${signal.received}</div>
          </div>
        </div>
        <div class="form-row">
          <ha-textfield
            label="Display label"
            .value=${mapping.label || ""}
            @input=${(ev) => handleLabelInput(ev.target.value)}
          ></ha-textfield>
          <ha-select label="Category" .value=${mapping.category} @selected=${(ev) => handleCategoryChange(this._extractSelectValue(ev))}>
            ${categories.map(
              (category) => html`<mwc-list-item value="${category.key}">${category.title}</mwc-list-item>`
            )}
          </ha-select>
        </div>
        <div>
          <div class="signal-meta">Link to Home Assistant devices</div>
          <div class="device-checkboxes">
            ${this.devices.map(
              (device) => html`
                <mwc-formfield label="${device.name}">
                  <mwc-checkbox
                    ?checked=${mapping.linked_devices?.includes(device.device_id)}
                    @change=${(ev) => this._toggleMappingDevice(signal.payload, device.device_id, ev.target.checked)}
                  ></mwc-checkbox>
                </mwc-formfield>
              `
            )}
            ${!this.devices.length
              ? html`<span class="signal-meta">No RaspyRFM devices configured yet.</span>`
              : ""}
          </div>
        </div>
        <div class="mapping-actions">
          <mwc-button dense unelevated icon="mdi:content-save" @click=${() => this._saveMapping(signal.payload)}
            >Save mapping</mwc-button
          >
          <mwc-button dense icon="mdi:backup-restore" @click=${() => this._resetMapping(signal.payload)}
            >Reset changes</mwc-button
          >
          <mwc-button dense icon="mdi:delete" class="danger" @click=${() => this._deleteMapping(signal.payload)}
            >Remove mapping</mwc-button
          >
        </div>
      </div>
    `;
  }

  _renderDevices() {
    if (!this.devices.length) {
      return html`
        <ha-card header="Configured devices">
          <div class="card-content">No RaspyRFM devices created yet.</div>
        </ha-card>
      `;
    }
    return html`
      <ha-card header="Configured devices">
        <div class="card-content">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Signals</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              ${this.devices.map((device) => html`
                <tr>
                  <td>${device.name}</td>
                  <td>${device.device_type}</td>
                  <td>
                    ${Object.entries(device.signals || {}).map(
                      ([key, value]) => html`
                        <div class="signal-chip">
                          <div><strong>${this._labelForAction(this._normaliseActionKey(key))}</strong></div>
                          <div class="signal-meta">${value}</div>
                          <div class="signal-actions">
                            <mwc-button dense icon="mdi:send" @click=${() => this._invokeAction(device.device_id, key)}
                              >Send</mwc-button
                            >
                          </div>
                        </div>
                      `,
                    ) }
                  </td>
                  <td>
                    <mwc-button @click=${() => this._deleteDevice(device.device_id)}>Delete</mwc-button>
                  </td>
                </tr>
              `)}
            </tbody>
          </table>
        </div>
      </ha-card>
    `;
  }

  _updateName(value) {
    this.formName = value;
  }

  _updateType(value) {
    const next = value || "switch";
    if (next === this.formType) {
      return;
    }
    this.formType = next;
    this._configureActionsForType(next);
  }

  _updateMappingDraft(payload, updates) {
    const current = this.signalMappings[payload] || {
      payload,
      label: payload,
      category: "other",
      linked_devices: [],
    };
    this.signalMappings = {
      ...this.signalMappings,
      [payload]: { ...current, ...updates },
    };
  }

  _toggleMappingDevice(payload, deviceId, checked) {
    const current = this.signalMappings[payload] || {
      payload,
      label: payload,
      category: "other",
      linked_devices: [],
    };
    const linked = new Set(current.linked_devices || []);
    if (checked) {
      linked.add(deviceId);
    } else {
      linked.delete(deviceId);
    }
    this._updateMappingDraft(payload, { linked_devices: Array.from(linked) });
  }

  async _saveMapping(payload) {
    const entry = this.signalMappings[payload];
    if (!entry) {
      return;
    }
    try {
      const response = await this.hass.callWS({
        type: "raspyrfm/signals/map/update",
        payload,
        category: entry.category,
        label: entry.label || payload,
        linked_devices: entry.linked_devices || [],
      });
      const mapping = response.mapping || entry;
      this.signalMappings = {
        ...this.signalMappings,
        [payload]: mapping,
      };
      this._persistedMappings[payload] = JSON.parse(JSON.stringify(mapping));
      this.error = null;
    } catch (err) {
      console.warn("Failed to persist RaspyRFM mapping", err);
      this.error = err?.message || "Unable to save mapping.";
    }
  }

  async _deleteMapping(payload) {
    try {
      await this.hass.callWS({ type: "raspyrfm/signals/map/delete", payload });
      const next = { ...this.signalMappings };
      delete next[payload];
      this.signalMappings = next;
      delete this._persistedMappings[payload];
      this.error = null;
    } catch (err) {
      console.warn("Failed to delete RaspyRFM mapping", err);
      this.error = err?.message || "Unable to delete mapping.";
    }
  }

  _resetMapping(payload) {
    const persisted = this._persistedMappings[payload];
    if (!persisted) {
      const current = { ...this.signalMappings };
      delete current[payload];
      this.signalMappings = current;
      return;
    }
    this.signalMappings = {
      ...this.signalMappings,
      [payload]: JSON.parse(JSON.stringify(persisted)),
    };
  }

  async _createDevice() {
    this.error = null;
    const name = this.formName.trim();
    if (!name) {
      this.error = "Please provide a device name.";
      return;
    }

    const signals = {};
    const actions = Array.isArray(this.formActions) ? this.formActions : [];
    const missing = actions.filter((action) => action.required && !this.formSignals?.[action.key]);
    if (missing.length) {
      this.error = `Missing ${missing.map((entry) => entry.label).join(", ")} payloads.`;
      return;
    }

    actions.forEach((action) => {
      const payload = this.formSignals?.[action.key];
      if (payload) {
        signals[action.key] = payload;
      }
    });

    if ((this.formType === "button" || this.formType === "universal") && Object.keys(signals).length === 0) {
      this.error = "Add at least one action before creating the device.";
      return;
    }

    try {
      await this.hass.callWS({
        type: "raspyrfm/device/create",
        name,
        device_type: this.formType,
        signals,
      });
      await this._refreshDevices();
      this.formName = "";
      this.formSignals = {};
      this.formCustomAction = "";
      this._configureActionsForType(this.formType);
      this.error = null;
    } catch (err) {
      this.error = err?.message || "Failed to create device";
    }
  }

  _normaliseSignals(signals) {
    if (!Array.isArray(signals)) {
      return [];
    }
    const unique = [];
    const seen = new Set();
    signals.forEach((signal) => {
      const key = signal?.uid || `${signal?.payload}-${signal?.received}`;
      if (!key || seen.has(key)) {
        return;
      }
      seen.add(key);
      unique.push(signal);
    });
    if (unique.length > MAX_SIGNAL_HISTORY) {
      return unique.slice(unique.length - MAX_SIGNAL_HISTORY);
    }
    return unique;
  }

  _extractSelectValue(event) {
    if (!event) {
      return "";
    }
    if (event.detail && event.detail.value !== undefined) {
      return event.detail.value;
    }
    if (event.target && event.target.value !== undefined) {
      return event.target.value;
    }
    return "";
  }

  async _deleteDevice(deviceId) {
    await this.hass.callWS({ type: "raspyrfm/device/delete", device_id: deviceId });
    await this._refreshDevices();
  }

  async _invokeAction(deviceId, action) {
    try {
      await this.hass.callWS({ type: "raspyrfm/device/send", device_id: deviceId, action });
      this.error = null;
    } catch (err) {
      this.error = err?.message || "Unable to send action";
    }
  }

  async _handleStartLearning() {
    await this.hass.callWS({ type: "raspyrfm/learning/start" });
    this.learning = true;
  }

  async _handleStopLearning() {
    await this.hass.callWS({ type: "raspyrfm/learning/stop" });
    this.learning = false;
  }
}

customElements.define("raspyrfm-panel", RaspyRFMPanel);
