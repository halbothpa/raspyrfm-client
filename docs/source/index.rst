RaspyRFM Client Manual
======================

.. toctree::
   :hidden:
   :maxdepth: 2

   homeassistant_components
   ui-guide
   ui-showcase
   raspyrfm_client

Overview
--------

RaspyRFM bridges inexpensive 433&nbsp;MHz receivers and transmitters with
`Home Assistant <https://www.home-assistant.io/>`_.  The integration that
ships with this repository contains:

* A UDP ``gateway`` helper that speaks the RaspyRFM bridge protocol.
* A ``hub`` coordinating the learn manager, persistent storage, and entity
  registry updates inside Home Assistant.
* Binary sensor and switch platforms that translate learned payloads into
  Home Assistant entities.
* A rich management panel implemented as a LitElement web component for
  capturing, annotating, and replaying radio payloads.

The sections below document how these pieces fit together and how you can
adapt them for your own setup.

Quick links
~~~~~~~~~~~

* :doc:`homeassistant_components` – Backend components and Home Assistant
  integration details.
* :doc:`ui-guide` – Panels, cards, and mapping workspace provided by the
  custom frontend.
* :doc:`ui-showcase` – Visual highlights of the refreshed management panel.
* :doc:`raspyrfm_client` – Python API reference for the reusable client
  library.
