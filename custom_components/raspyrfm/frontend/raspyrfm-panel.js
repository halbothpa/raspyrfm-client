const { LitElement, html, css } = window;

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
      formOn: { state: true },
      formOff: { state: true },
      formTrigger: { state: true },
      error: { state: true },
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

      .error {
        color: var(--error-color);
        margin-bottom: 12px;
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
        }

        .signal-entry {
          flex-direction: column;
          align-items: stretch;
          gap: 12px;
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
    this.formOn = null;
    this.formOff = null;
    this.formTrigger = null;
    this.error = null;
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
    this.signals = signals.signals || [];
  }

  async _loadMappings() {
    const response = await this.hass.callWS({ type: "raspyrfm/signals/map/list" });
    const next = {};
    (response.mappings || []).forEach((entry) => {
      next[entry.payload] = entry;
    });
    this.signalMappings = next;
    this._persistedMappings = JSON.parse(JSON.stringify(next));
  }

  async _subscribeSignals() {
    this._signalUnsub = await this.hass.connection.subscribeMessage((message) => {
      if (message.type !== "event") {
        return;
      }
      const signal = message.event;
      this.signals = [...this.signals, signal];
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
        ${this.error ? html`<div class="error">${this.error}</div>` : ""}
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
    return html`
      <div class="signal-entry">
        <div class="meta-block">
          <div>${signal.payload}</div>
          <div class="signal-meta">${signal.received}</div>
        </div>
        <div class="form-row">
          <mwc-button dense outlined @click=${() => this._selectSignal(signal.payload, "on")}>Set as ON</mwc-button>
          <mwc-button dense outlined @click=${() => this._selectSignal(signal.payload, "off")}>Set as OFF</mwc-button>
          <mwc-button dense outlined @click=${() => this._selectSignal(signal.payload, "trigger")}>Set as trigger</mwc-button>
        </div>
      </div>
    `;
  }

  _renderForm() {
    return html`
      <ha-card header="Create Home Assistant device">
        <div class="card-content form-grid">
          <div class="form-row">
            <ha-textfield label="Name" .value=${this.formName} @input=${(ev) => this._updateName(ev.target.value)}></ha-textfield>
            <ha-select label="Type" .value=${this.formType} @selected=${(ev) => this._updateType(ev.target.value)}>
              <mwc-list-item value="switch">Switch</mwc-list-item>
              <mwc-list-item value="binary_sensor">Binary sensor</mwc-list-item>
            </ha-select>
          </div>
          ${this.formType === "switch"
            ? html`
                <div class="form-row">
                  <span class="pill">ON</span>
                  <span>${this.formOn || "Choose a captured signal"}</span>
                </div>
                <div class="form-row">
                  <span class="pill">OFF<span class="required">*</span></span>
                  <span>${this.formOff || "Choose a captured signal"}</span>
                </div>
              `
            : html`
                <div class="form-row">
                  <span class="pill">Trigger</span>
                  <span>${this.formTrigger || "Choose a captured signal"}</span>
                </div>
              `}
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
          <ha-select label="Category" .value=${mapping.category} @selected=${(ev) => handleCategoryChange(ev.target.value)}>
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
                    ${Object.entries(device.signals || {}).map(([key, value]) => html`<div><strong>${key}</strong>: ${value}</div>`) }
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
    this.formType = value;
  }

  _selectSignal(payload, target) {
    if (this.formType === "switch") {
      if (target === "on") {
        this.formOn = payload;
      } else if (target === "off") {
        this.formOff = payload;
      } else {
        this.error = "Switches do not use trigger signals";
        return;
      }
    } else {
      this.formTrigger = payload;
    }
    this.error = null;
    this.requestUpdate();
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
  }

  async _deleteMapping(payload) {
    await this.hass.callWS({ type: "raspyrfm/signals/map/delete", payload });
    const next = { ...this.signalMappings };
    delete next[payload];
    this.signalMappings = next;
    delete this._persistedMappings[payload];
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
    if (this.formType === "switch") {
      if (!this.formOn) {
        this.error = "Select an ON signal for the switch.";
        return;
      }
      signals.on = this.formOn;
      if (!this.formOff) {
        this.error = "Select an OFF signal for the switch.";
        return;
      }
      signals.off = this.formOff;
    } else {
      if (!this.formTrigger) {
        this.error = "Select a trigger signal for the sensor.";
        return;
      }
      signals.trigger = this.formTrigger;
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
      this.formOn = null;
      this.formOff = null;
      this.formTrigger = null;
      this.error = null;
    } catch (err) {
      this.error = err?.message || "Failed to create device";
    }
  }

  async _deleteDevice(deviceId) {
    await this.hass.callWS({ type: "raspyrfm/device/delete", device_id: deviceId });
    await this._refreshDevices();
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
