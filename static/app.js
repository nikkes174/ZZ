const cart = new Map();
const MIN_CHECKOUT_AMOUNT = 1000;
const SESSION_STORAGE_KEY = "zamzam_session_token";

const formatPrice = (value) => `${value.toLocaleString("ru-RU")} руб.`;

function getAdminHeaders(extraHeaders = {}) {
    const token = window.sessionStorage.getItem(SESSION_STORAGE_KEY) || "";
    return token ? { ...extraHeaders, Authorization: `Bearer ${token}` } : { ...extraHeaders };
}

const orderItems = document.getElementById("order-items");
const totalPrice = document.getElementById("total-price");
const itemsCount = document.getElementById("items-count");
const cutleryCount = document.getElementById("cutlery-count");
const cutlerySummaryItem = document.getElementById("cutlery-summary-item");
const cutleryDecrease = document.getElementById("cutlery-decrease");
const cutleryIncrease = document.getElementById("cutlery-increase");
const floatingCount = document.getElementById("floating-count");
const cartCheckoutNote = document.getElementById("cart-checkout-note");
const filtersContainer = document.getElementById("filters");
const menuGrid = document.getElementById("menu-grid");
const menuSection = document.getElementById("menu");
const cartDrawer = document.getElementById("order-panel");
const cartBackdrop = document.getElementById("cart-backdrop");
const checkoutBackdrop = document.getElementById("checkout-backdrop");
const footerMapBackdrop = document.getElementById("footer-map-backdrop");
const cartToggle = document.getElementById("cart-toggle");
const cartOpenInline = document.getElementById("cart-open-inline");
const cartOpenTopbar = document.getElementById("cart-open-topbar");
const cartOpenHero = document.getElementById("cart-open-hero");
const cartClose = document.getElementById("cart-close");
const checkoutButton = document.getElementById("checkout-button");
const checkoutModal = document.getElementById("checkout-modal");
const checkoutClose = document.getElementById("checkout-close");
const footerMapModal = document.getElementById("footer-map-modal");
const footerMapOpen = document.getElementById("footer-map-open");
const footerMapClose = document.getElementById("footer-map-close");
const checkoutForm = document.getElementById("checkout-form");
const checkoutTypePickup = document.getElementById("cart-checkout-type-pickup");
const checkoutTypeDelivery = document.getElementById("cart-checkout-type-delivery");
const checkoutPaymentCash = document.getElementById("checkout-payment-cash");
const checkoutPaymentCard = document.getElementById("checkout-payment-card");
const checkoutDeliveryFields = document.getElementById("checkout-delivery-fields");
const checkoutAddress = document.getElementById("checkout-address");
const checkoutEntrance = document.getElementById("checkout-entrance");
const checkoutComment = document.getElementById("checkout-comment");
const checkoutName = document.getElementById("checkout-name");
const checkoutPhone = document.getElementById("checkout-phone");
const checkoutSubmit = document.getElementById("checkout-submit");
const checkoutNote = document.getElementById("checkout-note");
const checkoutPreviewItems = document.getElementById("checkout-preview-items");
const checkoutPreviewCutlery = document.getElementById("checkout-preview-cutlery");
const checkoutPreviewTotal = document.getElementById("checkout-preview-total");
const floatingTools = document.querySelector(".floating-tools");
const adminToggle = document.getElementById("admin-toggle");
const adminModal = document.getElementById("admin-modal");
const adminModalTitle = document.getElementById("admin-modal-title");
const adminBackdrop = document.getElementById("admin-backdrop");
const adminClose = document.getElementById("admin-close");
const adminForm = document.getElementById("admin-form");
const adminItemId = document.getElementById("admin-item-id");
const adminItemVersion = document.getElementById("admin-item-version");
const adminTitle = document.getElementById("admin-title");
const adminDescription = document.getElementById("admin-description");
const adminPrice = document.getElementById("admin-price");
const adminCategory = document.getElementById("admin-category");
const adminImage = document.getElementById("admin-image");
const adminSave = document.getElementById("admin-save");
const heroSection = document.getElementById("hero");
const heroAdminModal = document.getElementById("hero-admin-modal");
const heroAdminClose = document.getElementById("hero-admin-close");
const heroAdminForm = document.getElementById("hero-admin-form");
const heroAdminKicker = document.getElementById("hero-admin-kicker");
const heroAdminTitle = document.getElementById("hero-admin-title");
const heroAdminAddress = document.getElementById("hero-admin-address");
const heroAdminSubtitlePrimary = document.getElementById("hero-admin-subtitle-primary");
const heroAdminSubtitleSecondary = document.getElementById("hero-admin-subtitle-secondary");
const heroAdminSave = document.getElementById("hero-admin-save");
const menuSectionHead = document.querySelector("#menu .section-head > div");
const deliverySectionHead = document.querySelector("#delivery .section-head > div");
const contactSectionHead = document.querySelector("#contact .contact-copy");
const menuSectionAdminModal = document.getElementById("menu-section-admin-modal");
const menuSectionAdminModalTitle = document.getElementById("menu-section-admin-modal-title");
const menuSectionAdminClose = document.getElementById("menu-section-admin-close");
const menuSectionAdminForm = document.getElementById("menu-section-admin-form");
const menuSectionAdminKicker = document.getElementById("menu-section-admin-kicker");
const menuSectionAdminTitle = document.getElementById("menu-section-admin-title");
const menuSectionAdminSave = document.getElementById("menu-section-admin-save");
const menuCategoriesOpen = document.getElementById("menu-categories-open");
const menuCategoriesAdminModal = document.getElementById("menu-categories-admin-modal");
const menuCategoriesAdminClose = document.getElementById("menu-categories-admin-close");
const menuCategoriesAdminForm = document.getElementById("menu-categories-admin-form");
const menuCategoriesAdminList = document.getElementById("menu-categories-admin-list");
const menuCategoriesAdminAdd = document.getElementById("menu-categories-admin-add");
const menuCategoriesAdminSave = document.getElementById("menu-categories-admin-save");

let lastScrollY = window.scrollY;
let activeAdminCard = null;
let activeFilter = filtersContainer?.querySelector(".filter-chip.active")?.dataset.filter || "all";
let adminMode = "edit";
let heroEditControlsBound = false;
let activeSectionEditor = null;
let cutleryItemsCount = 0;
let checkoutType = "pickup";
let checkoutPayment = "cash";
let isDelivery = false;
let cartToastTimeoutId = null;
let revealObserver = null;

if ("scrollRestoration" in window.history) {
    window.history.scrollRestoration = "manual";
}

const cartToast = (() => {
    const node = document.createElement("div");
    node.className = "cart-toast";
    node.setAttribute("aria-live", "polite");
    document.body.appendChild(node);
    return node;
})();

function ensurePhonePrefixValue(input) {
    if (!input) {
        return "";
    }

    const digits = input.value.replace(/\D/g, "");
    let normalized = digits;

    if (!normalized) {
        normalized = "7";
    } else if (normalized[0] === "8") {
        normalized = `7${normalized.slice(1)}`;
    } else if (normalized[0] !== "7") {
        normalized = `7${normalized}`;
    }

    input.value = `+${normalized}`;
    return input.value;
}

function bindPhonePrefix(input) {
    if (!input) {
        return;
    }

    ensurePhonePrefixValue(input);

    input.addEventListener("focus", () => {
        ensurePhonePrefixValue(input);
    });

    input.addEventListener("input", () => {
        const moveCaretToEnd = input.selectionStart === input.value.length;
        ensurePhonePrefixValue(input);
        if (moveCaretToEnd) {
            input.setSelectionRange(input.value.length, input.value.length);
        }
    });

    input.addEventListener("blur", () => {
        ensurePhonePrefixValue(input);
    });
}

window.zamzamEnsurePhonePrefix = ensurePhonePrefixValue;

function bindClick(element, handler) {
    if (element) {
        element.addEventListener("click", handler);
    }
    if (cartCheckoutNote) {
        cartCheckoutNote.textContent = isDelivery
            ? "Для доставки минимальный заказ 1000 ₽."
            : "Самовывоз доступен без минимальной суммы.";
    }
    if (cartCheckoutNote) {
        cartCheckoutNote.textContent = isDelivery
            ? "Для доставки минимальный заказ 1000 ₽."
            : "Самовывоз доступен без минимальной суммы.";
    }
}

function getCards() {
    return Array.from(document.querySelectorAll(".dish-card"));
}

function bindClick(element, handler) {
    if (element) {
        element.addEventListener("click", handler);
    }
}

function syncCartCheckoutNote() {
    if (cartCheckoutNote) {
        cartCheckoutNote.textContent =
            checkoutType === "delivery"
                ? "Для доставки минимальный заказ 1000 ₽."
                : "Самовывоз доступен без минимальной суммы.";
    }
}

function getCartEntries() {
    return [...cart.values()];
}

function getCartTotals() {
    const entries = getCartEntries();
    return {
        entries,
        totalItems: entries.reduce((sum, item) => sum + item.quantity, 0),
        totalPriceValue: entries.reduce((sum, item) => sum + item.price * item.quantity, 0),
    };
}

function openCart() {
    if (!cartDrawer || !cartBackdrop) {
        return;
    }

    cartDrawer.classList.add("is-open");
    cartBackdrop.classList.add("is-open");
    document.body.classList.add("cart-open");
}

function closeCart() {
    cartDrawer?.classList.remove("is-open");
    cartBackdrop?.classList.remove("is-open");
    document.body.classList.remove("cart-open");
}

function showCartToast(message) {
    cartToast.textContent = message;
    cartToast.classList.add("is-visible");

    if (cartToastTimeoutId) {
        window.clearTimeout(cartToastTimeoutId);
    }

    cartToastTimeoutId = window.setTimeout(() => {
        cartToast.classList.remove("is-visible");
    }, 1800);
}

window.showZamzamToast = showCartToast;

function ensureRevealObserver() {
    if (revealObserver || !("IntersectionObserver" in window)) {
        return;
    }

    revealObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                entry.target.classList.add("is-visible");
                revealObserver.unobserve(entry.target);
            });
        },
        {
            threshold: 0.12,
            rootMargin: "0px 0px -8% 0px",
        },
    );
}

function registerRevealElement(element, index = 0) {
    if (!element || element.classList.contains("is-hidden")) {
        return;
    }

    if (!("IntersectionObserver" in window)) {
        element.classList.add("is-visible");
        return;
    }

    ensureRevealObserver();
    element.classList.add("reveal-on-scroll");
    element.style.setProperty("--reveal-delay", `${Math.min(index, 8) * 70}ms`);
    revealObserver?.observe(element);
}

function initRevealAnimations() {
    const groups = [
        { selector: ".hero-inner > *", stagger: 90 },
        { selector: ".section-head", stagger: 0 },
        { selector: ".account-summary-card", stagger: 80 },
        { selector: ".account-orders", stagger: 120 },
        { selector: ".dish-card", stagger: 70 },
        { selector: ".step-card", stagger: 90 },
        { selector: ".review-card", stagger: 90 },
        { selector: ".contact-copy", stagger: 0 },
        { selector: ".contact-card", stagger: 120 },
        { selector: ".site-footer-inner > *", stagger: 100 },
    ];

    groups.forEach((group) => {
        document.querySelectorAll(group.selector).forEach((element, index) => {
            registerRevealElement(element, Math.round((index * group.stagger) / 70));
        });
    });
}

function syncCheckoutPreview() {
    const { totalItems, totalPriceValue } = getCartTotals();

    if (checkoutPreviewItems) {
        checkoutPreviewItems.textContent = `${totalItems}`;
    }
    if (checkoutPreviewCutlery) {
        checkoutPreviewCutlery.textContent = `${cutleryItemsCount}`;
    }
    if (checkoutPreviewTotal) {
        checkoutPreviewTotal.textContent = formatPrice(totalPriceValue);
    }
}

function syncCheckoutType() {
    isDelivery = checkoutType === "delivery";
    if (!isDelivery) {
        checkoutPayment = "card";
    }

    checkoutTypePickup?.classList.toggle("is-active", !isDelivery);
    checkoutTypeDelivery?.classList.toggle("is-active", isDelivery);
    checkoutDeliveryFields?.classList.toggle("is-hidden", !isDelivery);

    if (checkoutAddress) {
        checkoutAddress.required = isDelivery;
    }

    if (checkoutNote) {
        checkoutNote.textContent = isDelivery
            ? "Доставка: заполните адрес и детали для курьера, чтобы оператор подтвердил заказ без уточнений."
            : "Самовывоз: заказ будет готов к выдаче после подтверждения оператором.";
    }

    if (checkoutPaymentCash) {
        checkoutPaymentCash.disabled = !isDelivery;
        checkoutPaymentCash.classList.toggle("is-disabled", !isDelivery);
        checkoutPaymentCash.setAttribute("aria-disabled", String(!isDelivery));
    }
}

function syncCheckoutPayment() {
    if (checkoutType !== "delivery") {
        checkoutPayment = "card";
    }
    checkoutPaymentCash?.classList.toggle("is-active", checkoutPayment === "cash");
    checkoutPaymentCard?.classList.toggle("is-active", checkoutPayment === "card");
}

function openCheckoutModal() {
    if (!checkoutModal || !checkoutBackdrop || !checkoutForm) {
        return;
    }

    closeCart();
    syncCheckoutPreview();
    syncCheckoutType();
    syncCheckoutPayment();
    checkoutBackdrop.classList.add("is-open");
    checkoutModal.classList.add("is-open");
    checkoutModal.setAttribute("aria-hidden", "false");
}

function closeCheckoutModal() {
    if (!checkoutModal || !checkoutBackdrop) {
        return;
    }

    checkoutBackdrop.classList.remove("is-open");
    checkoutModal.classList.remove("is-open");
    checkoutModal.setAttribute("aria-hidden", "true");
}

function openFooterMapModal() {
    if (!footerMapModal || !footerMapBackdrop) {
        return;
    }

    footerMapBackdrop.classList.add("is-open");
    footerMapModal.classList.add("is-open");
    footerMapModal.setAttribute("aria-hidden", "false");
}

function closeFooterMapModal() {
    if (!footerMapModal || !footerMapBackdrop) {
        return;
    }

    footerMapBackdrop.classList.remove("is-open");
    footerMapModal.classList.remove("is-open");
    footerMapModal.setAttribute("aria-hidden", "true");
}

function updateFloatingToolsVisibility() {
    if (!floatingTools) {
        return;
    }

    const hasCartItems = cart.size > 0;
    const hasVisibleAccountTrigger = document.getElementById("account-floating-trigger")?.classList.contains("is-hidden") === false;
    const menuTriggerY = menuSection ? Math.max(0, menuSection.offsetTop - 140) : 0;
    const shouldShow = hasCartItems || hasVisibleAccountTrigger || window.scrollY >= menuTriggerY;

    floatingTools.classList.toggle("is-hidden", !shouldShow);
}

function toStaticUrl(imagePath) {
    if (!imagePath) {
        return "";
    }

    const normalizedPath = imagePath.startsWith("/") ? imagePath.slice(1) : imagePath;
    return `/static/${normalizedPath}`;
}

function applyFilter(selected) {
    activeFilter = selected;

    if (filtersContainer) {
        filtersContainer.querySelectorAll(".filter-chip").forEach((chip) => {
            chip.classList.toggle("active", chip.dataset.filter === selected);
        });
    }

    getCards().forEach((card) => {
        const matchesFilter = selected === "all" || card.dataset.category === selected;
        const isActive = card.dataset.itemIsActive !== "false";
        card.classList.toggle("is-hidden", !(matchesFilter && isActive));
    });
}

function ensureFilterChip(category) {
    if (!filtersContainer || !category || category === "all") {
        return;
    }

    const existingChip = filtersContainer.querySelector(`[data-filter="${category}"]`);
    if (existingChip) {
        return;
    }

    const chip = document.createElement("button");
    chip.className = "filter-chip";
    chip.type = "button";
    chip.dataset.filter = category;
    chip.textContent = category;
    filtersContainer.appendChild(chip);
}

function getMenuCategoriesFromFilters() {
    if (!filtersContainer) {
        return [];
    }

    return Array.from(filtersContainer.querySelectorAll(".filter-chip"))
        .map((chip) => ({
            value: chip.dataset.filter || "",
            label: chip.textContent?.trim() || "",
        }))
        .filter((category) => category.value && category.value !== "all");
}

function renderFilterChips(categories) {
    if (!filtersContainer) {
        return;
    }

    const allChip = filtersContainer.querySelector('[data-filter="all"]');
    filtersContainer.innerHTML = "";
    if (allChip) {
        filtersContainer.appendChild(allChip);
    } else {
        const chip = document.createElement("button");
        chip.className = "filter-chip active";
        chip.type = "button";
        chip.dataset.filter = "all";
        chip.textContent = "Все блюда";
        filtersContainer.appendChild(chip);
    }

    categories.forEach((category) => {
        const chip = document.createElement("button");
        chip.className = "filter-chip";
        chip.type = "button";
        chip.dataset.filter = category.value;
        chip.textContent = category.label;
        filtersContainer.appendChild(chip);
    });

    const hasActiveFilter = activeFilter === "all" || categories.some((category) => category.value === activeFilter);
    applyFilter(hasActiveFilter ? activeFilter : "all");
}

function syncCategoryOptions(selectedCategory = "") {
    if (!adminCategory || !filtersContainer) {
        return;
    }

    const categories = getMenuCategoriesFromFilters();
    if (selectedCategory && !categories.some((category) => category.value === selectedCategory)) {
        categories.push({ value: selectedCategory, label: selectedCategory });
    }

    adminCategory.innerHTML = categories
        .map((category) => `<option value="${category.value}">${category.label}</option>`)
        .join("");

    if (selectedCategory && categories.some((category) => category.value === selectedCategory)) {
        adminCategory.value = selectedCategory;
    } else if (categories.length) {
        adminCategory.value = categories[0].value;
    }
}

function removeEmptyFilterChip(category) {
    if (!filtersContainer || !category || category === "all") {
        return;
    }

    const hasCardsInCategory = getCards().some((card) => card.dataset.category === category);
    if (hasCardsInCategory) {
        return;
    }

    filtersContainer.querySelector(`[data-filter="${category}"]`)?.remove();
    if (activeFilter === category) {
        applyFilter("all");
    }
}

function createDishCard(item) {
    const article = document.createElement("article");
    article.className = "dish-card";
    article.dataset.category = item.category;
    article.dataset.itemId = String(item.id);
    article.dataset.itemVersion = String(item.version);
    article.dataset.itemIsActive = item.is_active ? "true" : "false";
    article.dataset.imagePath = item.image_path || "";
    article.style.setProperty("--card-accent", item.accent);

    const imageMarkup = item.image_path
        ? `<img class="dish-image" src="${toStaticUrl(item.image_path)}" alt="${item.title}">`
        : `<img class="dish-image is-hidden" src="" alt="${item.title}">`;
    const plateHiddenClass = item.image_path ? " is-hidden" : "";

    article.innerHTML = `
        <div class="dish-visual">
            ${imageMarkup}
            <div class="dish-plate${plateHiddenClass}">
                <div class="dish-center"></div>
            </div>
        </div>
        <div class="dish-body">
            <div class="dish-admin-row">
                <h3 class="dish-title"></h3>
                <button class="dish-edit-button" type="button">Редактировать</button>
            </div>
            <p class="dish-description"></p>
        </div>
        <div class="dish-footer">
            <strong class="dish-price"></strong>
            <div class="dish-actions">
                <div class="qty-picker" data-qty-picker>
                    <button class="qty-button" type="button" data-qty-action="decrease">-</button>
                    <span class="qty-value" data-qty-value>1</span>
                    <button class="qty-button" type="button" data-qty-action="increase">+</button>
                </div>
                <button class="add-button" type="button" data-id="${item.id}" data-title="${item.title}" data-price="${item.price}">
                    Добавить
                </button>
            </div>
        </div>
    `;

    syncCardFromItem(article, item);
    registerRevealElement(article, 0);
    return article;
}

function syncCardFromItem(card, item) {
    if (!card || !item) {
        return;
    }

    const titleNode = card.querySelector(".dish-title");
    const descriptionNode = card.querySelector(".dish-description");
    const priceNode = card.querySelector(".dish-price");
    const addButton = card.querySelector(".add-button");
    const imageNode = card.querySelector(".dish-image");
    const plateNode = card.querySelector(".dish-plate");

    if (titleNode) {
        titleNode.textContent = item.title;
    }

    if (descriptionNode) {
        descriptionNode.textContent = item.description;
    }

    if (priceNode) {
        priceNode.textContent = formatPrice(item.price);
    }

    if (addButton) {
        addButton.dataset.id = String(item.id);
        addButton.dataset.title = item.title;
        addButton.dataset.price = String(item.price);
    }

    if (imageNode) {
        const imagePath = item.image_path || "";
        imageNode.src = imagePath ? toStaticUrl(imagePath) : "";
        imageNode.alt = item.title;
        imageNode.classList.toggle("is-hidden", !imagePath);
    }

    if (plateNode) {
        plateNode.classList.toggle("is-hidden", Boolean(item.image_path));
    }

    card.dataset.category = item.category;
    card.dataset.itemId = String(item.id);
    card.dataset.itemVersion = String(item.version);
    card.dataset.itemIsActive = item.is_active ? "true" : "false";
    card.dataset.imagePath = item.image_path || "";
    card.style.setProperty("--card-accent", item.accent);
    card.classList.toggle("is-hidden", !(item.is_active && (activeFilter === "all" || activeFilter === item.category)));
}

function populateAdminFormFromItem(item) {
    if (!item) {
        return;
    }

    adminModalTitle.textContent = "Редактирование карточки";
    adminItemId.value = item.id ? String(item.id) : "";
    adminItemVersion.value = item.version ? String(item.version) : "1";
    adminTitle.value = item.title || "";
    adminDescription.value = item.description || "";
    adminPrice.value = String(Number(item.price || 0));
    syncCategoryOptions(item.category || "");
}

function openAdminModalWithItem(item) {
    if (!adminModal || !adminBackdrop || !adminForm || !item) {
        return;
    }

    adminMode = "edit";
    activeAdminCard = menuGrid?.querySelector(`.dish-card[data-item-id="${item.id}"]`) || null;
    adminForm.reset();
    if (adminImage) {
        adminImage.value = "";
    }

    populateAdminFormFromItem(item);
    adminBackdrop.classList.add("is-open");
    adminModal.classList.add("is-open");
    adminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

function openAdminModal(mode, card = null) {
    if (!adminModal || !adminBackdrop || !adminForm) {
        return;
    }
    if (mode !== "edit" || !card) {
        return;
    }

    adminMode = "edit";
    activeAdminCard = card;
    adminForm.reset();
    if (adminImage) {
        adminImage.value = "";
    }

    const titleNode = card.querySelector(".dish-title");
    const descriptionNode = card.querySelector(".dish-description");
    const priceNode = card.querySelector(".dish-price");

    adminModalTitle.textContent = "Редактирование карточки";
    adminItemId.value = card.dataset.itemId || "";
    adminItemVersion.value = card.dataset.itemVersion || "1";
    adminTitle.value = titleNode?.textContent?.trim() || "";
    adminDescription.value = descriptionNode?.textContent?.trim() || "";
    adminPrice.value = String(parseInt(priceNode?.textContent || "0", 10) || 0);
    syncCategoryOptions(card.dataset.category || "");

    adminBackdrop.classList.add("is-open");
    adminModal.classList.add("is-open");
    adminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

function closeAdminModal() {
    if (!adminModal || !adminBackdrop || !adminForm) {
        return;
    }

    adminBackdrop.classList.remove("is-open");
    adminModal.classList.remove("is-open");
    adminModal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("admin-open");
    activeAdminCard = null;
    adminMode = "edit";
    adminForm.reset();
}

function setAdminMode(enabled) {
    document.body.classList.toggle("admin-mode", enabled);
    adminToggle?.classList.toggle("is-active", enabled);
}

function getHeroFields() {
    return {
        kicker: heroSection?.querySelector(".hero-kicker"),
        title: heroSection?.querySelector("h1"),
        address: heroSection?.querySelector(".hero-address"),
        subtitlePrimary: heroSection?.querySelector("h2 span:first-child"),
        subtitleSecondary: heroSection?.querySelector("h2 span:last-child"),
    };
}

function getHeroPayload() {
    const fields = getHeroFields();
    return {
        kicker: fields.kicker?.textContent?.trim() || "",
        title: fields.title?.textContent?.trim() || "",
        address: fields.address?.textContent?.trim() || "",
        subtitle_primary: fields.subtitlePrimary?.textContent?.trim() || "",
        subtitle_secondary: fields.subtitleSecondary?.textContent?.trim() || "",
    };
}

function syncHeroContent(content) {
    const fields = getHeroFields();
    if (fields.kicker) {
        fields.kicker.textContent = content.kicker || "";
    }
    if (fields.title) {
        fields.title.textContent = content.title || "";
    }
    if (fields.address) {
        fields.address.textContent = content.address || "";
    }
    if (fields.subtitlePrimary) {
        fields.subtitlePrimary.textContent = content.subtitle_primary || "";
    }
    if (fields.subtitleSecondary) {
        fields.subtitleSecondary.textContent = content.subtitle_secondary || "";
    }
}

function ensureHeroEditControls() {
    if (!heroSection || heroEditControlsBound) {
        return;
    }

    const fieldNodes = [
        heroSection.querySelector(".hero-kicker"),
        heroSection.querySelector("h1"),
        heroSection.querySelector(".hero-address"),
        heroSection.querySelector("h2"),
    ].filter(Boolean);

    fieldNodes.forEach((node) => {
        const wrapper = document.createElement("div");
        wrapper.className = "hero-copy-row";
        if (node.matches(".hero-address, h2")) {
            wrapper.classList.add("hero-copy-row-block");
        }

        node.parentNode.insertBefore(wrapper, node);
        wrapper.appendChild(node);

        const button = document.createElement("button");
        button.className = "hero-edit-button";
        button.type = "button";
        button.dataset.heroEdit = "true";
        button.setAttribute("aria-label", "Редактировать hero-секцию");
        button.innerHTML = "&#9998;";
        wrapper.appendChild(button);
    });

    heroEditControlsBound = true;
}

function openHeroAdminModal() {
    if (!heroAdminModal || !adminBackdrop || !heroAdminForm) {
        return;
    }

    const content = getHeroPayload();
    heroAdminKicker.value = content.kicker;
    heroAdminTitle.value = content.title;
    heroAdminAddress.value = content.address;
    heroAdminSubtitlePrimary.value = content.subtitle_primary;
    heroAdminSubtitleSecondary.value = content.subtitle_secondary;

    closeAdminModal();
    adminBackdrop.classList.add("is-open");
    heroAdminModal.classList.add("is-open");
    heroAdminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

function closeHeroAdminModal() {
    if (!heroAdminModal || !adminBackdrop || !heroAdminForm) {
        return;
    }

    adminBackdrop.classList.remove("is-open");
    heroAdminModal.classList.remove("is-open");
    heroAdminModal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("admin-open");
    heroAdminForm.reset();
}

async function loadHeroContent() {
    if (!heroSection) {
        return;
    }

    try {
        const response = await fetch("/api/redactor/menu-items/hero-content");
        if (!response.ok) {
            throw new Error("Не удалось загрузить hero-секцию.");
        }

        const content = await response.json();
        syncHeroContent(content);
    } catch (error) {
        window.console.error(error);
    }
}

function getSectionFields(sectionHead) {
    return {
        kicker: sectionHead?.querySelector(".section-kicker"),
        title: sectionHead?.querySelector("h2"),
    };
}

function getSectionPayload(sectionHead) {
    const fields = getSectionFields(sectionHead);
    return {
        kicker: fields.kicker?.textContent?.trim() || "",
        title: fields.title?.textContent?.trim() || "",
    };
}

function syncSectionContent(sectionHead, content) {
    const fields = getSectionFields(sectionHead);
    if (fields.kicker) {
        fields.kicker.textContent = content.kicker || "";
    }
    if (fields.title) {
        fields.title.textContent = content.title || "";
    }
}

function ensureSectionEditControls(sectionHead, datasetKey, ariaLabel) {
    if (!sectionHead || sectionHead.dataset.sectionEditBound === "true") {
        return;
    }

    const fieldNodes = [
        sectionHead.querySelector(".section-kicker"),
        sectionHead.querySelector("h2"),
    ].filter(Boolean);

    fieldNodes.forEach((node) => {
        const wrapper = document.createElement("div");
        wrapper.className = "section-copy-row";
        node.parentNode.insertBefore(wrapper, node);
        wrapper.appendChild(node);

        const button = document.createElement("button");
        button.className = "section-edit-button";
        button.type = "button";
        button.dataset[datasetKey] = "true";
        button.setAttribute("aria-label", ariaLabel);
        button.innerHTML = "&#9998;";
        wrapper.appendChild(button);
    });

    sectionHead.dataset.sectionEditBound = "true";
}

function openSectionAdminModal(config) {
    if (!menuSectionAdminModal || !adminBackdrop || !menuSectionAdminForm) {
        return;
    }

    const content = getSectionPayload(config.head);
    menuSectionAdminKicker.value = content.kicker;
    menuSectionAdminTitle.value = content.title;
    activeSectionEditor = config;
    if (menuSectionAdminModalTitle) {
        menuSectionAdminModalTitle.textContent = config.modalTitle;
    }

    closeAdminModal();
    closeHeroAdminModal();
    adminBackdrop.classList.add("is-open");
    menuSectionAdminModal.classList.add("is-open");
    menuSectionAdminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

function closeMenuSectionAdminModal() {
    if (!menuSectionAdminModal || !adminBackdrop || !menuSectionAdminForm) {
        return;
    }

    adminBackdrop.classList.remove("is-open");
    menuSectionAdminModal.classList.remove("is-open");
    menuSectionAdminModal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("admin-open");
    activeSectionEditor = null;
    menuSectionAdminForm.reset();
}

function createCategoryAdminRow(category = { value: "", label: "" }) {
    const row = document.createElement("div");
    row.className = "category-admin-row";
    row.innerHTML = `
        <input class="category-admin-input" type="text" maxlength="64" placeholder="slug, например grill" value="${category.value || ""}">
        <input class="category-admin-input" type="text" maxlength="64" placeholder="Название категории" value="${category.label || ""}">
        <button class="admin-close category-admin-remove" type="button" aria-label="Удалить категорию">x</button>
    `;
    return row;
}

function closeMenuCategoriesAdminModal() {
    if (!menuCategoriesAdminModal || !adminBackdrop || !menuCategoriesAdminForm) {
        return;
    }

    adminBackdrop.classList.remove("is-open");
    menuCategoriesAdminModal.classList.remove("is-open");
    menuCategoriesAdminModal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("admin-open");
    menuCategoriesAdminForm.reset();
    if (menuCategoriesAdminList) {
        menuCategoriesAdminList.innerHTML = "";
    }
}

async function openMenuCategoriesAdminModal() {
    if (!menuCategoriesAdminModal || !adminBackdrop || !menuCategoriesAdminList) {
        return;
    }

    closeAdminModal();
    closeHeroAdminModal();
    closeMenuSectionAdminModal();

    const response = await fetch("/api/redactor/menu-items/menu-categories");
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody?.detail || "Не удалось загрузить категории.");
    }

    const payload = await response.json();
    menuCategoriesAdminList.innerHTML = "";
    (payload.items || []).forEach((item) => {
        menuCategoriesAdminList.appendChild(createCategoryAdminRow(item));
    });

    adminBackdrop.classList.add("is-open");
    menuCategoriesAdminModal.classList.add("is-open");
    menuCategoriesAdminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

async function loadSectionContent(url, sectionHead) {
    if (!sectionHead) {
        return;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("Не удалось загрузить секцию.");
        }

        const content = await response.json();
        syncSectionContent(sectionHead, content);
    } catch (error) {
        window.console.error(error);
    }
}

function renderCart() {
    const { entries, totalItems, totalPriceValue } = getCartTotals();
    const hasEntries = entries.length > 0;
    const canCheckout = hasEntries;

    if (cutleryCount) {
        cutleryCount.textContent = `${cutleryItemsCount}`;
    }
    if (cutlerySummaryItem) {
        cutlerySummaryItem.style.display = hasEntries ? "" : "none";
    }
    if (checkoutButton) {
        checkoutButton.disabled = !canCheckout;
    }

    if (!hasEntries) {
        orderItems.innerHTML = `
            <div class="order-empty">
                <strong>Пока пусто</strong>
                <p>Добавьте блюда из каталога, и заказ появится здесь.</p>
            </div>
        `;
        totalPrice.textContent = "0 руб.";
        itemsCount.textContent = "0";
        floatingCount.textContent = "0";
        syncCheckoutPreview();
        updateFloatingToolsVisibility();
        return;
    }

    orderItems.innerHTML = entries
        .map(
            (item) => `
                <div class="order-line">
                    <div>
                        <strong>${item.title}</strong>
                        <small>${item.quantity} x ${formatPrice(item.price)}</small>
                    </div>
                    <div class="order-line-actions">
                        <strong>${formatPrice(item.price * item.quantity)}</strong>
                        <button class="order-remove-button" type="button" data-remove-id="${item.id}" aria-label="Удалить блюдо">x</button>
                    </div>
                </div>
            `,
        )
        .join("");

    totalPrice.textContent = formatPrice(totalPriceValue);
    itemsCount.textContent = `${totalItems}`;
    floatingCount.textContent = `${totalItems}`;
    syncCheckoutPreview();
    updateFloatingToolsVisibility();
}

function updateCutleryCount(nextValue) {
    cutleryItemsCount = Math.max(0, nextValue);
    renderCart();
}

async function uploadImage(itemId, version) {
    if (!adminImage?.files?.length) {
        return null;
    }

    const formData = new FormData();
    formData.append("version", String(version));
    formData.append("image", adminImage.files[0]);

    const response = await fetch(`/api/redactor/menu-items/${itemId}/image`, {
        method: "POST",
        headers: getAdminHeaders(),
        body: formData,
    });

    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody?.detail || "Не удалось загрузить фото.");
    }

    return response.json();
}

if (menuGrid) {
    menuGrid.addEventListener("click", (event) => {
        const target = event.target.closest("button");
        if (!target) {
            return;
        }

        if (target.matches(".add-button")) {
            const id = target.dataset.id;
            const title = target.dataset.title;
            const price = Number(target.dataset.price);
            const card = target.closest(".dish-card");
            const qtyValue = card?.querySelector("[data-qty-value]");
            const quantityToAdd = Math.max(1, Number(qtyValue?.textContent || "1"));

            if (!cart.has(id)) {
                cart.set(id, { id, title, price, quantity: 0 });
            }

            cart.get(id).quantity += quantityToAdd;
            renderCart();
            showCartToast(`Блюдо добавлено в корзину`);
            return;
        }

        if (target.matches("[data-qty-action]")) {
            const picker = target.closest("[data-qty-picker]");
            const valueNode = picker?.querySelector("[data-qty-value]");
            const current = Number(valueNode?.textContent || "1");
            const next =
                target.dataset.qtyAction === "increase"
                    ? current + 1
                    : Math.max(1, current - 1);

            if (valueNode) {
                valueNode.textContent = `${next}`;
            }
            return;
        }

        if (target.matches(".dish-edit-button")) {
            if (!document.body.classList.contains("admin-mode")) {
                return;
            }

            openAdminModal("edit", target.closest(".dish-card"));
        }
    });
}

if (orderItems) {
    orderItems.addEventListener("click", (event) => {
        const removeButton = event.target.closest("[data-remove-id]");
        if (!removeButton) {
            return;
        }

        const id = removeButton.dataset.removeId;
        if (!id || !cart.has(id)) {
            return;
        }

        cart.delete(id);
        renderCart();
    });
}

bindClick(cutleryDecrease, (event) => {
    event.preventDefault();
    event.stopPropagation();
    updateCutleryCount(cutleryItemsCount - 1);
});
bindClick(cutleryIncrease, (event) => {
    event.preventDefault();
    event.stopPropagation();
    updateCutleryCount(cutleryItemsCount + 1);
});

if (heroSection) {
    heroSection.addEventListener("click", (event) => {
        const target = event.target.closest("[data-hero-edit]");
        if (!target || !document.body.classList.contains("admin-mode")) {
            return;
        }

        openHeroAdminModal();
    });
}

if (menuSectionHead) {
    menuSectionHead.addEventListener("click", (event) => {
        const target = event.target.closest("[data-menu-section-edit]");
        if (!target || !document.body.classList.contains("admin-mode")) {
            return;
        }

        openSectionAdminModal({
            head: menuSectionHead,
            modalTitle: "Редактирование блока меню",
            saveUrl: "/api/redactor/menu-items/menu-section-content",
        });
    });
}

if (deliverySectionHead) {
    deliverySectionHead.addEventListener("click", (event) => {
        const target = event.target.closest("[data-delivery-section-edit]");
        if (!target || !document.body.classList.contains("admin-mode")) {
            return;
        }

        openSectionAdminModal({
            head: deliverySectionHead,
            modalTitle: "Редактирование блока доставки",
            saveUrl: "/api/redactor/menu-items/delivery-section-content",
        });
    });
}

if (contactSectionHead) {
    contactSectionHead.addEventListener("click", (event) => {
        const target = event.target.closest("[data-contact-section-edit]");
        if (!target || !document.body.classList.contains("admin-mode")) {
            return;
        }

        openSectionAdminModal({
            head: contactSectionHead,
            modalTitle: "Редактирование блока контактов",
            saveUrl: "/api/redactor/menu-items/contact-section-content",
        });
    });
}

if (filtersContainer) {
    filtersContainer.addEventListener("click", (event) => {
        const chip = event.target.closest(".filter-chip");
        if (!chip) {
            return;
        }

        applyFilter(chip.dataset.filter || "all");
    });
}

if (checkoutButton) {
    checkoutButton.addEventListener("click", () => {
        if (!cart.size) {
            window.alert("Сначала добавьте блюда в корзину.");
            return;
        }

        window.alert("Демо-экран готов. Следующим шагом можно подключить оформление, оплату и API заказа.");
    });
}

checkoutButton?.addEventListener(
    "click",
    (event) => {
        if (!cart.size) {
            return;
        }

        const sessionToken = window.sessionStorage.getItem(SESSION_STORAGE_KEY) || "";
        if (!sessionToken) {
            event.preventDefault();
            event.stopImmediatePropagation();
            closeCart();
            window.openZamzamAuthModal?.("login");
            return;
        }

        event.preventDefault();
        event.stopImmediatePropagation();
        openCheckoutModal();
    },
    true,
);

bindClick(cartToggle, openCart);
bindClick(cartOpenInline, openCart);
bindClick(cartClose, closeCart);
bindClick(cartBackdrop, closeCart);
bindClick(checkoutClose, closeCheckoutModal);
bindClick(checkoutBackdrop, closeCheckoutModal);
bindClick(footerMapOpen, openFooterMapModal);
bindClick(footerMapClose, closeFooterMapModal);
bindClick(footerMapBackdrop, closeFooterMapModal);
bindClick(checkoutTypePickup, () => {
    checkoutType = "pickup";
    syncCheckoutType();
    syncCartCheckoutNote();
    renderCart();
});
bindClick(checkoutTypeDelivery, () => {
    checkoutType = "delivery";
    syncCheckoutType();
    syncCartCheckoutNote();
    renderCart();
});
bindClick(checkoutPaymentCash, () => {
    if (checkoutType !== "delivery") {
        checkoutPayment = "card";
        syncCheckoutPayment();
        return;
    }
    checkoutPayment = "cash";
    syncCheckoutPayment();
});
bindClick(checkoutPaymentCard, () => {
    checkoutPayment = "card";
    syncCheckoutPayment();
});
bindClick(adminToggle, () => {
    setAdminMode(!document.body.classList.contains("admin-mode"));
});
bindClick(adminClose, closeAdminModal);
bindClick(heroAdminClose, closeHeroAdminModal);
bindClick(menuSectionAdminClose, closeMenuSectionAdminModal);
bindClick(menuCategoriesAdminClose, closeMenuCategoriesAdminModal);
bindClick(adminBackdrop, () => {
    closeAdminModal();
    closeHeroAdminModal();
    closeMenuSectionAdminModal();
    closeMenuCategoriesAdminModal();
    window.zamzamCatalogAdmin?.close?.();
});
bindClick(menuCategoriesOpen, async () => {
    try {
        await openMenuCategoriesAdminModal();
    } catch (error) {
        window.alert(error.message || "Не удалось открыть категории.");
    }
});
bindClick(menuCategoriesAdminAdd, () => {
    menuCategoriesAdminList?.appendChild(createCategoryAdminRow());
});

if (adminForm) {
    adminForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const basePayload = {
            title: adminTitle.value.trim(),
            description: adminDescription.value.trim(),
            category: adminCategory.value.trim(),
            is_published: true,
        };

        adminSave.disabled = true;

        try {
            if (!adminItemId.value) {
                throw new Error("Не выбрана карточка для редактирования.");
            }

            const previousCategory = activeAdminCard?.dataset.category || "";
            const updateResponse = await fetch(`/api/redactor/menu-items/${adminItemId.value}`, {
                method: "PATCH",
                headers: getAdminHeaders({
                    "Content-Type": "application/json",
                }),
                body: JSON.stringify({
                    ...basePayload,
                    version: Number(adminItemVersion.value || "1"),
                }),
            });

            if (!updateResponse.ok) {
                const errorBody = await updateResponse.json().catch(() => ({}));
                throw new Error(errorBody?.detail || "Не удалось сохранить изменения.");
            }

            let item = await updateResponse.json();

            if (adminImage?.files?.length) {
                item = (await uploadImage(item.id, item.version)) || item;
            }

            ensureFilterChip(item.category);
            if (activeAdminCard) {
                syncCardFromItem(activeAdminCard, item);
                removeEmptyFilterChip(previousCategory);
            } else {
                const card = createDishCard(item);
                menuGrid?.appendChild(card);
                activeAdminCard = card;
            }
            applyFilter(activeFilter);

            closeAdminModal();
        } catch (error) {
            window.alert(error.message || "Не удалось выполнить действие.");
        } finally {
            adminSave.disabled = false;
        }
    });
}

if (heroAdminForm) {
    heroAdminForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const payload = {
            kicker: heroAdminKicker.value.trim(),
            title: heroAdminTitle.value.trim(),
            address: heroAdminAddress.value.trim(),
            subtitle_primary: heroAdminSubtitlePrimary.value.trim(),
            subtitle_secondary: heroAdminSubtitleSecondary.value.trim(),
        };

        heroAdminSave.disabled = true;

        try {
            const response = await fetch("/api/redactor/menu-items/hero-content", {
                method: "PATCH",
                headers: getAdminHeaders({
                    "Content-Type": "application/json",
                }),
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                throw new Error(errorBody?.detail || "Не удалось сохранить hero-секцию.");
            }

            const content = await response.json();
            syncHeroContent(content);
            closeHeroAdminModal();
        } catch (error) {
            window.alert(error.message || "Не удалось сохранить hero-секцию.");
        } finally {
            heroAdminSave.disabled = false;
        }
    });
}

if (menuSectionAdminForm) {
    menuSectionAdminForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (!activeSectionEditor) {
            return;
        }

        const payload = {
            kicker: menuSectionAdminKicker.value.trim(),
            title: menuSectionAdminTitle.value.trim(),
        };

        menuSectionAdminSave.disabled = true;

        try {
            const response = await fetch(activeSectionEditor.saveUrl, {
                method: "PATCH",
                headers: getAdminHeaders({
                    "Content-Type": "application/json",
                }),
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                throw new Error(errorBody?.detail || "Не удалось сохранить блок меню.");
            }

            const content = await response.json();
            syncSectionContent(activeSectionEditor.head, content);
            closeMenuSectionAdminModal();
        } catch (error) {
            window.alert(error.message || "Не удалось сохранить секцию.");
        } finally {
            menuSectionAdminSave.disabled = false;
        }
    });
}

menuCategoriesAdminList?.addEventListener("click", (event) => {
    const button = event.target.closest(".category-admin-remove");
    if (!button) {
        return;
    }

    button.closest(".category-admin-row")?.remove();
});

if (menuCategoriesAdminForm) {
    menuCategoriesAdminForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const items = Array.from(menuCategoriesAdminList?.querySelectorAll(".category-admin-row") || [])
            .map((row) => {
                const inputs = row.querySelectorAll(".category-admin-input");
                return {
                    value: (inputs[0]?.value || "").trim().toLowerCase(),
                    label: (inputs[1]?.value || "").trim(),
                };
            })
            .filter((item) => item.value && item.label);

        menuCategoriesAdminSave.disabled = true;

        try {
            const response = await fetch("/api/redactor/menu-items/menu-categories", {
                method: "PATCH",
                headers: getAdminHeaders({
                    "Content-Type": "application/json",
                }),
                body: JSON.stringify({ items }),
            });

            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                throw new Error(errorBody?.detail || "Не удалось сохранить категории.");
            }

            const payload = await response.json();
            renderFilterChips(payload.items || []);
            syncCategoryOptions(adminCategory?.value || "");
            closeMenuCategoriesAdminModal();
        } catch (error) {
            window.alert(error.message || "Не удалось сохранить категории.");
        } finally {
            menuCategoriesAdminSave.disabled = false;
        }
    });
}

if (checkoutForm) {
    checkoutForm.addEventListener("submit", (event) => {
        if (window.zamzamAccountCheckoutEnabled) {
            return;
        }

        event.preventDefault();

        const { totalItems, totalPriceValue } = getCartTotals();
        if (!totalItems) {
            window.alert("Сначала добавьте блюда в корзину.");
            return;
        }

        const customerName = checkoutName?.value.trim() || "";
        const customerPhone = ensurePhonePrefixValue(checkoutPhone).trim();
        const deliveryAddress = checkoutAddress?.value.trim() || "";

        if (!customerName || !customerPhone) {
            window.alert("Укажите телефон для связи.");
            return;
        }

        if (checkoutType === "delivery" && !deliveryAddress) {
            window.alert("Укажите адрес доставки.");
            return;
        }

        if (checkoutSubmit) {
            checkoutSubmit.disabled = true;
        }

        const orderModeLabel = checkoutType === "delivery" ? "доставку" : "самовывоз";
        const paymentLabel = checkoutPayment === "cash" ? "наличными" : "безналично";
        const orderedCutleryCount = cutleryItemsCount;

        window.setTimeout(() => {
            if (checkoutSubmit) {
                checkoutSubmit.disabled = false;
            }

            cart.clear();
            cutleryItemsCount = 0;
            checkoutForm.reset();
            checkoutType = "pickup";
            checkoutPayment = "card";
            ensurePhonePrefixValue(checkoutPhone);
            syncCheckoutType();
            syncCheckoutPayment();
            syncCartCheckoutNote();
            renderCart();
            closeCheckoutModal();
            closeCart();
            window.alert(
                `Заказ на ${orderModeLabel} принят. Блюд: ${totalItems}, приборов: ${orderedCutleryCount}, к оплате: ${formatPrice(totalPriceValue)}. Оплата: ${paymentLabel}.`,
            );
        }, 350);
    });
}

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeCart();
        closeCheckoutModal();
        closeFooterMapModal();
        closeAdminModal();
        closeHeroAdminModal();
        closeMenuSectionAdminModal();
        closeMenuCategoriesAdminModal();
        window.zamzamCatalogAdmin?.close?.();
    }
});

window.addEventListener("scroll", () => {
    lastScrollY = window.scrollY;
    updateFloatingToolsVisibility();
});

window.addEventListener("load", () => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
});

setAdminMode(false);
bindPhonePrefix(checkoutPhone);
bindPhonePrefix(document.getElementById("auth-phone"));
bindPhonePrefix(document.getElementById("auth-register-phone"));
bindPhonePrefix(document.getElementById("orders-admin-phone"));
bindPhonePrefix(document.getElementById("account-phone-input"));
syncCheckoutType();
syncCheckoutPayment();
syncCartCheckoutNote();
ensureHeroEditControls();
loadHeroContent();
ensureSectionEditControls(menuSectionHead, "menuSectionEdit", "Редактировать блок меню");
ensureSectionEditControls(deliverySectionHead, "deliverySectionEdit", "Редактировать блок доставки");
ensureSectionEditControls(contactSectionHead, "contactSectionEdit", "Редактировать блок контактов");
loadSectionContent("/api/redactor/menu-items/menu-section-content", menuSectionHead);
loadSectionContent("/api/redactor/menu-items/delivery-section-content", deliverySectionHead);
loadSectionContent("/api/redactor/menu-items/contact-section-content", contactSectionHead);
applyFilter(activeFilter);
renderCart();
updateFloatingToolsVisibility();
initRevealAnimations();

window.zamzamApp = {
    getCartEntries: () => getCartEntries().map((item) => ({ ...item })),
    getCartTotals: () => ({ ...getCartTotals() }),
    getCheckoutState: () => ({
        checkoutType,
        checkoutPayment,
        cutleryItemsCount,
    }),
    closeCart,
    closeCheckoutModal,
    openAdminModalWithItem,
    setAdminMode,
    formatPrice,
    resetAfterOrder() {
        cart.clear();
        cutleryItemsCount = 0;
        checkoutForm?.reset();
        checkoutType = "pickup";
        checkoutPayment = "card";
        ensurePhonePrefixValue(checkoutPhone);
        syncCheckoutType();
        syncCheckoutPayment();
        syncCartCheckoutNote();
        renderCart();
        closeCheckoutModal();
        closeCart();
    },
};
