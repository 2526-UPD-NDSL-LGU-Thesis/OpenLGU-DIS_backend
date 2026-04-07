async function loadPage(page) {
    const app = document.getElementById("container");
    try {
        const res = await fetch(`/${page}`);
        const html = await res.text();
        app.innerHTML = html;

        runPageInit(page)
    } catch (err) {
        app.innerHTML = "<p>Error loading page.</p>";
    }
}

async function runPageInit(page) {
    switch (page) {
        case "profile":
            const scanModule = await import("./profile.js");
            scanModule.initProfilePage();
            break;

        case "register":
            const regModule = await import("./register.js");
            regModule.initRegisterPage();
            break;

        case "admin":
            const labsModule = await import("./admin.js");
            labsModule.initLabsPage();
            break;

        case "claim":
            const claimModule = await import("./claim.js");
            claimModule.initClaimPage();
            break;

        default:
            break;
    }
}

// Default route = scan
function getCurrentPage() {
    return location.hash.replace("#", "") || "profile";
}

window.addEventListener("hashchange", () => {
    loadPage(getCurrentPage());
});

// Initial load
document.addEventListener("DOMContentLoaded", () => {
    loadPage(getCurrentPage());
});
