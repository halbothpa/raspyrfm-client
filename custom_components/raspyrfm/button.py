"""Button platform for RaspyRFM."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from homeassistant.components.button import ButtonEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SIGNAL_DEVICE_REGISTRY_UPDATED, SIGNAL_SIGNAL_RECEIVED
from .entity import RaspyRFMEntity
from .hub import RaspyRFMHub
from .storage import RaspyRFMDeviceEntry


async def async_setup_entry(hass, entry, async_add_entities):
    hub: RaspyRFMHub = hass.data[DOMAIN][entry.entry_id]
    entities: Dict[str, RaspyRFMButton] = {}

    @callback
    def _ensure_entities() -> None:
        new_entities = []
        for device in hub.storage.iter_devices_by_type("button"):
            for action in sorted(device.signals.keys()):
                key = f"{device.device_id}:{action}"
                if key in entities:
                    continue
                entity = RaspyRFMButton(hub, device, action)
                entities[key] = entity
                new_entities.append(entity)
        if new_entities:
            async_add_entities(new_entities)

    _ensure_entities()

    @callback
    def handle_device_update(device_id: str | None) -> None:
        if device_id is None:
            _ensure_entities()
            return
        device = hub.storage.get_device(device_id)
        if device is None:
            _ensure_entities()
            return
        stale_keys = [
            key
            for key in list(entities)
            if key.startswith(f"{device_id}:")
            and key.split(":", 1)[1] not in device.signals
        ]
        for key in stale_keys:
            entity = entities.pop(key)
            if entity.hass is not None:
                entity.hass.async_create_task(entity.async_remove())
        for action in device.signals.keys():
            key = f"{device_id}:{action}"
            if key not in entities:
                _ensure_entities()
                return
        # Existing entities will refresh their state on next dispatcher tick.

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_REGISTRY_UPDATED, handle_device_update)
    )


class RaspyRFMButton(RaspyRFMEntity, ButtonEntity):
    """Representation of a RaspyRFM button action."""

    def __init__(self, hub: RaspyRFMHub, device: RaspyRFMDeviceEntry, action: str) -> None:
        super().__init__(hub, device)
        self._action = action
        self._last_triggered: datetime | None = None
        self._signal_unsub = None

    @property
    def name(self) -> str:
        base = super().name
        label = self._action.replace("_", " ").title()
        return f"{base} {label}"

    @property
    def unique_id(self) -> str:
        return f"{super().unique_id}:{self._action}"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def handle_signal(event: Dict[str, Any]) -> None:
            payload = event.get("payload")
            if payload == self._device.signals.get(self._action):
                self._last_triggered = dt_util.utcnow()
                self.async_write_ha_state()

        self._signal_unsub = async_dispatcher_connect(
            self.hass, SIGNAL_SIGNAL_RECEIVED, handle_signal
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._signal_unsub is not None:
            self._signal_unsub()
            self._signal_unsub = None
        await super().async_will_remove_from_hass()

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        attrs: Dict[str, Any] = {
            "action": self._action,
        }
        if self._last_triggered is not None:
            attrs["last_triggered"] = self._last_triggered.isoformat()
        return attrs

    async def async_press(self, **kwargs: Any) -> None:
        payload = self._device.signals.get(self._action)
        if payload is None:
            raise ValueError(f"No signal stored for action {self._action}")
        await self._hub.async_send_raw(payload)
        self._last_triggered = dt_util.utcnow()
        self.async_write_ha_state()
