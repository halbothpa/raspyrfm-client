Home Assistant Components
=========================

This section documents the backend pieces that power the RaspyRFM
Home Assistant integration.  Each subsection links to the relevant
source files and explains how the pieces collaborate to monitor radio
traffic, learn payloads, and expose entities inside Home Assistant.

Configuration flow and setup
----------------------------

RaspyRFM is installed as a config entry.  The integration registers a
config flow that resolves the gateway host name and persists the chosen
UDP port.  Once an entry is created, ``async_setup_entry`` instantiates
the hub, forwards platform setups, and makes the management panel,
websocket commands, and the ``raspyrfm.send_action`` service available so
payloads can be replayed from automations.

.. literalinclude:: ../../custom_components/raspyrfm/config_flow.py
   :language: python
   :lines: 1-81

.. literalinclude:: ../../custom_components/raspyrfm/__init__.py
   :language: python
   :lines: 1-53

Gateway and hub orchestration
-----------------------------

The :class:`~custom_components.raspyrfm.gateway.RaspyRFMGateway` wraps the
UDP socket used by the hardware bridge.  The hub owns a gateway instance
and coordinates persistent storage, signal learning, and entity updates
via Home Assistant dispatcher signals.

.. literalinclude:: ../../custom_components/raspyrfm/gateway.py
   :language: python
   :lines: 1-54

.. literalinclude:: ../../custom_components/raspyrfm/hub.py
   :language: python
   :lines: 1-239

Signal learning pipeline
------------------------

The :class:`~custom_components.raspyrfm.learn.LearnManager` binds a UDP
listener to ``DEFAULT_LISTEN_PORT`` (49881) and streams payloads into the
hub.  Incoming packets are normalised into ``LearnedSignal`` dataclasses
and broadcast over dispatcher events so that the UI and entity platforms
receive live updates.  Each payload is fingerprinted against the
``raspyrfm-client`` device library using the ``classifier`` helper, which
allows the UI to suggest an entity type even when users have not labelled
the signal yet.

.. literalinclude:: ../../custom_components/raspyrfm/learn.py
   :language: python
   :lines: 1-133

.. literalinclude:: ../../custom_components/raspyrfm/classifier.py
   :language: python
   :lines: 1-220

Persistent storage and device registry
--------------------------------------

Two storage helpers manage device definitions and optional metadata about
captured payloads.  The ``RaspyRFMDeviceStorage`` class keeps track of
all entity types created from learned signals, including switches, lights,
button groups, and universal listeners, while ``RaspyRFMSignalMapStorage``
stores labels, semantic categories, and links between payloads and devices.

.. literalinclude:: ../../custom_components/raspyrfm/storage.py
   :language: python
   :lines: 1-193

Entity platforms
----------------

All entities share a base class that listens for dispatcher updates when
devices change.  The entity platforms iterate over stored devices, create
entities on demand, and react to live signal messages from the learning
pipeline.  Besides switches and binary sensors the integration now exposes
a light platform for dimmable actuators, a button platform that creates one
entity per stored action, and a universal sensor that records and replays
raw payloads when no fingerprint matches.

.. literalinclude:: ../../custom_components/raspyrfm/entity.py
   :language: python
   :lines: 1-57

.. literalinclude:: ../../custom_components/raspyrfm/switch.py
   :language: python
   :lines: 1-98

.. literalinclude:: ../../custom_components/raspyrfm/binary_sensor.py
   :language: python
   :lines: 1-88

.. literalinclude:: ../../custom_components/raspyrfm/light.py
   :language: python
   :lines: 1-103

.. literalinclude:: ../../custom_components/raspyrfm/button.py
   :language: python
   :lines: 1-124

.. literalinclude:: ../../custom_components/raspyrfm/sensor.py
   :language: python
   :lines: 1-81

Websocket API surface
---------------------

The integration exposes a websocket namespace under ``raspyrfm/``.  The
commands cover the full lifecycle: starting and stopping capture, listing
signals, creating or deleting devices, triggering stored actions, and
maintaining the optional signal mapping metadata.

.. literalinclude:: ../../custom_components/raspyrfm/websocket.py
   :language: python
   :lines: 1-320

Panel registration and static assets
------------------------------------

Every config entry registers a static path and serves a custom panel that
is restricted to administrators.  The panel is implemented as a LitElement
module that runs entirely inside the Home Assistant frontend.

.. literalinclude:: ../../custom_components/raspyrfm/panel.py
   :language: python
   :lines: 1-48

Frontend component
------------------

The ``raspyrfm-panel`` web component drives the onboarding experience for
RaspyRFM users.  It exposes learning controls, renders cards summarising
captured payloads, fingerprints signals against the Python library to
suggest device types, provides a flexible creation form, and lets users map
payloads to semantic categories with optional device links.  The component
relies exclusively on the websocket commands described above, so no
additional backend endpoints are required.

.. literalinclude:: ../../custom_components/raspyrfm/frontend/raspyrfm-panel.js
   :language: javascript
   :lines: 1-520

Home Assistant integration checklist
------------------------------------

To use the integration in your own Home Assistant instance:

1. Copy the ``custom_components/raspyrfm`` directory into your Home
   Assistant ``config/custom_components`` folder.
2. Restart Home Assistant so the new integration is discovered.
3. Navigate to *Settings → Devices & Services* and add the RaspyRFM
   integration.  Provide the host name or IP address of the RaspyRFM
   gateway and the UDP port it listens on (``49880`` by default).
4. Open the *RaspyRFM* panel from the sidebar to start a learning session
   and capture payloads.  Use the *Create Home Assistant device* card to
   turn them into entities, then link payloads to devices in the mapping
   workspace.
5. Optional: update the labels, categories, and device associations for
   each payload in the mapping workspace.  The data is persisted through
   ``.storage/raspyrfm_signal_map`` and is restored after Home Assistant
   restarts.
