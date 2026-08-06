/*
 * Terminal typing effect.
 *
 * Unlike the typed.js setup this replaces, the text is NOT held in a JS string.
 * It is rendered by the server as ordinary markup inside [data-type]
 */
(function () {
    var CHARS_PER_SECOND = 9;

    var root = document.querySelector('[data-type]');
    if (!root) return;

    var caret = document.querySelector('[data-caret]');
    var steps = [];

    // Manual walk rather than a TreeWalker: we need to push a [data-instant]
    // element and then NOT descend into it, which a TreeWalker filter can't
    // express (FILTER_REJECT would skip the element itself too).
    function collect(node) {
        for (var child = node.firstChild; child; child = child.nextSibling) {
            if (child.nodeType === Node.TEXT_NODE) {
                if (!child.nodeValue) continue;
                // Only the trimmed content is charged for. A text node here is
                // usually "\n<indent>fastfetch\n<indent>", and typing that
                // indentation would be seconds of nothing happening.
                var text = child.nodeValue;
                var lead = text.match(/^\s*/)[0];
                var body = text.trim();
                steps.push({ node: child, text: text, lead: lead, body: body, cost: body.length });
            } else if (child.nodeType === Node.ELEMENT_NODE) {
                if (child.hasAttribute('data-instant')) {
                    // data-delay holds back the block for N ms after the
                    // preceding text finishes, so the command looks like it is
                    // actually running before its output lands. Expressed in
                    // "characters" so it rides the same timeline as the typing.
                    var delayMs = parseInt(child.getAttribute('data-delay'), 10) || 0;
                    steps.push({ el: child, cost: delayMs / 1000 * CHARS_PER_SECOND });
                } else if (child.tagName === 'BR') {
                    steps.push({ br: child, cost: 0 });
                } else {
                    collect(child);
                }
            }
        }
    }
    collect(root);

    // Cumulative start offset per step, so the frame loop advances a cursor
    // rather than rescanning the whole list for every character.
    var total = 0;
    steps.forEach(function (step) {
        step.start = total;
        total += step.cost;
    });
    if (!total) return;

    function show(step) {
        if (step.br) step.br.style.display = '';
        else if (step.el) step.el.style.display = '';
        else step.node.nodeValue = step.text;
    }

    function hide(step) {
        // display:none, NOT visibility:hidden, as an invisible <br> still breaks
        // the line, which dropped the caret onto row 2 the moment typing began
        // instead of letting it trail the last typed character.
        if (step.br) step.br.style.display = 'none';
        else if (step.el) step.el.style.display = 'none';
        // Keep the leading whitespace: it collapses to the single space after
        // the prompt, so the caret starts exactly where a shell's would.
        else step.node.nodeValue = step.lead;
    }

    // Respect the OS setting: no animation, just show the finished terminal.
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        if (caret) caret.removeAttribute('hidden');
        return;
    }

    steps.forEach(hide);
    if (caret) caret.removeAttribute('hidden');

    var cursor = 0;
    var startedAt = null;

    function frame(timestamp) {
        if (startedAt === null) startedAt = timestamp;

        var target = Math.min(total, (timestamp - startedAt) / 1000 * CHARS_PER_SECOND);

        // Fully-revealed steps, including every zero-cost one whose turn has come.
        while (cursor < steps.length && steps[cursor].start + steps[cursor].cost <= target) {
            show(steps[cursor]);
            cursor++;
        }

        // Partially reveal the step straddling the current position. Trailing
        // whitespace is withheld until the step completes so the caret, which
        // follows this node, sits against the last typed character.
        // (An element step with a cost is a pure delay.)
        if (cursor < steps.length && steps[cursor].cost && steps[cursor].node) {
            var shown = Math.max(0, Math.floor(target - steps[cursor].start));
            steps[cursor].node.nodeValue = steps[cursor].lead + steps[cursor].body.slice(0, shown);
        }

        if (cursor < steps.length) requestAnimationFrame(frame);
    }

    requestAnimationFrame(frame);

    // If the page is hidden mid animation, make sure the text still ends up visible.
    window.addEventListener('pagehide', function () {
        for (var i = cursor; i < steps.length; i++) show(steps[i]);
    });
})();
