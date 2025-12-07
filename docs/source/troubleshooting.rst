Troubleshooting
===============

Missing ``miniz_export.h`` when building archive unzipper
---------------------------------------------------------
When compiling the Flipper Zero ``archive_unzipper`` application on Ubuntu
GitHub Actions runners, the build may fail with the following error::

    fatal error: miniz_export.h: No such file or directory

The upstream ``miniz`` sources occasionally omit this generated header. A
minimal replacement is now included in this repository at
``applications_user/archive_unzipper/extern/miniz_export.h`` so it is copied
alongside ``miniz.h`` during the build sync step.

If you need to craft the file manually, a tiny stub is sufficient:

.. code-block:: c

    #pragma once
    #ifndef MINIZ_EXPORT
    #define MINIZ_EXPORT
    #endif

Keep the file in the same directory as ``miniz.h`` (for example,
``applications_user/archive_unzipper/extern/``) so the include path resolves
without additional compiler flags.
