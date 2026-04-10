const SESSION_STORAGE_KEY = "zamzam_session_token";
window.zamzamAuthFallbackBound = true;

const ACTIVE_ORDER_STATUSES = new Set(["Готовится", "Заказ отправлен", "Готов к выдаче"]);

const authModal = document.getElementById("auth-modal");
const authBackdrop = document.getElementById("auth-backdrop");
const authBack = document.getElementById("auth-back");
const authClose = document.getElementById("auth-close");
const authHint = document.getElementById("auth-hint");
const authTabLogin = document.getElementById("auth-tab-login");
const authTabRegister = document.getElementById("auth-tab-register");
const authLoginForm = document.getElementById("auth-login-form");
const authRegisterForm = document.getElementById("auth-register-form");
const authPhone = document.getElementById("auth-phone");
const authPassword = document.getElementById("auth-password");
const authRegisterName = document.getElementById("auth-register-name");
const authRegisterPhone = document.getElementById("auth-register-phone");
const authRegisterPassword = document.getElementById("auth-register-password");
const authLoginSubmit = document.getElementById("auth-login-submit");
const authRegisterSubmit = document.getElementById("auth-register-submit");

const authRequiredModal = document.getElementById("auth-required-modal");
const authRequiredClose = document.getElementById("auth-required-close");
const authRequiredLogin = document.getElementById("auth-required-login");
const authRequiredRegister = document.getElementById("auth-required-register");

const accountSection = document.getElementById("account");
const accountClose = document.getElementById("account-close");
const accountBonusBalance = document.getElementById("account-bonus-balance");
const accountUserPhone = document.getElementById("account-user-phone");
const accountOrderStatus = document.getElementById("account-order-status");
const accountOrdersCount = document.getElementById("account-orders-count");
const accountOrdersList = document.getElementById("account-orders-list");
const accountCurrentOrderCard = document.getElementById("account-current-order-card");
const accountCurrentRefresh = document.getElementById("account-current-refresh");
const accountHistoryRefresh = document.getElementById("account-history-refresh");
const accountPhoneForm = document.getElementById("account-phone-form");
const accountPhoneInput = document.getElementById("account-phone-input");
const accountPhoneSubmit = document.getElementById("account-phone-submit");
const accountPhoneHint = document.getElementById("account-phone-hint");
const accountFloatingTrigger = document.getElementById("account-floating-trigger");

const loginButton = document.getElementById("cart-open-topbar");
const checkoutForm = document.getElementById("checkout-form");
const checkoutBonusSpent = document.getElementById("checkout-bonus-spent");
const checkoutBonusBalanceText = document.getElementById("checkout-bonus-balance-text");
const checkoutPreviewTotal = document.getElementById("checkout-preview-total");
const checkoutButton = document.getElementById("checkout-button");

let sessionToken = window.sessionStorage.getItem(SESSION_STORAGE_KEY) || "";
let authMode = "login";
let currentBonusBalance = 0;

function ensurePhonePrefixValue(input) {
    if (typeof window.zamzamEnsurePhonePrefix === "function") {
        return window.zamzamEnsurePhonePrefix(input);
    }

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

function getAppApi() {
    return window.zamzamApp || null;
}

function getCheckoutPhone() {
    const input = document.getElementById("checkout-phone");
    return ensurePhonePrefixValue(input).trim();
}

function getCheckoutName() {
    return document.getElementById("checkout-name")?.value.trim() || "";
}

function getCartSubtotal() {
    const appApi = getAppApi();
    if (!appApi) {
        return 0;
    }
    return appApi.getCartTotals().totalPriceValue || 0;
}

function getBonusSpentValue() {
    return Math.max(0, Number(checkoutBonusSpent?.value || 0));
}

function clampBonusSpent(nextValue) {
    const subtotal = getCartSubtotal();
    return Math.max(0, Math.min(nextValue, currentBonusBalance, subtotal));
}

function syncBonusUi() {
    if (checkoutBonusBalanceText) {
        checkoutBonusBalanceText.textContent = `Доступно бонусов: ${currentBonusBalance}`;
    }

    if (!checkoutBonusSpent) {
        return;
    }

    const clampedValue = clampBonusSpent(getBonusSpentValue());
    checkoutBonusSpent.max = `${Math.max(0, Math.min(currentBonusBalance, getCartSubtotal()))}`;
    checkoutBonusSpent.value = `${clampedValue}`;

    if (checkoutPreviewTotal) {
        const appApi = getAppApi();
        if (appApi) {
            checkoutPreviewTotal.textContent = appApi.formatPrice(getCartSubtotal() - clampedValue);
        }
    }
}

function setHint(message, isError = false) {
    if (!authHint) {
        return;
    }

    authHint.textContent = message;
    authHint.style.color = isError ? "#9f2d0f" : "";
}

function setAccountPhoneHint(message, isError = false) {
    if (!accountPhoneHint) {
        return;
    }

    accountPhoneHint.textContent = message;
    accountPhoneHint.style.color = isError ? "#9f2d0f" : "";
}

function syncAuthMode() {
    authLoginForm?.classList.toggle("is-hidden", authMode !== "login");
    authRegisterForm?.classList.toggle("is-hidden", authMode !== "register");
    authTabLogin?.classList.toggle("is-active", authMode === "login");
    authTabRegister?.classList.toggle("is-active", authMode === "register");
    if (authBack) {
        authBack.style.visibility = "hidden";
    }
}

function setAuthMode(mode = "login") {
    authMode = mode === "register" ? "register" : "login";
    syncAuthMode();
    setHint("");

    if (authMode === "login") {
        if (authPhone && !authPhone.value.trim()) {
            authPhone.value = getCheckoutPhone();
        }
        return;
    }

    if (authRegisterPhone && !authRegisterPhone.value.trim()) {
        authRegisterPhone.value = getCheckoutPhone();
    }
    if (authRegisterName && !authRegisterName.value.trim()) {
        authRegisterName.value = getCheckoutName();
    }
}

window.setZamzamAuthMode = setAuthMode;

function syncSharedBackdrop() {
    const isAnyModalOpen =
        authModal?.classList.contains("is-open") ||
        authRequiredModal?.classList.contains("is-open") ||
        !accountSection?.classList.contains("is-hidden");

    authBackdrop?.classList.toggle("is-open", Boolean(isAnyModalOpen));
    document.body.classList.toggle("admin-open", Boolean(isAnyModalOpen));
}

function openAuthModal(mode = "login") {
    setAuthMode(mode);
    authModal?.classList.add("is-open");
    authModal?.setAttribute("aria-hidden", "false");
    syncSharedBackdrop();
}

window.openZamzamAuthModal = async function openZamzamAuthModal(mode = "login") {
    if (sessionToken) {
        await loadAccount();
        if (sessionToken) {
            showAccountSection();
            return false;
        }
    }

    openAuthModal(mode);
    return false;
};

function closeAuthModal() {
    authModal?.classList.remove("is-open");
    authModal?.setAttribute("aria-hidden", "true");
    setHint("");
    syncSharedBackdrop();
}

function openAuthRequiredModal() {
    authRequiredModal?.classList.add("is-open");
    authRequiredModal?.setAttribute("aria-hidden", "false");
    syncSharedBackdrop();
}

function closeAuthRequiredModal() {
    authRequiredModal?.classList.remove("is-open");
    authRequiredModal?.setAttribute("aria-hidden", "true");
    syncSharedBackdrop();
}

function openAccountModal() {
    if (!accountSection) {
        return;
    }

    accountSection.classList.remove("is-hidden");
    accountSection.setAttribute("aria-hidden", "false");
    syncSharedBackdrop();
}

function closeAccountModal() {
    if (!accountSection) {
        return;
    }

    accountSection.classList.add("is-hidden");
    accountSection.setAttribute("aria-hidden", "true");
    setAccountPhoneHint("");
    syncSharedBackdrop();
}

function openAuthFromRequired(mode) {
    closeAuthRequiredModal();
    openAuthModal(mode);
}

function updateLoginButton() {
    if (loginButton) {
        loginButton.textContent = sessionToken ? "Кабинет" : "Войти";
    }
    accountFloatingTrigger?.classList.toggle("is-hidden", !sessionToken);
}

function getSessionHeaders() {
    return {
        "Content-Type": "application/json",
        "X-Session-Token": sessionToken,
    };
}

function formatOrderDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "" : date.toLocaleString("ru-RU");
}

function getCheckoutTypeLabel(checkoutType) {
    return checkoutType === "delivery" ? "Доставка" : "Самовывоз";
}

function renderCurrentOrder(order) {
    if (!accountCurrentOrderCard) {
        return;
    }

    if (!order) {
        accountCurrentOrderCard.innerHTML = '<div class="account-order-empty">Активного заказа пока нет.</div>';
        return;
    }

    const itemsText = order.items.map((item) => `${item.title} x ${item.quantity}`).join(", ");
    const addressText = order.delivery_address || "Самовывоз";

    accountCurrentOrderCard.innerHTML = `
        <article class="account-order-card account-order-card-current">
            <div class="account-order-head">
                <strong>Заказ №${order.id}</strong>
                <span class="account-order-status">${order.status}</span>
            </div>
            <div class="account-order-meta">Тип: ${getCheckoutTypeLabel(order.checkout_type)} • Создан: ${formatOrderDate(order.created_at)}</div>
            <div class="account-order-meta">Сумма: ${order.total_amount} руб. • Бонусы: +${order.bonus_awarded}</div>
            <div class="account-order-meta">Получение: ${addressText}</div>
            <div class="account-order-items">${itemsText}</div>
        </article>
    `;
}

function renderOrders(orders) {
    if (!accountOrdersList) {
        return;
    }

    if (!orders.length) {
        accountOrdersList.innerHTML = '<div class="account-order-empty">После первого подтвержденного заказа история появится здесь.</div>';
        renderCurrentOrder(null);
        return;
    }

    const activeOrder = orders.find((order) => ACTIVE_ORDER_STATUSES.has(order.status)) || null;
    renderCurrentOrder(activeOrder);

    accountOrdersList.innerHTML = orders
        .map((order) => {
            const itemsText = order.items.map((item) => `${item.title} x ${item.quantity}`).join(", ");
            return `
                <article class="account-order-card">
                    <div class="account-order-head">
                        <strong>Заказ №${order.id}</strong>
                        <span class="account-order-status">${order.status}</span>
                    </div>
                    <div class="account-order-meta">Создан: ${formatOrderDate(order.created_at)}</div>
                    <div class="account-order-meta">Сумма: ${order.total_amount} руб. • Бонусы: +${order.bonus_awarded}</div>
                    <div class="account-order-items">${itemsText}</div>
                </article>
            `;
        })
        .join("");
}

function showAccountSection() {
    openAccountModal();
}

async function loadAccount() {
    if (!sessionToken) {
        currentBonusBalance = 0;
        updateLoginButton();
        syncBonusUi();
        closeAccountModal();
        return;
    }

    try {
        const [dashboardResponse, ordersResponse] = await Promise.all([
            fetch("/api/user/me", { headers: { "X-Session-Token": sessionToken } }),
            fetch("/api/orders/my", { headers: { "X-Session-Token": sessionToken } }),
        ]);

        if (dashboardResponse.status === 401 || ordersResponse.status === 401) {
            window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
            sessionToken = "";
            currentBonusBalance = 0;
            updateLoginButton();
            syncBonusUi();
            closeAccountModal();
            return;
        }

        if (!dashboardResponse.ok || !ordersResponse.ok) {
            throw new Error("Не удалось загрузить личный кабинет.");
        }

        const dashboard = await dashboardResponse.json();
        const ordersPage = await ordersResponse.json();
        currentBonusBalance = dashboard.user.bonus_balance || 0;

        if (accountBonusBalance) {
            accountBonusBalance.textContent = `${dashboard.user.bonus_balance}`;
        }
        if (accountUserPhone) {
            accountUserPhone.textContent = dashboard.user.phone;
        }
        if (accountPhoneInput) {
            accountPhoneInput.value = dashboard.user.phone;
        }
        if (accountOrderStatus) {
            accountOrderStatus.textContent = dashboard.latest_order_status || "Заказов пока нет";
        }
        if (accountOrdersCount) {
            accountOrdersCount.textContent = `Активных заказов: ${dashboard.active_orders_count}`;
        }

        renderOrders(ordersPage.items || []);
        updateLoginButton();
        syncBonusUi();
    } catch (error) {
        console.error(error);
    }
}

window.loadZamzamAccount = loadAccount;

async function handleAuthSuccess(payload) {
    sessionToken = payload.session_token;
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, sessionToken);
    updateLoginButton();
    closeAuthModal();
    await loadAccount();
    showAccountSection();
}

async function login(event) {
    event.preventDefault();

    const phone = ensurePhonePrefixValue(authPhone).trim();
    const password = authPassword?.value.trim() || "";
    if (!phone || !password) {
        setHint("Введите номер телефона и пароль.", true);
        return;
    }

    if (authLoginSubmit) {
        authLoginSubmit.disabled = true;
    }
    setHint("");

    try {
        const response = await fetch("/api/user/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phone, password }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось выполнить вход.");
        }

        await handleAuthSuccess(payload);
    } catch (error) {
        setHint(error.message || "Не удалось выполнить вход.", true);
    } finally {
        if (authLoginSubmit) {
            authLoginSubmit.disabled = false;
        }
    }
}

async function register(event) {
    event.preventDefault();

    const phone = ensurePhonePrefixValue(authRegisterPhone).trim();
    const password = authRegisterPassword?.value.trim() || "";
    const fullName = authRegisterName?.value.trim() || getCheckoutName() || null;
    if (!phone || !password) {
        setHint("Введите номер телефона и пароль.", true);
        return;
    }

    if (authRegisterSubmit) {
        authRegisterSubmit.disabled = true;
    }
    setHint("");

    try {
        const response = await fetch("/api/user/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                phone,
                password,
                full_name: fullName,
            }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось завершить регистрацию.");
        }

        await handleAuthSuccess(payload);
    } catch (error) {
        setHint(error.message || "Не удалось завершить регистрацию.", true);
    } finally {
        if (authRegisterSubmit) {
            authRegisterSubmit.disabled = false;
        }
    }
}

async function updatePhone(event) {
    event.preventDefault();

    const phone = ensurePhonePrefixValue(accountPhoneInput).trim();
    if (!phone) {
        setAccountPhoneHint("Введите номер телефона.", true);
        return;
    }

    if (accountPhoneSubmit) {
        accountPhoneSubmit.disabled = true;
    }
    setAccountPhoneHint("");

    try {
        const response = await fetch("/api/user/me", {
            method: "PATCH",
            headers: getSessionHeaders(),
            body: JSON.stringify({ phone }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось обновить номер телефона.");
        }

        if (accountUserPhone) {
            accountUserPhone.textContent = payload.phone;
        }
        if (accountPhoneInput) {
            accountPhoneInput.value = payload.phone;
        }
        setAccountPhoneHint("Номер телефона обновлен.");
    } catch (error) {
        setAccountPhoneHint(error.message || "Не удалось обновить номер телефона.", true);
    } finally {
        if (accountPhoneSubmit) {
            accountPhoneSubmit.disabled = false;
        }
    }
}

function buildOrderPayload(appApi) {
    const entries = appApi.getCartEntries();
    const checkoutState = appApi.getCheckoutState();
    const customerName = getCheckoutName();
    const customerPhone = getCheckoutPhone();
    const deliveryAddress = document.getElementById("checkout-address")?.value.trim() || "";
    const entrance = document.getElementById("checkout-entrance")?.value.trim() || "";
    const comment = document.getElementById("checkout-comment")?.value.trim() || "";

    return {
        entries,
        customerName,
        customerPhone,
        bonusSpent: clampBonusSpent(getBonusSpentValue()),
        payload: {
            customer_name: customerName,
            customer_phone: customerPhone,
            checkout_type: checkoutState.checkoutType,
            payment_type: checkoutState.checkoutPayment,
            delivery_address: deliveryAddress || null,
            entrance: entrance || null,
            comment: comment || null,
            cutlery_count: checkoutState.cutleryItemsCount,
            bonus_spent: clampBonusSpent(getBonusSpentValue()),
            items: entries.map((item) => ({
                id: item.id,
                title: item.title,
                price: item.price,
                quantity: item.quantity,
            })),
        },
    };
}

async function submitOrderWithSession() {
    const appApi = getAppApi();
    if (!appApi) {
        return;
    }

    const { entries, customerName, customerPhone, payload } = buildOrderPayload(appApi);
    const checkoutSubmit = document.getElementById("checkout-submit");

    if (!entries.length) {
        window.alert("Сначала добавьте блюда в корзину.");
        return;
    }

    if (!customerName || !customerPhone) {
        window.alert("Заполните имя и телефон.");
        return;
    }

    syncBonusUi();
    checkoutSubmit.disabled = true;

    try {
        const response = await fetch("/api/orders", {
            method: "POST",
            headers: getSessionHeaders(),
            body: JSON.stringify(payload),
        });
        const responsePayload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(responsePayload?.detail || "Не удалось оформить заказ.");
        }

        appApi.resetAfterOrder();
        currentBonusBalance = Math.max(0, currentBonusBalance - payload.bonus_spent);
        if (checkoutBonusSpent) {
            checkoutBonusSpent.value = "0";
        }
        await loadAccount();
        showAccountSection();
    } catch (error) {
        window.alert(error.message || "Не удалось оформить заказ.");
    } finally {
        checkoutSubmit.disabled = false;
    }
}

async function submitOrder(event) {
    const appApi = getAppApi();
    if (!appApi) {
        return;
    }

    event.preventDefault();
    event.stopImmediatePropagation();

    const { entries, customerName, customerPhone } = buildOrderPayload(appApi);

    if (!entries.length) {
        window.alert("Сначала добавьте блюда в корзину.");
        return;
    }

    if (!customerName || !customerPhone) {
        window.alert("Заполните имя и телефон.");
        return;
    }

    if (!sessionToken) {
        openAuthRequiredModal();
        return;
    }

    await submitOrderWithSession();
}

async function handleLoginButtonClick(event) {
    event?.preventDefault?.();
    if (sessionToken) {
        await loadAccount();
        if (sessionToken) {
            showAccountSection();
            return;
        }
    }
    await window.openZamzamAuthModal("login");
}

if (loginButton) {
    loginButton.onclick = handleLoginButtonClick;
    loginButton.addEventListener("click", handleLoginButtonClick);
}

accountFloatingTrigger?.addEventListener("click", async () => {
    await loadAccount();
    if (sessionToken) {
        showAccountSection();
        return;
    }
    await window.openZamzamAuthModal("login");
});

authTabLogin?.addEventListener("click", () => {
    setAuthMode("login");
});
authTabRegister?.addEventListener("click", () => {
    setAuthMode("register");
});
authBack?.addEventListener("click", () => {
    setAuthMode("login");
});
authBackdrop?.addEventListener("click", () => {
    closeAuthModal();
    closeAuthRequiredModal();
    closeAccountModal();
});
authClose?.addEventListener("click", closeAuthModal);
authRequiredClose?.addEventListener("click", closeAuthRequiredModal);
accountClose?.addEventListener("click", closeAccountModal);
authRequiredLogin?.addEventListener("click", () => {
    openAuthFromRequired("login");
});
authRequiredRegister?.addEventListener("click", () => {
    openAuthFromRequired("register");
});
authLoginForm?.addEventListener("submit", login);
authRegisterForm?.addEventListener("submit", register);
accountCurrentRefresh?.addEventListener("click", loadAccount);
accountHistoryRefresh?.addEventListener("click", loadAccount);
accountPhoneForm?.addEventListener("submit", updatePhone);
checkoutForm?.addEventListener("submit", submitOrder, true);

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeAuthModal();
        closeAuthRequiredModal();
        closeAccountModal();
    }
});

updateLoginButton();
syncBonusUi();
syncAuthMode();
loadAccount();

checkoutBonusSpent?.addEventListener("input", syncBonusUi);
checkoutButton?.addEventListener("click", () => {
    window.setTimeout(syncBonusUi, 0);
});
document.getElementById("cart-checkout-type-pickup")?.addEventListener("click", () => {
    window.setTimeout(syncBonusUi, 0);
});
document.getElementById("cart-checkout-type-delivery")?.addEventListener("click", () => {
    window.setTimeout(syncBonusUi, 0);
});
