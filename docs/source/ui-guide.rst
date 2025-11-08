Home Assistant Experience
=========================

The RaspyRFM Home Assistant panel now blends informative validation with live insights that help you
understand each 433&nbsp;MHz payload. The screenshots and diagrams below are generated assets that mirror the
refined user experience.

.. container:: figure-grid

   .. figure:: _static/raspyrfm-switch-form.svg
      :alt: RaspyRFM device creation form with required OFF signal
      :figwidth: 100%

      The device creation workflow emphasises that switches need both ON and OFF payloads before they can be saved.

   .. figure:: _static/raspyrfm-device-list.svg
      :alt: RaspyRFM device overview card in Home Assistant
      :figwidth: 100%

      A refreshed overview groups configured entities with their payload metadata for quick troubleshooting.

Signal Mapping Workspace
========================

The new graphical mapper turns the stream of learned payloads into a topology of sensors, actuators, and misc
signals. You can assign friendly labels, associate payloads with stored RaspyRFM devices, and instantly see the
resulting layout on the canvas.

.. figure:: _static/raspyrfm-signal-mapping.svg
   :alt: RaspyRFM signal mapping canvas mock-up
   :align: center
   :figwidth: 85%

   Nodes are grouped into dedicated swimlanes so you always know which payloads feed sensors, actuators, or auxiliary workflows.

.. figure:: _static/raspyrfm-mapping-editor.svg
   :alt: RaspyRFM mapping editor mock-up
   :align: center
   :figwidth: 85%

   The editor couples category selectors and device toggles with save, reset, and delete controls to curate each payload.

Documentation Theme Preview
===========================

The GitHub Pages site uses the `Furo <https://pradyunsg.me/furo/>`_ theme with a custom accent palette and spacing tweaks that
mirror the Home Assistant frontend.

.. container:: demo-highlight

   .. figure:: _static/raspyrfm-docs-theme.svg
      :alt: RaspyRFM documentation theme sample page
      :figwidth: 100%

      Documentation cards now stretch across the page with generous white space and large typography for better readability on large displays.
