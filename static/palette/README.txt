Konsole Breeze ANSI palette
===========================

The 16 ANSI colour values used across this site are the Breeze colour scheme
from KDE's Konsole terminal emulator, by the KDE Visual Design Group.

    Upstream: https://github.com/KDE/konsole
    Source:   src/colorschemes/Breeze.colorscheme
    Project:  https://konsole.kde.org/
    Licence:  GPL-2.0-or-later, full text in GPL-2.0-or-later.txt

Nothing from Konsole ships in this repo. The values are transcribed into
assets/app.css as --color-breeze-* theme tokens, eight normal and eight intense,
and every colour on the site resolves to one of them.

On the licence
--------------

Konsole is GPL-2.0-or-later and that is what this file records. The palette
itself is sixteen RGB values, which is closer to a table of facts than to
creative expression, so it is doubtful copyright reaches it at all and the
GPL's terms for derived works almost certainly do not apply to a site that
reuses the numbers. The attribution here is offered because the scheme is
someone's design work and worth crediting, not because a licence compels it.
Nothing about reusing these values places this site under the GPL.

Names
-----

Upstream names the entries Color0 through Color7 with Intense variants. The
tokens here use the ANSI colour names instead, so Color0 is black and
Color4Intense is blue-intense. Black doubles as the terminal panel background,
which is why it looks like a gap in the swatch row on the home page.
