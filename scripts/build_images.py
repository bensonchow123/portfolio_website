"""Make AVIF versions for responsive images.
Run `python -m scripts.build_images` from the repo root after adding an image."""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

# We can read AVIF files too, so added AVIF files get the same sizes.
SOURCE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp', '.avif')

# `variants` lists the smaller files we make. `cap` is the largest main file.
# Backgrounds keep their original width. Photos are shown at about 500px.
PROFILES = {
    'backdrop': {'variants': (768, 1280, 1920), 'cap': None, 'quality': 55},
    'image': {'variants': (256,), 'cap': 512, 'quality': 70},
    'photo': {'variants': (400, 800), 'cap': 1200, 'quality': 62},
}

# Skip sizes that are too close together. They add another request without
# helping much, and can make rescaled screenshots look softer.
MIN_GAP = 0.15

ROOTS = (
    ('static/images', lambda name: 'backdrop' if name.endswith('-background') else 'image'),
    ('static/projects', lambda name: 'photo'),
)

# Keep the social preview image as a JPEG. Some crawlers still do not support AVIF.
# It is not shown on the site anyway.
SKIP = {'benson-chow.jpg'}


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError('%s failed: %s' % (command[0], result.stderr.strip()))
    return result.stdout.strip()


def source_width(path):
    """Return the displayed width, even for a sideways phone photo."""
    fields = dict(line.split('=', 1) for line in run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
         '-show_entries', 'stream=width,height:side_data=rotation',
         '-of', 'default=nw=1', path]).splitlines() if '=' in line)

    rotation = abs(int(fields.get('rotation', 0)))
    return int(fields['height' if rotation in (90, 270) else 'width'])


def quality_to_crf(quality):
    # libaom uses a CRF scale from 0 to 63. Lower values mean higher quality.
    # We turn our 0 to 100 setting around for it.
    return round((100 - quality) * 63 / 100)


def encode(source, width, quality, scratch):
    """Make one resized AVIF in a temporary folder.
    The caller keeps it only if it should replace the current file."""
    staged = os.path.join(scratch, 'staged.avif')
    run(['ffmpeg', '-y', '-v', 'error', '-i', source,
         # Let ffmpeg choose an even height. Lanczos keeps text sharper than the default.
         '-vf', 'scale=%d:-2:flags=lanczos+accurate_rnd' % width,
         '-c:v', 'libaom-av1', '-crf', str(quality_to_crf(quality)),
         '-cpu-used', '4', '-pix_fmt', 'yuv420p', '-still-picture', '1',
         '-f', 'avif', staged])
    return staged


def outputs_for(source, profile):
    """List the AVIF files for this image, from widest to narrowest.
    That lets us compare each size with the next wider one."""
    width = source_width(source)
    base = os.path.splitext(source)[0]
    cap = profile['cap']

    planned = [('%s.avif' % base, min(width, cap) if cap else width)]
    for rung in sorted(profile['variants'], reverse=True):
        if rung <= planned[-1][1] * (1 - MIN_GAP):
            planned.append(('%s-%d.avif' % (base, rung), rung))
    return width, planned


def sweep(planned):
    """Remove old resized files the current plan does not need anymore."""
    base = os.path.splitext(planned[0][0])[0]
    keep = {os.path.basename(path) for path, _ in planned}
    directory = os.path.dirname(base) or '.'

    stale = []
    for name in sorted(os.listdir(directory)):
        if re.fullmatch(re.escape(os.path.basename(base)) + r'-\d+\.avif', name) and name not in keep:
            os.remove(os.path.join(directory, name))
            stale.append(os.path.join(directory, name))
    return stale


def find_sources():
    for root, classify in ROOTS:
        for directory, _, names in os.walk(root):
            for name in sorted(names):
                stem, extension = os.path.splitext(name)
                # Do not treat a generated size as a source. Otherwise the next run loops over it.
                if stem.rsplit('-', 1)[-1].isdigit() and extension.lower() == '.avif':
                    continue
                if extension.lower() in SOURCE_EXTENSIONS and name not in SKIP:
                    yield os.path.join(directory, name), PROFILES[classify(stem)]


def needs_encode(source, source_pixels, target, target_width, force):
    # If the source is already AVIF, it is also the main output file.
    # Only remake it when its width no longer fits. Otherwise quality slowly drops.
    if os.path.abspath(source) == os.path.abspath(target):
        return source_pixels != target_width
    if force:
        return True
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

    written = skipped = dropped = pruned = 0
    # Keep the temporary file nearby so os.replace stays on one filesystem.
    scratch = tempfile.mkdtemp(dir='.')
    try:
        for source, profile in find_sources():
            pixels, planned = outputs_for(source, profile)

            for target in sweep(planned):
                print('%s  dropped, too close to the width above it' % target)
                dropped += 1

            for target, width in planned:
                if not needs_encode(source, pixels, target, width, args.force):
                    skipped += 1
                    continue
                os.replace(encode(source, width, profile['quality'], scratch), target)
                print('%s  %dw  %.0f kB' % (target, width, os.path.getsize(target) / 1024))
                written += 1

            # Keep a source when it is also the main AVIF output.
            same = os.path.abspath(source) == os.path.abspath(planned[0][0])
            if args.prune and not same and all(os.path.exists(t) for t, _ in planned):
                os.remove(source)
                pruned += 1
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print('wrote %d, up to date %d, dropped %d, pruned %d'
          % (written, skipped, dropped, pruned))
    if written and not args.prune:
        print('sources kept, pass --prune to drop them once you are happy')


if __name__ == '__main__':
    main()
