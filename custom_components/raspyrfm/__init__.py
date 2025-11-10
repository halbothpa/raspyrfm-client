"""Home Assistant integration for the RaspyRFM gateway."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_ACTION,
    ATTR_DEVICE_ID,
    DATA_SERVICE_REGISTERED,
    DOMAIN,
    PLATFORMS,
    SERVICE_SEND_ACTION,
)
from .hub import RaspyRFMHub
from .panel import async_register_panel, async_unregister_panel
from .websocket import async_register_websocket_handlers

_LOGGER = logging.getLogger(__name__)

SEND_ACTION_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_ACTION): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RaspyRFM from a config entry."""
    hub = RaspyRFMHub(hass, entry)

    try:
        await hub.async_setup()
    except OSError as err:
        raise ConfigEntryNotReady("Unable to initialise RaspyRFM hub") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    if not hass.data[DOMAIN].get(DATA_SERVICE_REGISTERED):

        async def _async_handle_send_action(call) -> None:
            device_id: str = call.data[ATTR_DEVICE_ID]
            action: str = call.data[ATTR_ACTION]
            for key, candidate in hass.data[DOMAIN].items():
                if key.startswith("_"):
                    continue
                if candidate.storage.get_device(device_id):
                    await candidate.async_send_device_action(device_id, action)
                    break
            else:
                raise ValueError(f"Unknown RaspyRFM device: {device_id}")

        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_ACTION,
            _async_handle_send_action,
            schema=SEND_ACTION_SCHEMA,
        )
        hass.data[DOMAIN][DATA_SERVICE_REGISTERED] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await async_register_panel(hass, entry)
    async_register_websocket_handlers(hass)

    entry.async_on_unload(entry.add_update_listener(async_update_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a RaspyRFM config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hub = hass.data[DOMAIN].pop(entry.entry_id)
        await hub.async_unload()
        await async_unregister_panel(hass, entry)

        remaining_hubs = [
            key for key in hass.data[DOMAIN] if not key.startswith("_")
        ]
        if not remaining_hubs and hass.data[DOMAIN].pop(DATA_SERVICE_REGISTERED, None):
            hass.services.async_remove(DOMAIN, SERVICE_SEND_ACTION)

    return unload_ok


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    hub: RaspyRFMHub = hass.data[DOMAIN][entry.entry_id]
    await hub.async_update_entry(entry)
