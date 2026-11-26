(() => {
    const params = new URLSearchParams(window.location.search);
    const query = (params.get("q") || "").trim();
    const input = document.getElementById("searchQuery");
    const results = document.getElementById("searchResults");
    const message = document.getElementById("searchMessage");
    if (!input || !results || !message) return;

    input.value = query;
    if (!query) {
        message.textContent = "Shkruaj një term për të kërkuar në faqet e KOD.";
        return;
    }

    const pages = [
        { title: "Kreu", url: "/", text: "Njohuri të hapura, teknologji dhe komuniteti digjital." },
        { title: "Rreth nesh", url: "/about/", text: "Misioni, parimet, qasja e hapur, privatësia dhe bashkëpunimi." },
        { title: "Kontakt", url: "/contact/", text: "Na kontakto për pyetje, sugjerime dhe bashkëpunim." },
        { title: "Statusi i shërbimeve", url: "/status/", text: "Statusi dhe monitorimi i shërbimeve të KOD." }
    ];

    const terms = query.toLocaleLowerCase("sq").split(/\s+/).filter(Boolean);
    const matches = pages.filter(page => {
        const haystack = `${page.title} ${page.text}`.toLocaleLowerCase("sq");
        return terms.some(term => haystack.includes(term));
    });

    results.replaceChildren();
    if (!matches.length) {
        message.textContent = `Nuk u gjetën rezultate për “${query}”.`;
        return;
    }

    message.textContent = `${matches.length} rezultat(e) për “${query}”.`;
    matches.forEach(page => {
        const article = document.createElement("article");
        article.className = "search-result";
        const heading = document.createElement("h2");
        const link = document.createElement("a");
        link.href = page.url;
        link.textContent = page.title;
        const description = document.createElement("p");
        description.textContent = page.text;
        heading.append(link);
        article.append(heading, description);
        results.append(article);
    });
})();