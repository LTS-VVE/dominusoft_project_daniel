(() => {
    const form = document.getElementById("contactForm");
    if (!form) return;

    const SERVICE_ID = form.dataset.service;
    const TEMPLATE_ID = form.dataset.template;
    const PUBLIC_KEY = form.dataset.key;

    const feedback = document.getElementById("formFeedback");
    const button = form.querySelector('button[type="submit"]');

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (!form.reportValidity()) return;

        if (!SERVICE_ID || !TEMPLATE_ID || !PUBLIC_KEY) {
            feedback.textContent = "Ndodhi një gabim. Ju lutemi provoni përsëri më vonë.";
            return;
        }

        if (typeof emailjs === "undefined") {
            feedback.textContent = "Shërbimi nuk është aktualisht i disponueshëm.";
            return;
        }

        button.disabled = true;
        feedback.textContent = "Mesazhi po dërgohet...";

        try {
            await emailjs.sendForm(
                SERVICE_ID,
                TEMPLATE_ID,
                form,
                { publicKey: PUBLIC_KEY }
            );

            feedback.textContent = "Mesazhi u dërgua me sukses. Faleminderit!";
            form.reset();

        } catch (err) {
            console.error("Contact form error:", err);
            feedback.textContent = "Dërgimi i mesazhit dështoi. Ju lutemi provoni përsëri.";

        } finally {
            button.disabled = false;
        }
    });
})();