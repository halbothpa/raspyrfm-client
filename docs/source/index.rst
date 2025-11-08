API
===

.. toctree::
   :maxdepth: 2

   raspyrfm_client

Home Assistant UI
=================

The RaspyRFM custom integration exposes a Home Assistant configuration panel to manage RF switches.
The following illustrations capture the refreshed interface that now requires both ON and OFF payloads
before a device can be saved.

.. figure:: _static/raspyrfm-switch-form.svg
   :alt: RaspyRFM device creation form with required OFF signal
   :align: center
   :figwidth: 85%

   Device creation dialog with the mandatory OFF signal field highlighted so users provide
   matching payloads for both switch directions.

.. figure:: _static/raspyrfm-device-list.svg
   :alt: RaspyRFM device overview card in Home Assistant
   :align: center
   :figwidth: 85%

   Home Assistant dashboard card showcasing RaspyRFM switches with clear ON/OFF state buttons
   after the OFF payload requirement was introduced.
