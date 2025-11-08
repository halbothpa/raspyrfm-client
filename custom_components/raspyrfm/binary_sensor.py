"""Binary sensor platform for RaspyRFM."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from homeassistant.components.binary_sensor import BinarySensorEntity
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

RESET_TIMEOUT = 5


async def async_setup_entry(hass, entry, async_add_entities):
    hub: RaspyRFMHub = hass.data[DOMAIN][entry.entry_id]
    entities: Dict[str, RaspyRFMBinarySensor] = {}

    @callback
    def _ensure_entities() -> None:
        new_entities = []
        for device in hub.storage.iter_devices_by_type("binary_sensor"):
            if device.device_id in entities:
                continue
            entity = RaspyRFMBinarySensor(hub, device)
            entities[device.device_id] = entity
            new_entities.append(entity)
        if new_entities:
            async_add_entities(new_entities)

    @callback
    def _prune_entities() -> None:
        for device_id, entity in list(entities.items()):
            device = hub.storage.get_device(device_id)
            if device is None or device.device_type != "binary_sensor":
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


class RaspyRFMBinarySensor(RaspyRFMEntity, BinarySensorEntity):
    """Representation of a learned binary sensor."""

    def __init__(self, hub: RaspyRFMHub, device: RaspyRFMDeviceEntry) -> None:
        super().__init__(hub, device)
        self._reset_handle: asyncio.TimerHandle | None = None
        self._signal_unsub = None
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def handle_signal(event: Dict[str, Any]) -> None:
            payload = event.get("payload")
            if payload not in self._device.signals.values():
                return
            self._attr_is_on = True
            self.async_write_ha_state()
            if self._reset_handle is not None:
                self._reset_handle.cancel()
            self._reset_handle = self.hass.loop.call_later(RESET_TIMEOUT, self._reset_state)

        self._signal_unsub = async_dispatcher_connect(
            self.hass, SIGNAL_SIGNAL_RECEIVED, handle_signal
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._signal_unsub is not None:
            self._signal_unsub()
            self._signal_unsub = None
        if self._reset_handle is not None:
            self._reset_handle.cancel()
            self._reset_handle = None
        await super().async_will_remove_from_hass()

    @callback
    def _reset_state(self) -> None:
        self._reset_handle = None
        self._attr_is_on = False
        self.async_write_ha_state()
