/* ==========================================================================
   app.js — Application-level JavaScript
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function () {
    // ── HTMX error handler ────────────────────────────────────────────────
    // When an HTMX request fails, display a user-friendly error message
    // instead of silently failing or showing a blank swap.

    document.body.addEventListener("htmx:responseError", function (event) {
        var xhr = event.detail.xhr;
        var status = xhr.status;
        var message;

        if (status === 401 || status === 403) {
            message = "Sessao expirada. Por favor, faca login novamente.";
            window.location.href =
                document.querySelector('meta[name="login-url"]')?.content ||
                "/accounts/login/?next=" + encodeURIComponent(window.location.pathname);
            return;
        }

        if (status === 404) {
            message = "Recurso nao encontrado.";
        } else if (status === 500) {
            message = "Erro interno do servidor. Tente novamente mais tarde.";
        } else if (status === 0) {
            message = "Erro de ligacao. Verifique a sua conexao.";
        } else {
            message = "Erro inesperado (" + status + ").";
        }

        // Show error as a dismissible banner at the top of the page
        showBanner(message, "error");
    });

    document.body.addEventListener("htmx:sendError", function () {
        showBanner("Erro de ligacao. Verifique a sua conexao e tente novamente.", "error");
    });
});

/**
 * Show a dismissible banner at the top of the main content area.
 * @param {string} text  - Message to display
 * @param {string} level - "error" | "warning" | "success" | "info"
 */
function showBanner(text, level) {
    var colorMap = {
        error: "bg-red-50 border-red-200 text-red-800",
        warning: "bg-yellow-50 border-yellow-200 text-yellow-800",
        success: "bg-green-50 border-green-200 text-green-800",
        info: "bg-blue-50 border-blue-200 text-blue-800",
    };

    var classes = colorMap[level] || colorMap.info;

    var banner = document.createElement("div");
    banner.className =
        "rounded-md p-3 flex items-center justify-between border " + classes;
    banner.innerHTML =
        '<span class="text-sm">' +
        text +
        '</span><button type="button" class="text-current opacity-50 hover:opacity-100 ml-3" onclick="this.parentElement.remove()">&times;</button>';

    var main = document.querySelector("main") || document.body;
    main.insertBefore(banner, main.firstChild);

    // Auto-dismiss after 8 seconds
    setTimeout(function () {
        if (banner.parentElement) {
            banner.remove();
        }
    }, 8000);
}