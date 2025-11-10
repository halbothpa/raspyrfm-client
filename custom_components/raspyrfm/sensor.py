"""Sensor platform for universal RaspyRFM devices."""

from __future__ import annotations

from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_DEVICE_REGISTRY_UPDATED, SIGNAL_SIGNAL_RECEIVED
from .entity import RaspyRFMEntity
from .hub import RaspyRFMHub
from .storage import RaspyRFMDeviceEntry


async def async_setup_entry(hass, entry, async_add_entities):
    hub: RaspyRFMHub = hass.data[DOMAIN][entry.entry_id]
    entities: Dict[str, RaspyRFMUniversalSensor] = {}

    @callback
    def _ensure_entities() -> None:
        new_entities = []
        for device in hub.storage.iter_devices_by_type("universal"):
            if device.device_id in entities:
                continue
            entity = RaspyRFMUniversalSensor(hub, device)
            entities[device.device_id] = entity
            new_entities.append(entity)
        if new_entities:
            async_add_entities(new_entities)

    _ensure_entities()

    @callback
    def handle_device_update(device_id: str | None) -> None:
        if device_id is None or device_id not in entities:
            _ensure_entities()

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_REGISTRY_UPDATED, handle_device_update)
    )


class RaspyRFMUniversalSensor(RaspyRFMEntity, SensorEntity):
    """A best-effort entity for devices without a dedicated platform."""

    _attr_icon = "mdi:radio-tower"

    def __init__(self, hub: RaspyRFMHub, device: RaspyRFMDeviceEntry) -> None:
        super().__init__(hub, device)
        self._attr_native_value = None
        self._signal_unsub = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def handle_signal(event: Dict[str, Any]) -> None:
            payload = event.get("payload")
            for action, stored_payload in self._device.signals.items():
                if payload == stored_payload:
                    self._attr_native_value = action
                    self.async_write_ha_state()
                    break

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
        return {
            "available_actions": list(self._device.signals.keys()),
        }
