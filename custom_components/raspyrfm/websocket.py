"""Websocket commands exposed by the RaspyRFM integration."""

from __future__ import annotations

import logging
from typing import Any, Dict, Set

import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components import websocket_api

from .const import (
    DOMAIN,
    MAPPING_CATEGORIES,
    SIGNAL_LEARNING_STATE,
    SIGNAL_SIGNAL_RECEIVED,
    WS_TYPE_DEVICE_CREATE,
    WS_TYPE_DEVICE_DELETE,
    WS_TYPE_DEVICE_LIST,
    WS_TYPE_DEVICE_RELOAD,
    WS_TYPE_DEVICE_SEND,
    WS_TYPE_LEARNING_START,
    WS_TYPE_LEARNING_STATUS,
    WS_TYPE_LEARNING_STOP,
    WS_TYPE_LEARNING_SUBSCRIBE,
    WS_TYPE_SIGNAL_MAP_DELETE,
    WS_TYPE_SIGNAL_MAP_LIST,
    WS_TYPE_SIGNAL_MAP_UPDATE,
    WS_TYPE_SIGNALS_LIST,
    WS_TYPE_SIGNALS_SUBSCRIBE,
)
from .hub import RaspyRFMHub

_LOGGER = logging.getLogger(__name__)

HANDLERS_REGISTERED = "_raspyrfm_ws_handlers"


def async_register_websocket_handlers(hass: HomeAssistant) -> None:
    """Register websocket commands."""

    if hass.data.get(HANDLERS_REGISTERED):
        return

    websocket_api.async_register_command(hass, handle_learning_start)
    websocket_api.async_register_command(hass, handle_learning_stop)
    websocket_api.async_register_command(hass, handle_learning_status)
    websocket_api.async_register_command(hass, handle_learning_subscribe)
    websocket_api.async_register_command(hass, handle_signals_list)
    websocket_api.async_register_command(hass, handle_signals_subscribe)
    websocket_api.async_register_command(hass, handle_device_create)
    websocket_api.async_register_command(hass, handle_device_delete)
    websocket_api.async_register_command(hass, handle_device_list)
    websocket_api.async_register_command(hass, handle_device_reload)
    websocket_api.async_register_command(hass, handle_device_send_action)
    websocket_api.async_register_command(hass, handle_signal_map_list)
    websocket_api.async_register_command(hass, handle_signal_map_update)
    websocket_api.async_register_command(hass, handle_signal_map_delete)

    hass.data[HANDLERS_REGISTERED] = True


def _get_hub(hass: HomeAssistant, msg: Dict[str, Any]) -> RaspyRFMHub:
    entry_id = msg.get("entry_id")
    if entry_id is None:
        # fallback to first entry
        if DOMAIN not in hass.data or not hass.data[DOMAIN]:
            raise websocket_api.HomeAssistantWebSocketError("No RaspyRFM entries configured")
        candidates = [
            key for key in hass.data[DOMAIN] if not key.startswith("_")
        ]
        if not candidates:
            raise websocket_api.HomeAssistantWebSocketError("No RaspyRFM entries configured")
        entry_id = candidates[0]

    hub = hass.data[DOMAIN].get(entry_id)
    if hub is None:
        raise websocket_api.HomeAssistantWebSocketError("Unknown RaspyRFM entry")
    return hub


@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_LEARNING_START, vol.Optional("entry_id"): str})
@websocket_api.async_response
async def handle_learning_start(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Start capturing signals."""

    hub = _get_hub(hass, msg)
    await hub.async_start_learning()
    connection.send_result(msg["id"], {"active": True})


@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_LEARNING_STOP, vol.Optional("entry_id"): str})
@websocket_api.async_response
async def handle_learning_stop(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Stop capturing signals."""

    hub = _get_hub(hass, msg)
    await hub.async_stop_learning()
    connection.send_result(msg["id"], {"active": False})


@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_LEARNING_STATUS, vol.Optional("entry_id"): str})
@websocket_api.async_response
async def handle_learning_status(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Return the current learning state."""

    hub = _get_hub(hass, msg)
    connection.send_result(msg["id"], {"active": hub.learn_manager.is_active})


@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_LEARNING_SUBSCRIBE, vol.Optional("entry_id"): str})
@callback
def handle_learning_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Subscribe to learning state updates."""

    @callback
    def forward(payload: Dict[str, Any]) -> None:
        connection.send_message(websocket_api.event_message(msg["id"], payload))

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_LEARNING_STATE, forward
    )
    connection.send_result(msg["id"])


@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_SIGNALS_LIST, vol.Optional("entry_id"): str})
@websocket_api.async_response
async def handle_signals_list(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Return a list of currently captured signals."""

    hub = _get_hub(hass, msg)
    signals = await hub.learn_manager.async_list_signals()
    connection.send_result(msg["id"], {"signals": signals})


@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_SIGNALS_SUBSCRIBE, vol.Optional("entry_id"): str})
@callback
def handle_signals_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Subscribe to incoming signals."""

    @callback
    def forward(payload: Dict[str, Any]) -> None:
        connection.send_message(websocket_api.event_message(msg["id"], payload))

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_SIGNAL_RECEIVED, forward
    )
    connection.send_result(msg["id"])


SUPPORTED_DEVICE_TYPES = ["switch", "binary_sensor", "light", "button", "universal"]


_DEVICE_CREATE_SCHEMA = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_DEVICE_CREATE,
        vol.Required("name"): cv.string,
        vol.Required("device_type"): vol.In(SUPPORTED_DEVICE_TYPES),
        vol.Required("signals"): {cv.string: cv.string},
        vol.Optional("metadata"): {cv.string: cv.Any()},
        vol.Optional("entry_id"): str,
    }
)


@websocket_api.websocket_command(_DEVICE_CREATE_SCHEMA)
@websocket_api.async_response
async def handle_device_create(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Create a device from captured signals."""

    hub = _get_hub(hass, msg)
    _validate_device_payload(msg["device_type"], msg["signals"])
    device = await hub.async_create_device(
        msg["name"], msg["device_type"], msg["signals"], msg.get("metadata")
    )
    connection.send_result(msg["id"], {"device": device.to_dict()})


@websocket_api.websocket_command({
    vol.Required("type"): WS_TYPE_DEVICE_DELETE,
    vol.Required("device_id"): cv.string,
    vol.Optional("entry_id"): str,
})
@websocket_api.async_response
async def handle_device_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Delete a stored device."""

    hub = _get_hub(hass, msg)
    await hub.async_remove_device(msg["device_id"])
    connection.send_result(msg["id"], {})


@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_DEVICE_LIST, vol.Optional("entry_id"): str})
@websocket_api.async_response
async def handle_device_list(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Return the list of stored devices."""

    hub = _get_hub(hass, msg)
    devices = [device.to_dict() for device in hub.iter_devices()]
    connection.send_result(msg["id"], {"devices": devices})


@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_DEVICE_RELOAD, vol.Optional("entry_id"): str})
@websocket_api.async_response
async def handle_device_reload(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Reload devices from persistent storage."""

    hub = _get_hub(hass, msg)
    await hub.async_reload_devices()
    connection.send_result(msg["id"], {})


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_DEVICE_SEND,
        vol.Required("device_id"): cv.string,
        vol.Required("action"): cv.string,
        vol.Optional("entry_id"): str,
    }
)
@websocket_api.async_response
async def handle_device_send_action(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: Dict[str, Any],
) -> None:
    """Trigger a stored signal for a RaspyRFM device."""

    hub = _get_hub(hass, msg)
    try:
        await hub.async_send_device_action(msg["device_id"], msg["action"])
    except ValueError as err:
        raise websocket_api.HomeAssistantWebSocketError(str(err)) from err
    connection.send_result(msg["id"], {})


def _validate_device_payload(device_type: str, signals: Dict[str, str]) -> None:
    """Ensure the provided payload mapping matches the expected schema."""

    required: Dict[str, str] = {}
    optional: Set[str] = set()

    if device_type == "switch":
        required = {"on": "ON payload", "off": "OFF payload"}
    elif device_type == "binary_sensor":
        required = {"trigger": "Trigger payload"}
    elif device_type == "light":
        required = {"on": "ON payload"}
        optional = {"off", "bright", "dim"}
    elif device_type in {"button", "universal"}:
        if not signals:
            raise websocket_api.HomeAssistantWebSocketError(
                "Provide at least one signal mapping"
            )
    else:
        raise websocket_api.HomeAssistantWebSocketError("Unsupported device type")

    missing = [key for key in required if key not in signals or not signals[key]]
    if missing:
        raise websocket_api.HomeAssistantWebSocketError(
            f"Missing {', '.join(missing)} for {device_type}"
        )

    unexpected = [
        key
        for key in signals
        if key not in required and key not in optional and device_type not in {"button", "universal"}
    ]
    if unexpected:
        raise websocket_api.HomeAssistantWebSocketError(
            f"Unexpected signals for {device_type}: {', '.join(unexpected)}"
        )


@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_SIGNAL_MAP_LIST, vol.Optional("entry_id"): str})
@websocket_api.async_response
async def handle_signal_map_list(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Return the stored signal mapping metadata."""

    hub = _get_hub(hass, msg)
    mappings = await hub.async_list_signal_mappings()
    connection.send_result(msg["id"], {"mappings": mappings})


_SIGNAL_MAP_UPDATE_SCHEMA = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_SIGNAL_MAP_UPDATE,
        vol.Required("payload"): cv.string,
        vol.Required("category"): vol.In(MAPPING_CATEGORIES),
        vol.Required("label"): cv.string,
        vol.Optional("linked_devices"): [cv.string],
        vol.Optional("entry_id"): str,
    }
)


@websocket_api.websocket_command(_SIGNAL_MAP_UPDATE_SCHEMA)
@websocket_api.async_response
async def handle_signal_map_update(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Store mapping information for a payload."""

    hub = _get_hub(hass, msg)
    mapping = await hub.async_set_signal_mapping(
        msg["payload"],
        msg["category"],
        msg["label"],
        msg.get("linked_devices"),
    )
    connection.send_result(msg["id"], {"mapping": mapping.to_dict()})


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_SIGNAL_MAP_DELETE,
        vol.Required("payload"): cv.string,
        vol.Optional("entry_id"): str,
    }
)
@websocket_api.async_response
async def handle_signal_map_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]) -> None:
    """Remove mapping information for a payload."""

    hub = _get_hub(hass, msg)
    await hub.async_remove_signal_mapping(msg["payload"])
    connection.send_result(msg["id"], {})
