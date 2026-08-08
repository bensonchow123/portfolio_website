"""
Encode the AVIF ladder that srcset() serves from.
`python build_images.py [--force] [--prune]`

Drop an image next to the ones it belongs with, run this, then reference the
.avif it writes. Widths come from the directory the source sits in.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

# ffmpeg reads AVIF too, so an already-encoded drop still gets a ladder.
SOURCE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp', '.avif')

# variants: the -<width>.avif rungs. cap: widest the canonical file may be,
# None to keep the source width. Backdrops keep it because they cover the
# viewport, photos do not because they sit in a 500px box.
PROFILES = {
    'backdrop': {'variants': (768, 1280, 1920), 'cap': None, 'quality': 55},
    'image': {'variants': (256,), 'cap': 512, 'quality': 70},
    'photo': {'variants': (400, 800), 'cap': 1200, 'quality': 62},
}

ROOTS = (
    ('static/images', lambda name: 'backdrop' if name.endswith('-background') else 'image'),
    ('static/projects', lambda name: 'photo'),
)

# The og:image stays a JPEG. Social scrapers are still unreliable on AVIF, and
# it is never rendered on the site, so converting it would cost link previews.
SKIP = {'benson-chow.jpg'}


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError('%s failed: %s' % (command[0], result.stderr.strip()))
    return result.stdout.strip()


def source_width(path):
    """Upright width. A phone photo tagged sideways stores its width and height
    the wrong way round, and ffmpeg rotates on decode, so swap them here too."""
    fields = dict(line.split('=', 1) for line in run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
         '-show_entries', 'stream=width,height:side_data=rotation',
         '-of', 'default=nw=1', path]).splitlines() if '=' in line)

    rotation = abs(int(fields.get('rotation', 0)))
    return int(fields['height' if rotation in (90, 270) else 'width'])


def quality_to_crf(quality):
    # libaom takes 0-63 where lower is better, inverse of the 0-100 scale the
    # profiles are written in. Measured: quality 62 lands on crf 24.
    return round((100 - quality) * 63 / 100)


def encode(source, target, width, quality, scratch):
    """Scale and encode in one pass. Written to a temporary file first, so a
    source that is its own canonical output can be replaced safely."""
    staged = os.path.join(scratch, 'staged.avif')
    run(['ffmpeg', '-y', '-v', 'error', '-i', source,
         # -2 keeps the height even, lanczos matches the sharpness of the
         # existing ladder rather than the softer bicubic default.
         '-vf', 'scale=%d:-2:flags=lanczos+accurate_rnd' % width,
         '-c:v', 'libaom-av1', '-crf', str(quality_to_crf(quality)),
         '-cpu-used', '4', '-pix_fmt', 'yuv420p', '-still-picture', '1',
         '-f', 'avif', staged])
    os.replace(staged, target)


def outputs_for(source, profile):
    """Every file this source should produce, as (path, width) pairs."""
    width = source_width(source)
    base = os.path.splitext(source)[0]
    cap = profile['cap']

    planned = [('%s.avif' % base, min(width, cap) if cap else width)]
    for rung in profile['variants']:
        # A rung at or above the canonical width would duplicate it.
        if rung < planned[0][1]:
            planned.append(('%s-%d.avif' % (base, rung), rung))
    return width, planned


def find_sources():
    for root, classify in ROOTS:
        for directory, _, names in os.walk(root):
            for name in sorted(names):
                stem, extension = os.path.splitext(name)
                # A generated rung is not a source, or every run would recurse.
                if stem.rsplit('-', 1)[-1].isdigit() and extension.lower() == '.avif':
                    continue
                if extension.lower() in SOURCE_EXTENSIONS and name not in SKIP:
                    yield os.path.join(directory, name), PROFILES[classify(stem)]


def needs_encode(source, source_pixels, target, target_width, force):
    if force:
        return True
    # An AVIF source is its own canonical file, so mtimes say nothing. Only
    # rewrite it when it is wider than the profile allows.
    if os.path.abspath(source) == os.path.abspath(target):
        return source_pixels != target_width
    return not os.path.exists(target) or os.path.getmtime(target) < os.path.getmtime(source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true',
                        help='re-encode even when the AVIF is newer than the source')
    parser.add_argument('--prune', action='store_true',
                        help='delete each source once its whole ladder is written')
    args = parser.parse_args()

    for tool in ('ffmpeg', 'ffprobe'):
        if shutil.which(tool) is None:
            sys.exit('%s is not installed' % tool)

    written = skipped = pruned = 0
    scratch = tempfile.mkdtemp()
    try:
        for source, profile in find_sources():
            pixels, planned = outputs_for(source, profile)
            for target, width in planned:
                if not needs_encode(source, pixels, target, width, args.force):
                    skipped += 1
                    continue
                encode(source, target, width, profile['quality'], scratch)
                print('%s  %dw  %.0f kB' % (target, width, os.path.getsize(target) / 1024))
                written += 1

            # Never delete a source that is also its own canonical output.
            same = os.path.abspath(source) == os.path.abspath(planned[0][0])
            if args.prune and not same and all(os.path.exists(t) for t, _ in planned):
                os.remove(source)
                pruned += 1
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print('wrote %d, up to date %d, pruned %d' % (written, skipped, pruned))
    if written and not args.prune:
        print('sources kept, pass --prune to drop them once you are happy')


if __name__ == '__main__':
    main()
