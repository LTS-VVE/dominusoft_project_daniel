(() => {
    "use strict";

    const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    // PAGE LOADER
    const loader = document.getElementById("page-loader");

    if (loader) {
        function hideLoader() {
            loader.classList.add("is-hidden");

            setTimeout(() => {
                loader.remove();
            }, 500);
        }

        if (document.readyState === "complete") {
            hideLoader();
        } else {
            window.addEventListener("load", hideLoader, { once: true });
        }
    }

    // TYPEWRITER
    const target = document.getElementById("typewriter");

    if (target) {
        if (reducedMotion) {
            target.textContent = "të hapura.";
        } else {
            const words = [
                "për të mësuar.",
                "për të ndarë ide.",
                "për të krijuar.",
                "për të eksploruar.",
                "pa kufij."
            ];

            let wordIndex = 0;
            let charIndex = 0;
            let deleting = false;

            function type() {
                const word = words[wordIndex];

                target.textContent = word.slice(0, charIndex);

                if (!deleting && charIndex < word.length) {
                    charIndex++;
                    setTimeout(type, 85);
                } else if (!deleting) {
                    deleting = true;
                    setTimeout(type, 1500);
                } else if (charIndex > 0) {
                    charIndex--;
                    setTimeout(type, 40);
                } else {
                    deleting = false;
                    wordIndex = (wordIndex + 1) % words.length;
                    setTimeout(type, 350);
                }
            }

            type();
        }
    }

    // SCROLL REVEAL
    const revealElements = document.querySelectorAll(".reveal");

    if (reducedMotion || !("IntersectionObserver" in window)) {
        revealElements.forEach(element => {
            element.classList.add("visible");
        });
        return;
    }

    const revealObserver = new IntersectionObserver(
        (entries, observer) => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;

                entry.target.classList.add("visible");
                observer.unobserve(entry.target);
            });
        },
        {
            threshold: 0.12,
            rootMargin: "0px 0px -35px 0px"
        }
    );

    revealElements.forEach(element => {
        revealObserver.observe(element);
    });

})();