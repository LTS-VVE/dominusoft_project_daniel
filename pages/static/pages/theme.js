/* KOD: theme switcher + Mistral-style motion (pixel field, marquee, card spotlight) */
(function () {
    var KEY = "kod-theme", ok = ["dark", "light", "contrast"];
    var root = document.documentElement;
    var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

    /* ---------- theme ---------- */
    function paint(t) {
        root.setAttribute("data-theme", t);
        root.setAttribute("data-bs-theme", t === "light" ? "light" : "dark");
        document.querySelectorAll("[data-set-theme]").forEach(function (b) {
            var on = b.getAttribute("data-set-theme") === t;
            b.classList.toggle("active", on);
            b.setAttribute("aria-pressed", on ? "true" : "false");
        });
    }
    function apply(t, animate) {
        if (ok.indexOf(t) < 0) t = "dark";
        if (!animate || reduce) { paint(t); return; }
        if (document.startViewTransition) {
            document.startViewTransition(function () { paint(t); });
        } else {
            root.classList.add("theme-anim");
            paint(t);
            setTimeout(function () { root.classList.remove("theme-anim"); }, 650);
        }
    }

    /* ---------- pixel sunset field ---------- */
    var PAL = [[225, 5, 0], [250, 80, 15], [255, 130, 5], [255, 175, 0], [255, 216, 0]];
    function pal(f) {
        f = Math.max(0, Math.min(1, f)) * (PAL.length - 1);
        var i = Math.floor(f), j = Math.min(i + 1, PAL.length - 1), k = f - i;
        return [PAL[i][0] + (PAL[j][0] - PAL[i][0]) * k | 0,
                PAL[i][1] + (PAL[j][1] - PAL[i][1]) * k | 0,
                PAL[i][2] + (PAL[j][2] - PAL[i][2]) * k | 0];
    }
    function pixelField(host, big) {
        var c = document.createElement("canvas");
        c.className = "fx-pixels";
        c.setAttribute("aria-hidden", "true");
        host.insertBefore(c, host.firstChild);
        var ctx = c.getContext("2d");
        var w = 0, h = 0, cell = 24, cols = 0, rows = 0, running = false, last = 0;

        function size() {
            w = host.clientWidth;
            cell = Math.min(28, Math.max(18, Math.round(w / 48)));
            h = cell * (big ? 5 : 4);
            c.width = w; c.height = h; c.style.height = h + "px";
            cols = Math.ceil(w / cell); rows = Math.round(h / cell);
        }
        function draw(t) {
            ctx.clearRect(0, 0, w, h);
            for (var i = 0; i < cols; i++) {
                var x = i / cols;
                var a1 = 0.5 + 0.5 * Math.sin(x * 6.2 + t * 0.00045);
                var a2 = 0.5 + 0.5 * Math.sin(x * 13.1 - t * 0.0007 + 1.7);
                var hh = Math.round((0.18 + 0.82 * (a1 * 0.65 + a2 * 0.35)) * rows * (0.55 + 0.45 * x));
                for (var r = 0; r < hh; r++) {
                    var f = r / Math.max(1, rows - 1);
                    var fl = 0.5 + 0.5 * Math.sin(i * 12.9898 + r * 78.233 + t * (0.0016 + ((i * 7 + r * 3) % 5) * 0.0004));
                    var a = (0.30 + 0.70 * fl) * (1 - (r / (rows + 2)) * 0.35);
                    if (r === hh - 1) a = Math.min(1, a + 0.25);
                    var col = pal(f);
                    ctx.fillStyle = "rgba(" + col[0] + "," + col[1] + "," + col[2] + "," + a.toFixed(3) + ")";
                    ctx.fillRect(i * cell, h - (r + 1) * cell, cell - 2, cell - 2);
                }
            }
        }
        function loop(ts) {
            if (!running) return;
            if (ts - last > 33) { last = ts; draw(ts); }
            requestAnimationFrame(loop);
        }
        size(); draw(0);
        if (reduce) return;
        if ("ResizeObserver" in window) new ResizeObserver(function () { size(); draw(last); }).observe(host);
        if ("IntersectionObserver" in window) {
            new IntersectionObserver(function (e) {
                var on = e[0].isIntersecting;
                if (on && !running) { running = true; requestAnimationFrame(loop); }
                if (!on) running = false;
            }).observe(host);
        } else { running = true; requestAnimationFrame(loop); }
    }

    /* ---------- cursor spotlight on cards ---------- */
    function spotlight() {
        document.addEventListener("pointermove", function (e) {
            var el = e.target.closest && e.target.closest(".card, .value-item");
            if (!el) return;
            var r = el.getBoundingClientRect();
            el.style.setProperty("--mx", (e.clientX - r.left) + "px");
            el.style.setProperty("--my", (e.clientY - r.top) + "px");
        }, { passive: true });
    }

    document.addEventListener("DOMContentLoaded", function () {
        apply(root.getAttribute("data-theme"), false);
        document.querySelectorAll("[data-set-theme]").forEach(function (b) {
            b.addEventListener("click", function () {
                var t = b.getAttribute("data-set-theme");
                try { localStorage.setItem(KEY, t); } catch (e) {}
                apply(t, true);
            });
        });
        document.querySelectorAll(".hero-cover").forEach(function (h) { pixelField(h, true); });
        document.querySelectorAll(".page-hero").forEach(function (h) { pixelField(h, false); });
        marquee();
        if (!reduce) spotlight();
    });
})();