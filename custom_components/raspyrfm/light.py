"""Light platform for RaspyRFM."""

from __future__ import annotations

from typing import Any, Dict

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_DEVICE_REGISTRY_UPDATED, SIGNAL_SIGNAL_RECEIVED
from .entity import RaspyRFMEntity
from .hub import RaspyRFMHub
from .storage import RaspyRFMDeviceEntry


async def async_setup_entry(hass, entry, async_add_entities):
    hub: RaspyRFMHub = hass.data[DOMAIN][entry.entry_id]
    entities: Dict[str, RaspyRFMLight] = {}

    @callback
    def _ensure_entities() -> None:
        new_entities = []
        for device in hub.storage.iter_devices_by_type("light"):
            if device.device_id in entities:
                continue
            entity = RaspyRFMLight(hub, device)
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


class RaspyRFMLight(RaspyRFMEntity, LightEntity):
    """Representation of a dimmable RaspyRFM light."""

    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

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
            elif payload == self._device.signals.get("off"):
                self._attr_is_on = False
            elif payload == self._device.signals.get("bright"):
                self._attr_is_on = True
            elif payload == self._device.signals.get("dim") and "off" not in self._device.signals:
                # Devices without an explicit OFF signal often dim to turn off.
                self._attr_is_on = False
            else:
                return
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
        return {"available_signals": list(self._device.signals.keys())}

    async def async_turn_on(self, **kwargs: Any) -> None:
        payload = self._device.signals.get("on") or self._device.signals.get("bright")
        if payload is None:
            raise ValueError("No ON or BRIGHT signal stored for this device")
        await self._hub.async_send_raw(payload)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        payload = self._device.signals.get("off") or self._device.signals.get("dim")
        if payload is None:
            raise ValueError("No OFF or DIM signal stored for this device")
        await self._hub.async_send_raw(payload)
        self._attr_is_on = False
        self.async_write_ha_state()
