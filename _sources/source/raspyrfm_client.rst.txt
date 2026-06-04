raspyrfm_client package
=======================

The ``raspyrfm_client`` package is the orchestration layer that glues gateways,
control units, and device metadata together.  It discovers available
implementations on import, provides ergonomic helpers for runtime access, and
ships with base classes you can extend to model new radio-frequency hardware.
This chapter now pairs narrative explanations, architecture diagrams, and API
maps so you can move from concept to implementation without leaving the page.

Overview
--------

At the centre of the package sits :class:`~raspyrfm_client.client.RaspyRFMClient`.
It coordinates three core responsibilities:

``Discovery``
   Automatically import all gateway and control-unit modules under
   :mod:`raspyrfm_client.device_implementations`.  Any modules you drop into the
   tree become available the next time
   :meth:`~raspyrfm_client.client.RaspyRFMClient.reload_implementation_classes`
   runs.
``Cataloguing``
   Provide quick lookups for known :class:`~raspyrfm_client.device_implementations.manufacturer_constants.Manufacturer`
   values and the models each manufacturer exposes.  These enumerations keep the
   public API self-documenting.
``Execution``
   Instantiate gateways and control units that conform to the shared base
   classes in :mod:`raspyrfm_client.device_implementations.gateway.base` and
   :mod:`raspyrfm_client.device_implementations.controlunit.base`.  Once
   instantiated, helper methods such as
   :meth:`~raspyrfm_client.client.RaspyRFMClient.get_gateway` hand you a
   ready-to-use transport implementation.

System architecture
-------------------

.. figure:: _static/raspyrfm-client-architecture.svg
   :alt: Architecture diagram showing discovery, client core, and gateway/control unit execution
   :align: center
   :class: ui-showcase-figure

   RaspyRFMClient coordinates discovery (left), orchestration (centre), and the
   transport surface (right).  Discovery scans the ``device_implementations``
   namespace, the core aggregates metadata and exposes helper methods, while the
   transport layer instantiates gateways and control units that communicate with
   real hardware.

Legend:

* **Discovery bay** – Base classes enumerate manufacturers, default models, and
  lazy-import hooks.
* **Client core** – A single ``RaspyRFMClient`` instance caches the catalogue,
  enforces typing, and brokers connections.
* **Execution pods** – Gateway and control-unit instances deliver the actual
  radio operations, exposing ``open``, ``close``, and ``send_code`` semantics.

Quick start
-----------

Follow the numbered comments to see how a typical integration unfolds:

.. code-block:: python

   from raspyrfm_client.client import RaspyRFMClient
   from raspyrfm_client.device_implementations.manufacturer_constants import Manufacturer
   from raspyrfm_client.device_implementations.gateway.manufacturer.gateway_constants import GatewayModel

   # 1. Spin up the client; discovery runs on instantiation.
   client = RaspyRFMClient()

   # 2. Inspect the catalogue discovered on import.
   print(sorted(client.get_supported_gateway_manufacturers()))

   # 3. Select a specific gateway implementation by manufacturer/model.
   gateway = client.get_gateway(
       manufacturer=Manufacturer.RASPYRFM,
       model=GatewayModel.RASPYRFM_DEFAULT,
       host="192.168.0.42",
       port=49880,
   )

   # 4. Interact with the gateway using the shared base-class contract.
   gateway.open()
   gateway.send_code(code="on", socket_id="A1")
   gateway.close()

Core concepts
-------------

* **Gateways** translate between RaspyRFM and physical transmitters.  They
  inherit from :class:`~raspyrfm_client.device_implementations.gateway.base.GatewayBase`
  and encapsulate connection handling plus RF send logic.
* **Control units** describe controllable sockets, blinds, and switches.  They
  derive from :class:`~raspyrfm_client.device_implementations.controlunit.base.ControlUnitBase`
  and expose high-level actions defined in
  :mod:`raspyrfm_client.device_implementations.controlunit.actions`.
* **Manufacturers** and **models** are enumerated in the
  :mod:`raspyrfm_client.device_implementations.manufacturer_constants` and
  :mod:`raspyrfm_client.device_implementations.gateway.manufacturer.gateway_constants`
  modules respectively, giving you strongly-typed handles for each supported
  device family.
* **Device manifests** (``raspyrfm_client.device``) capture metadata that the
  UI and automation engine consume for labelling, validation, and previews.

Lifecycle checklist
-------------------

Use this sequence when integrating with a new installation:

1. **Initialise** – Instantiate :class:`~raspyrfm_client.client.RaspyRFMClient`
   as early as possible so discovery populates the catalogue.
2. **Catalogue** – Inspect manufacturers and models using ``get_supported_*``
   methods before hard-coding enums in configuration files.
3. **Connect** – Use :meth:`~raspyrfm_client.client.RaspyRFMClient.get_gateway`
   to create transport instances.  Gateways share a consistent interface across
   manufacturers, so you can swap models without refactoring call sites.
4. **Compose control units** – Build composite scenes by fetching
   :meth:`~raspyrfm_client.client.RaspyRFMClient.get_controlunit` instances and
   triggering actions from automation code.
5. **Reload** – Call
   :meth:`~raspyrfm_client.client.RaspyRFMClient.reload_implementation_classes`
   after deploying new modules or updating vendor-specific logic; the client will
   re-import the tree and rebuild the catalogue.

Extending the catalogue
-----------------------

1. Create a subclass of
   :class:`~raspyrfm_client.device_implementations.gateway.base.GatewayBase` or
   :class:`~raspyrfm_client.device_implementations.controlunit.base.ControlUnitBase`
   in the appropriate ``device_implementations`` subpackage.
2. Register new enum values in
   :mod:`raspyrfm_client.device_implementations.manufacturer_constants` and
   (for gateways) :mod:`raspyrfm_client.device_implementations.gateway.manufacturer.gateway_constants`.
3. Wire any bespoke actions into
   :mod:`raspyrfm_client.device_implementations.controlunit.actions` so UI and
   automation tooling inherit correct labelling.
4. Call
   :meth:`~raspyrfm_client.client.RaspyRFMClient.reload_implementation_classes`
   or instantiate a fresh :class:`~raspyrfm_client.client.RaspyRFMClient` to pull
   in the new module.
5. Use :meth:`~raspyrfm_client.client.RaspyRFMClient.get_gateway` and
   :meth:`~raspyrfm_client.client.RaspyRFMClient.get_controlunit` to obtain your
   customised implementations.

Implementation map
------------------

.. list-table:: Key modules and their responsibilities
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`raspyrfm_client.client`
     - High-level client that bootstraps implementations, performs discovery,
       maintains the manufacturer/model catalogue, and exposes helper methods to
       retrieve gateways and control units.
   * - :mod:`raspyrfm_client.device`
     - Data models used to serialise discovered devices, entity manifests, and
       control-unit payload definitions.
   * - :mod:`raspyrfm_client.device_implementations`
     - Namespace package containing gateway/control-unit classes organised by
       manufacturer and model.  Place your subclasses here to extend the
       catalogue.
   * - :mod:`raspyrfm_client.device_implementations.gateway.base`
     - Abstract base types and mixins shared by all gateway implementations.
   * - :mod:`raspyrfm_client.device_implementations.controlunit.base`
     - Abstract base types and helper utilities for modelling switchable
       devices.
   * - :mod:`raspyrfm_client.device_implementations.controlunit.actions`
     - Re-usable action descriptors (on/off, dim, toggle, etc.) that concrete
       control units import.
   * - :mod:`raspyrfm_client.discovery`
     - Internal helper that walks the package tree, imports modules lazily, and
       guards against circular dependencies during reloads.

Integration patterns
--------------------

* **Home Assistant bridge** – Use the RaspyRFMClient as a long-lived singleton
  in a background task.  Fetch control units for each automation and queue
  ``send_code`` operations onto an executor to maintain responsiveness.
* **Test harness** – Couple :mod:`raspyrfm_client.client` with the
  :mod:`example.py` script.  By swapping the manufacturer and model enums you can
  validate new RF payloads without reconfiguring your production deployment.
* **Custom dashboards** – Serialise device metadata from
  :mod:`raspyrfm_client.device` into JSON and feed it into front-end graphs or UI
  cards.  The data classes include human-friendly labels that match the UI
  showcase.

Troubleshooting
---------------

* **Missing implementations** – Ensure the Python package path includes the
  directory containing your new modules before calling
  :class:`~raspyrfm_client.client.RaspyRFMClient`.  ``reload_implementation_classes``
  only rescans importable modules.
* **Enum mismatches** – Align manufacturer and model enums across gateway and
  control-unit modules.  The client raises a ``KeyError`` if the pair is unknown,
  helping you detect typo-induced bugs early.
* **Connection instability** – Gateways expose a context manager API.  Use
  ``with client.get_gateway(...) as gateway:`` to ensure ``open``/``close`` calls
  pair correctly even when exceptions occur.

API reference
-------------

.. toctree::
   :maxdepth: 1

   raspyrfm_client.device
   raspyrfm_client.device.manufacturer

.. automodule:: raspyrfm_client.client
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: raspyrfm_client
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: raspyrfm_client.device_implementations
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: raspyrfm_client.device_implementations.gateway.base
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: raspyrfm_client.device_implementations.controlunit.base
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: raspyrfm_client.device_implementations.controlunit.actions
   :members:
   :undoc-members:
   :show-inheritance:
