Breeze Light cursor
===================

The PNGs here are the default, pointer and text cursors from the Breeze Light
cursor theme by the KDE Visual Design Group.

    breeze-light-*.png          default    arrow, the whole site
    breeze-light-pointer-*.png  pointer    links and buttons
    breeze-light-text-*.png     text       the terminal panel on the home page

    Upstream: https://invent.kde.org/plasma/breeze
    Project:  https://kde.org/plasma-desktop/
    Licence:  LGPL-2.0-or-later, full text in LGPL-2.0-or-later.txt

Modifications
-------------

The upstream artwork ships as an Xcursor binary containing every size. The two
files here are the 32x32 and 64x64 frames extracted from it and written as PNG,
with the premultiplied alpha undone so browsers composite them correctly. The
pixels are otherwise unchanged. Nothing was recoloured or redrawn.

They were then re-encoded with PNG filter type 0 and no ancillary chunks,
which is smaller at this size because filtering mostly transparent rows
costs more than it saves. Decoded pixels are byte identical to the
extracted frames. A re-extract will produce larger files until it is
re-encoded the same way.

Hotspots
--------

Upstream stores these in the Xcursor header and CSS has nowhere to read them
from, so each one is repeated by hand after the url list. Taken from the 32px
frame, because the CSS value is in CSS pixels and the 64px frame is only there
for hidpi.

    default    4 4
    pointer    16 4
    text       16 15
