const catalogSearchOpen = document.getElementById("catalog-search-open");
const catalogAdminModal = document.getElementById("catalog-admin-modal");
const catalogAdminClose = document.getElementById("catalog-admin-close");
const catalogSearchInput = document.getElementById("catalog-search-input");
const catalogSearchSubmit = document.getElementById("catalog-search-submit");
const catalogSearchResults = document.getElementById("catalog-search-results");
const adminBackdropShared = document.getElementById("admin-backdrop");
let catalogSearchDebounceId = null;

function getAdminHeaders(extraHeaders = {}) {
    const token = window.sessionStorage.getItem("zamzam_session_token") || "";
    return token ? { ...extraHeaders, Authorization: `Bearer ${token}` } : { ...extraHeaders };
}

function openCatalogAdminModal() {
    if (!catalogAdminModal || !adminBackdropShared) {
        return;
    }

    adminBackdropShared.classList.add("is-open");
    catalogAdminModal.classList.add("is-open");
    catalogAdminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

function closeCatalogAdminModal() {
    if (!catalogAdminModal || !adminBackdropShared) {
        return;
    }

    catalogAdminModal.classList.remove("is-open");
    catalogAdminModal.setAttribute("aria-hidden", "true");
    if (!document.getElementById("admin-modal")?.classList.contains("is-open")) {
        adminBackdropShared.classList.remove("is-open");
        document.body.classList.remove("admin-open");
    }
}

window.zamzamCatalogAdmin = {
    close: closeCatalogAdminModal,
};

function renderCatalogSearchResults(items) {
    if (!catalogSearchResults) {
        return;
    }

    if (!items.length) {
        catalogSearchResults.innerHTML = '<div class="account-order-empty">Ничего не найдено.</div>';
        return;
    }

    catalogSearchResults.innerHTML = items
        .map(
            (item) => `
                <div class="order-line">
                    <div>
                        <strong>${item.iiko_title || item.title}</strong>
                        <small>${window.zamzamApp?.formatPrice ? window.zamzamApp.formatPrice(item.price) : item.price}</small>
                    </div>
                    <button class="topbar-action topbar-action-button" type="button" data-catalog-item-id="${item.id}">
                        ${item.is_published ? "Редактировать" : "Добавить"}
                    </button>
                </div>
            `,
        )
        .join("");
}

async function searchCatalogItems() {
    if (!catalogSearchInput || !catalogSearchSubmit) {
        return;
    }

    const query = catalogSearchInput.value.trim();
    catalogSearchSubmit.disabled = true;

    try {
        const response = await fetch(`/api/redactor/menu-items/catalog/search?q=${encodeURIComponent(query)}&limit=30&offset=0`, {
            headers: getAdminHeaders(),
        });
        if (!response.ok) {
            const errorBody = await response.json().catch(() => ({}));
            throw new Error(errorBody?.detail || "Не удалось выполнить поиск.");
        }

        const payload = await response.json();
        renderCatalogSearchResults(payload.items || []);
    } catch (error) {
        if (catalogSearchResults) {
            catalogSearchResults.innerHTML = `<div class="account-order-empty">${error.message || "Не удалось выполнить поиск."}</div>`;
        }
    } finally {
        catalogSearchSubmit.disabled = false;
    }
}

async function openItemFromSearch(itemId) {
    const response = await fetch(`/api/redactor/menu-items/${itemId}`, {
        headers: getAdminHeaders(),
    });
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody?.detail || "Не удалось загрузить товар.");
    }

    const item = await response.json();
    closeCatalogAdminModal();
    window.zamzamApp?.openAdminModalWithItem?.(item);
}

catalogSearchOpen?.addEventListener("click", () => {
    if (!document.body.classList.contains("admin-mode")) {
        document.getElementById("admin-toggle")?.click();
    }
    openCatalogAdminModal();
    searchCatalogItems();
});

catalogAdminClose?.addEventListener("click", closeCatalogAdminModal);
catalogSearchSubmit?.addEventListener("click", searchCatalogItems);
catalogSearchInput?.addEventListener("input", () => {
    if (catalogSearchDebounceId) {
        window.clearTimeout(catalogSearchDebounceId);
    }

    catalogSearchDebounceId = window.setTimeout(() => {
        searchCatalogItems();
    }, 250);
});
catalogSearchInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        if (catalogSearchDebounceId) {
            window.clearTimeout(catalogSearchDebounceId);
            catalogSearchDebounceId = null;
        }
        searchCatalogItems();
    }
});

catalogSearchResults?.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-catalog-item-id]");
    if (!button) {
        return;
    }

    button.disabled = true;
    try {
        await openItemFromSearch(button.dataset.catalogItemId);
    } catch (error) {
        window.alert(error.message || "Не удалось открыть товар.");
    } finally {
        button.disabled = false;
    }
});

adminBackdropShared?.addEventListener("click", closeCatalogAdminModal);
