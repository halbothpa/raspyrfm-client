"""Switch platform for RaspyRFM."""

from __future__ import annotations

from typing import Any, Dict

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DOMAIN,
    SIGNAL_DEVICE_REGISTRY_UPDATED,
    SIGNAL_DEVICE_REMOVED,
    SIGNAL_SIGNAL_RECEIVED,
)
from .entity import RaspyRFMEntity
from .hub import RaspyRFMHub
from .storage import RaspyRFMDeviceEntry


async def async_setup_entry(hass, entry, async_add_entities):
    hub: RaspyRFMHub = hass.data[DOMAIN][entry.entry_id]
    entities: Dict[str, RaspyRFMSwitch] = {}

    @callback
    def _ensure_entities() -> None:
        new_entities = []
        for device in hub.storage.iter_devices_by_type("switch"):
            if device.device_id in entities:
                continue
            entity = RaspyRFMSwitch(hub, device)
            entities[device.device_id] = entity
            new_entities.append(entity)
        if new_entities:
            async_add_entities(new_entities)

    @callback
    def _prune_entities() -> None:
        for device_id, entity in list(entities.items()):
            device = hub.storage.get_device(device_id)
            if device is None or device.device_type != "switch":
                entities.pop(device_id)
                hass.async_create_task(entity.async_remove())

    _ensure_entities()

    @callback
    def handle_device_update(device_id: str | None) -> None:
        if device_id is None:
            _ensure_entities()
            _prune_entities()
            return

        if device_id not in entities:
            _ensure_entities()
            return

        _prune_entities()

    @callback
    def handle_device_removed(device_id: str) -> None:
        entity = entities.pop(device_id, None)
        if entity is not None:
            hass.async_create_task(entity.async_remove())

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_REGISTRY_UPDATED, handle_device_update)
    )
    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_REMOVED, handle_device_removed)
    )


class RaspyRFMSwitch(RaspyRFMEntity, SwitchEntity):
    """Representation of a learned switch."""

    def __init__(self, hub: RaspyRFMHub, device: RaspyRFMDeviceEntry) -> None:
        super().__init__(hub, device)
        self._attr_is_on = False
        self._signal_unsub = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def handle_signal(event: Dict[str, Any]) -> None:
            payload = event.get("payload")
            if payload == self._device.signals.get("on"):
                self._attr_is_on = True
                self.async_write_ha_state()
            elif payload == self._device.signals.get("off"):
                self._attr_is_on = False
                self.async_write_ha_state()

        self._signal_unsub = async_dispatcher_connect(
            self.hass, SIGNAL_SIGNAL_RECEIVED, handle_signal
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._signal_unsub is not None:
            self._signal_unsub()
            self._signal_unsub = None
        await super().async_will_remove_from_hass()

    async def async_turn_on(self, **kwargs: Any) -> None:
        signal = self._device.signals.get("on")
        if signal is None:
            raise ValueError("No ON signal stored for this device")
        await self._hub.async_send_raw(signal)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        signal = self._device.signals.get("off")
        if signal is None:
            raise ValueError("No OFF signal stored for this device")
        await self._hub.async_send_raw(signal)
        self._attr_is_on = False
        self.async_write_ha_state()
