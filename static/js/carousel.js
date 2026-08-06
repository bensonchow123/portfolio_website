/*
 * Project-detail carousel
 *
 * The paging itself is CSS scroll div, so swipe, trackpad and the dot anchors
 * all work with this, and the template renders slide 01 as the initial state.
 * This script adds the ‹ › buttons and keeps the indicators in step while you scroll.
 */
(function () {
    var scroller = document.querySelector('[data-carousel]');
    if (!scroller) return;

    var prev = document.querySelector('[data-carousel-prev]');
    var next = document.querySelector('[data-carousel-next]');
    var dots = Array.prototype.slice.call(document.querySelectorAll('[data-carousel-dot]'));
    var count = document.querySelector('[data-carousel-count]');
    var total = dots.length;

    function pad(n) { return (n < 10 ? '0' : '') + n; }

    // Every slide is exactly one scroller-width wide (w-full shrink-0), so the
    // index is just how many widths we have scrolled.
    function current() {
        var index = Math.round(scroller.scrollLeft / (scroller.clientWidth || 1));
        if (index < 0) index = 0;
        if (total && index > total - 1) index = total - 1;
        return index;
    }

    // Paging wraps in both directions: › on the last slide returns to the
    // first. Neither button is ever a dead end, so neither is ever disabled.
    function step(delta) {
        if (!total) return;
        var index = (current() + delta + total) % total;
        scroller.scrollTo({ left: index * scroller.clientWidth, behavior: 'smooth' });
    }

    function sync() {
        var index = current();

        dots.forEach(function (dot, i) {
            if (i === index) dot.setAttribute('aria-current', 'true');
            else dot.removeAttribute('aria-current');
        });

        if (count && total) count.textContent = pad(index + 1) + ' / ' + pad(total);
    }

    if (prev && next) {
        prev.addEventListener('click', function () { step(-1); });
        next.addEventListener('click', function () { step(1); });
        // Shipped hidden so a no-JS visitor never sees dead controls.
        prev.hidden = false;
        next.hidden = false;

        // Clicking the left or right half of the image pages too, which is how every photo viewer behaves.
        // Only wired up alongside the buttons, so a no-JS visitor never gets an
        // area that looks clickable and isn't.
        scroller.style.cursor = 'pointer';
        scroller.addEventListener('click', function (event) {
            // Never swallow a click meant for an embedded video or a link.
            if (event.target.closest('a, button, iframe, video')) return;
            var box = scroller.getBoundingClientRect();
            step(event.clientX < box.left + box.width / 2 ? -1 : 1);
        });
    }

    scroller.addEventListener('scroll', sync, { passive: true });
    window.addEventListener('resize', sync);
    sync();
})();
