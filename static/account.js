(() => {
const SESSION_STORAGE_KEY = "zamzam_session_token";
const REFRESH_STORAGE_KEY = "zamzam_refresh_token";
const PENDING_PAYMENT_STORAGE_KEY = "zamzam_pending_payment_id";
const PENDING_PAYMENT_SYNC_RETRY_DELAYS = [3000, 7000, 15000, 30000];
let pendingPaymentSyncRetryIndex = 0;
let pendingPaymentSyncTimeoutId = null;
window.zamzamAuthFallbackBound = true;
window.zamzamAccountCheckoutEnabled = true;

function readPersistentStorage(key) {
    try {
        return window.localStorage.getItem(key) || window.sessionStorage.getItem(key) || "";
    } catch (error) {
        return window.sessionStorage.getItem(key) || "";
    }
}

function writePersistentStorage(key, value) {
    if (!value) {
        return;
    }
    try {
        window.localStorage.setItem(key, value);
    } catch (error) {
        // Keep checkout working in restricted mobile browser storage modes.
    }
    window.sessionStorage.setItem(key, value);
}

function removePersistentStorage(key) {
    try {
        window.localStorage.removeItem(key);
    } catch (error) {
        // Keep logout working even when persistent storage is unavailable.
    }
    window.sessionStorage.removeItem(key);
}

const ACTIVE_ORDER_STATUSES = new Set(["Готовится", "Приготовлен", "Заказ отправлен", "Готов к выдаче"]);

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
const authRegisterEmail = document.getElementById("auth-register-email");
const authRegisterPassword = document.getElementById("auth-register-password");
const authRecoveryForm = document.getElementById("auth-recovery-form");
const authRecoveryEmail = document.getElementById("auth-recovery-email");
const authRecoveryTokenField = document.getElementById("auth-recovery-token-field");
const authRecoveryToken = document.getElementById("auth-recovery-token");
const authRecoveryPasswordField = document.getElementById("auth-recovery-password-field");
const authRecoveryPassword = document.getElementById("auth-recovery-password");
const authForgotPassword = document.getElementById("auth-forgot-password");
const authRecoverySubmit = document.getElementById("auth-recovery-submit");
const authResetSubmit = document.getElementById("auth-reset-submit");
const authLoginSubmit = document.getElementById("auth-login-submit");
const authRegisterSubmit = document.getElementById("auth-register-submit");
const authRegisterOfertaConsent = document.getElementById("auth-register-oferta-consent");
const authRegisterPolicyConsent = document.getElementById("auth-register-policy-consent");
const authRegisterConsents = document.getElementById("auth-register-consents");

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
const floatingTools = document.querySelector(".floating-tools");
const checkoutOfertaConsent = document.getElementById("checkout-oferta-consent");
const checkoutPolicyConsent = document.getElementById("checkout-policy-consent");
const checkoutAddressInput = document.getElementById("checkout-address");
const checkoutHouseInput = document.getElementById("checkout-house");
const checkoutFlatInput = document.getElementById("checkout-flat");

let sessionToken = readPersistentStorage(SESSION_STORAGE_KEY);
let authMode = "login";
let recoveryCodeSent = false;
let currentBonusBalance = 0;
let lastAutofilledCheckoutName = "";
let lastAutofilledCheckoutPhone = "";
let latestCheckoutProfileUser = null;
let accountAutoRefreshInFlight = false;
let checkoutWarningTimeoutId = null;

function refreshSessionToken() {
    sessionToken = readPersistentStorage(SESSION_STORAGE_KEY);
    return sessionToken;
}

function setAuthTokens(payload) {
    sessionToken = payload?.access_token || "";
    const refreshToken = payload?.refresh_token || "";
    if (sessionToken) {
        writePersistentStorage(SESSION_STORAGE_KEY, sessionToken);
    }
    if (refreshToken) {
        writePersistentStorage(REFRESH_STORAGE_KEY, refreshToken);
    }
}

function clearAuthTokens() {
    removePersistentStorage(SESSION_STORAGE_KEY);
    removePersistentStorage(REFRESH_STORAGE_KEY);
    sessionToken = "";
}

async function refreshAccessToken() {
    const refreshToken = readPersistentStorage(REFRESH_STORAGE_KEY);
    if (!refreshToken) {
        return false;
    }

    const response = await fetch("/api/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload?.access_token) {
        clearAuthTokens();
        return false;
    }
    setAuthTokens(payload);
    return true;
}

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

function isValidCheckoutPhone(phone) {
    const digits = String(phone || "").replace(/\D/g, "");
    return digits.length === 11 && digits[0] === "7";
}

function getResponseErrorMessage(payload, fallbackMessage) {
    return typeof payload?.detail === "string" ? payload.detail : fallbackMessage;
}

function showCheckoutWarning(message) {
    let popup = document.getElementById("checkout-warning-popup");
    if (!popup) {
        popup = document.createElement("div");
        popup.id = "checkout-warning-popup";
        popup.className = "checkout-consent-popup checkout-warning-popup";
        popup.setAttribute("role", "alert");
        document.body.appendChild(popup);
    }

    popup.textContent = message;
    popup.classList.add("is-visible");

    if (checkoutWarningTimeoutId) {
        window.clearTimeout(checkoutWarningTimeoutId);
    }

    checkoutWarningTimeoutId = window.setTimeout(() => {
        popup.classList.remove("is-visible");
    }, 3200);
}

function getCheckoutName() {
    return document.getElementById("checkout-name")?.value.trim() || "";
}

function isCheckoutPhonePlaceholderValue(value) {
    const normalized = String(value || "").trim();
    if (!normalized) {
        return true;
    }

    const digits = normalized.replace(/\D/g, "");
    return digits === "" || digits === "7";
}

function syncCheckoutProfileFields(user) {
    if (!user) {
        return;
    }

    latestCheckoutProfileUser = {
        full_name: (user.full_name || "").trim(),
        phone: (user.phone || "").trim(),
    };

    const checkoutNameInput = document.getElementById("checkout-name");
    const checkoutPhoneInput = document.getElementById("checkout-phone");
    const nextName = latestCheckoutProfileUser.full_name;
    const nextPhone = latestCheckoutProfileUser.phone;

    if (checkoutNameInput && nextName) {
        const currentName = checkoutNameInput.value.trim();
        if (!currentName || currentName === lastAutofilledCheckoutName) {
            checkoutNameInput.value = nextName;
            lastAutofilledCheckoutName = nextName;
        }
    }

    if (checkoutPhoneInput && nextPhone) {
        const currentPhone = checkoutPhoneInput.value.trim();
        if (isCheckoutPhonePlaceholderValue(currentPhone) || currentPhone === lastAutofilledCheckoutPhone) {
            checkoutPhoneInput.value = nextPhone;
            ensurePhonePrefixValue(checkoutPhoneInput);
            lastAutofilledCheckoutPhone = checkoutPhoneInput.value.trim();
        }
    }
}

window.zamzamSyncCheckoutProfileFields = (user = null) => {
    if (user) {
        syncCheckoutProfileFields(user);
        return;
    }

    if (latestCheckoutProfileUser) {
        syncCheckoutProfileFields(latestCheckoutProfileUser);
    }
};

function getCartSubtotal() {
    const appApi = getAppApi();
    if (!appApi) {
        return 0;
    }
    return appApi.getCartTotals().totalPriceValue || 0;
}

function validateCheckoutConsents() {
    if (!checkoutOfertaConsent?.checked || !checkoutPolicyConsent?.checked) {
        window.alert("Подтвердите согласие с офертой и политикой конфиденциальности.");
        return false;
    }
    return true;
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

function hasRegisterConsents() {
    return Boolean(authRegisterOfertaConsent?.checked && authRegisterPolicyConsent?.checked);
}

function showRegisterConsentWarning() {
    authRegisterConsents?.classList.add("is-attention");
    setHint("Подтвердите согласие с офертой и политикой конфиденциальности.", true);

    const missingConsent = !authRegisterOfertaConsent?.checked
        ? authRegisterOfertaConsent
        : authRegisterPolicyConsent;
    missingConsent?.focus();
}

function syncRecoveryStep() {
    authRecoveryTokenField?.classList.toggle("is-hidden", !recoveryCodeSent);
    authRecoveryPasswordField?.classList.toggle("is-hidden", !recoveryCodeSent);
    authResetSubmit?.classList.toggle("is-hidden", !recoveryCodeSent);
    authRecoverySubmit?.classList.toggle("is-hidden", recoveryCodeSent);

    if (authRecoveryToken) {
        authRecoveryToken.required = recoveryCodeSent;
    }
    if (authRecoveryPassword) {
        authRecoveryPassword.required = recoveryCodeSent;
    }
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
    authRecoveryForm?.classList.toggle("is-hidden", authMode !== "recovery");
    authTabLogin?.classList.toggle("is-active", authMode === "login");
    authTabRegister?.classList.toggle("is-active", authMode === "register");
    if (authBack) {
        authBack.style.visibility = authMode === "recovery" ? "visible" : "hidden";
    }
}

function setAuthMode(mode = "login") {
    authMode = ["login", "register", "recovery"].includes(mode) ? mode : "login";
    if (authMode === "recovery") {
        recoveryCodeSent = false;
    }
    syncAuthMode();
    syncRecoveryStep();
    setHint("");

    if (authMode === "login") {
        if (authPhone && !authPhone.value.trim()) {
            authPhone.value = getCheckoutPhone();
        }
        return;
    }

    if (authMode === "recovery") {
        if (authRecoveryEmail && authRegisterEmail?.value.trim() && !authRecoveryEmail.value.trim()) {
            authRecoveryEmail.value = authRegisterEmail.value.trim();
        }
        if (authRecoveryToken) {
            authRecoveryToken.value = "";
        }
        if (authRecoveryPassword) {
            authRecoveryPassword.value = "";
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
    refreshSessionToken();
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
    refreshSessionToken();
    if (loginButton) {
        loginButton.textContent = sessionToken ? "Кабинет" : "Войти";
    }
    accountFloatingTrigger?.classList.toggle("is-hidden", !sessionToken);
}

function getSessionHeaders() {
    refreshSessionToken();
    return {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sessionToken}`,
    };
}

const baseUpdateLoginButton = updateLoginButton;
updateLoginButton = function () {
    baseUpdateLoginButton();
    if (loginButton) {
        loginButton.textContent = sessionToken ? "Выйти" : "Войти";
    }
    if (sessionToken) {
        floatingTools?.classList.remove("is-hidden");
    }
};

function formatOrderDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "" : date.toLocaleString("ru-RU");
}

function getCheckoutTypeLabel(checkoutType) {
    return checkoutType === "delivery" ? "Доставка" : "Самовывоз";
}

function getOrderStatusClass(status) {
    if (status === "Готовится") {
        return "account-order-status-preparing";
    }
    if (status === "Готов к выдаче") {
        return "account-order-status-ready";
    }
    if (status === "Приготовлен") {
        return "account-order-status-ready";
    }
    return "";
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
                <span class="account-order-status ${getOrderStatusClass(order.status)}">${order.status}</span>
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
                        <span class="account-order-status ${getOrderStatusClass(order.status)}">${order.status}</span>
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

function isAccountModalOpen() {
    return Boolean(accountSection && !accountSection.classList.contains("is-hidden"));
}

async function loadAccount() {
    refreshSessionToken();
    if (!sessionToken) {
        currentBonusBalance = 0;
        latestCheckoutProfileUser = null;
        window.zamzamApp?.setAdminMode?.(false);
        updateLoginButton();
        syncBonusUi();
        closeAccountModal();
        return;
    }

    try {
        let [dashboardResponse, ordersResponse] = await Promise.all([
            fetch("/api/user/me", { headers: { Authorization: `Bearer ${sessionToken}` } }),
            fetch("/api/orders/my", { headers: { Authorization: `Bearer ${sessionToken}` } }),
        ]);

        if (dashboardResponse.status === 401 || ordersResponse.status === 401) {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                refreshSessionToken();
                [dashboardResponse, ordersResponse] = await Promise.all([
                    fetch("/api/user/me", { headers: { Authorization: `Bearer ${sessionToken}` } }),
                    fetch("/api/orders/my", { headers: { Authorization: `Bearer ${sessionToken}` } }),
                ]);
            }
        }

        if (dashboardResponse.status === 401 || ordersResponse.status === 401) {
            clearAuthTokens();
            currentBonusBalance = 0;
            latestCheckoutProfileUser = null;
            window.zamzamApp?.setAdminMode?.(false);
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
        window.zamzamApp?.setAdminMode?.(Boolean(dashboard.user.is_admin));

        if (accountBonusBalance) {
            accountBonusBalance.textContent = `${dashboard.user.bonus_balance}`;
        }
        if (accountUserPhone) {
            accountUserPhone.textContent = dashboard.user.phone;
        }
        if (accountPhoneInput) {
            accountPhoneInput.value = dashboard.user.phone;
        }
        syncCheckoutProfileFields(dashboard.user);
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

async function syncPendingPayment() {
    refreshSessionToken();
    const paymentId = readPersistentStorage(PENDING_PAYMENT_STORAGE_KEY);
    if (!paymentId || !sessionToken) {
        pendingPaymentSyncRetryIndex = 0;
        if (pendingPaymentSyncTimeoutId) {
            window.clearTimeout(pendingPaymentSyncTimeoutId);
            pendingPaymentSyncTimeoutId = null;
        }
        return;
    }

    try {
        const response = await fetch(`/api/payments/${encodeURIComponent(paymentId)}/sync`, {
            method: "POST",
            headers: { Authorization: `Bearer ${sessionToken}` },
        });
        const payload = await response.json().catch(() => ({}));
        if (response.ok && payload?.order_id) {
            removePersistentStorage(PENDING_PAYMENT_STORAGE_KEY);
            pendingPaymentSyncRetryIndex = 0;
            if (pendingPaymentSyncTimeoutId) {
                window.clearTimeout(pendingPaymentSyncTimeoutId);
                pendingPaymentSyncTimeoutId = null;
            }
            await loadAccount();
            if (typeof window.showZamzamOrderSuccessModal === "function") {
                window.showZamzamOrderSuccessModal("Ваш заказ принят. Скоро с вами свяжется наш оператор.");
            } else if (typeof window.showZamzamToast === "function") {
                window.showZamzamToast("Заказ успешно оплачен");
            }
        }
    } catch (error) {
        console.error(error);
    }

    if (!readPersistentStorage(PENDING_PAYMENT_STORAGE_KEY)) {
        pendingPaymentSyncRetryIndex = 0;
        return;
    }
    if (pendingPaymentSyncTimeoutId || pendingPaymentSyncRetryIndex >= PENDING_PAYMENT_SYNC_RETRY_DELAYS.length) {
        return;
    }
    const retryDelay = PENDING_PAYMENT_SYNC_RETRY_DELAYS[pendingPaymentSyncRetryIndex];
    pendingPaymentSyncRetryIndex += 1;
    pendingPaymentSyncTimeoutId = window.setTimeout(() => {
        pendingPaymentSyncTimeoutId = null;
        syncPendingPayment();
    }, retryDelay);
}

async function handleAuthSuccess(payload) {
    setAuthTokens(payload);
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
        const response = await fetch("/api/auth/login", {
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
    const email = authRegisterEmail?.value.trim() || "";
    const password = authRegisterPassword?.value.trim() || "";
    const fullName = authRegisterName?.value.trim() || getCheckoutName() || null;
    if (!phone || !email || !password) {
        setHint("Введите номер телефона, email и пароль.", true);
        return;
    }

    if (!hasRegisterConsents()) {
        showRegisterConsentWarning();
        return;
    }

    if (authRegisterSubmit) {
        authRegisterSubmit.disabled = true;
    }
    setHint("");

    try {
        const response = await fetch("/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                phone,
                email,
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

async function requestPasswordRecovery(event) {
    event.preventDefault();

    const email = authRecoveryEmail?.value.trim() || "";
    if (!email) {
        setHint("Введите email для восстановления пароля.", true);
        return;
    }

    if (authRecoverySubmit) {
        authRecoverySubmit.disabled = true;
    }
    setHint("");

    try {
        const response = await fetch("/api/auth/password/recovery", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось отправить письмо.");
        }

        recoveryCodeSent = true;
        syncRecoveryStep();
        setHint("Если email зарегистрирован, код восстановления отправлен.", false);
        authRecoveryToken?.focus();
    } catch (error) {
        setHint(error.message || "Не удалось отправить письмо.", true);
    } finally {
        if (authRecoverySubmit) {
            authRecoverySubmit.disabled = false;
        }
    }
}

async function resetPassword(event) {
    event.preventDefault();

    const token = authRecoveryToken?.value.trim() || "";
    const password = authRecoveryPassword?.value.trim() || "";
    if (!token || !password) {
        setHint("Введите код из письма и новый пароль.", true);
        return;
    }

    if (authResetSubmit) {
        authResetSubmit.disabled = true;
    }
    setHint("");

    try {
        const response = await fetch("/api/auth/password/reset", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token, password }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось сменить пароль.");
        }

        setHint("Пароль успешно изменен. Теперь можно войти.", false);
        setAuthMode("login");
        if (authPassword) {
            authPassword.value = "";
            authPassword.focus();
        }
    } catch (error) {
        setHint(error.message || "Не удалось сменить пароль.", true);
    } finally {
        if (authResetSubmit) {
            authResetSubmit.disabled = false;
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
        syncCheckoutProfileFields({
            full_name: latestCheckoutProfileUser?.full_name || "",
            phone: payload.phone,
        });
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
    const deliveryStreet = checkoutAddressInput?.value.trim() || "";
    const deliveryHouse = checkoutHouseInput?.value.trim() || "";
    const deliveryFlat = checkoutFlatInput?.value.trim() || "";
    const entrance = document.getElementById("checkout-entrance")?.value.trim() || "";
    const comment = document.getElementById("checkout-comment")?.value.trim() || "";
    const isDelivery = checkoutState.checkoutType === "delivery";

    return {
        entries,
        customerName,
        customerPhone,
        bonusSpent: clampBonusSpent(getBonusSpentValue()),
        payload: {
            customer_name: customerName,
            customer_phone: customerPhone,
            checkout_type: checkoutState.checkoutType,
            branch_code: checkoutState.branchCode,
            payment_type: "card",
            delivery_address: null,
            delivery_street: isDelivery ? deliveryStreet || null : null,
            delivery_house: isDelivery ? deliveryHouse || null : null,
            delivery_flat: isDelivery ? deliveryFlat || null : null,
            entrance: isDelivery ? entrance || null : null,
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

    if (!customerName || !isValidCheckoutPhone(customerPhone)) {
        showCheckoutWarning("Заполните имя и телефон.");
        document.getElementById("checkout-phone")?.focus();
        return;
    }

    if (payload.checkout_type === "delivery" && !payload.delivery_street) {
        showCheckoutWarning("Укажите улицу доставки.");
        checkoutAddressInput?.focus();
        return;
    }

    if (payload.checkout_type === "delivery" && !payload.delivery_house) {
        showCheckoutWarning("Укажите номер дома.");
        checkoutHouseInput?.focus();
        return;
    }

    if (!validateCheckoutConsents()) {
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
            throw new Error(getResponseErrorMessage(responsePayload, "Не удалось оформить заказ."));
        }

        if (responsePayload?.order_id && !responsePayload?.confirmation_url) {
            currentBonusBalance = Math.max(
                0,
                Number(responsePayload.bonus_balance ?? currentBonusBalance - payload.bonus_spent),
            );
            if (checkoutBonusSpent) {
                checkoutBonusSpent.value = "0";
            }
            syncBonusUi();
            appApi.resetAfterOrder();
            await loadAccount();
            window.showZamzamOrderSuccessModal?.("Ваш заказ принят. Скоро с вами свяжется наш оператор.");
            return;
        }

        if (!responsePayload?.confirmation_url) {
            throw new Error("Не удалось получить ссылку на оплату.");
        }
        if (responsePayload.payment_id) {
            writePersistentStorage(PENDING_PAYMENT_STORAGE_KEY, responsePayload.payment_id);
        }
        window.location.href = responsePayload.confirmation_url;
        currentBonusBalance = Math.max(0, currentBonusBalance - payload.bonus_spent);
        if (checkoutBonusSpent) {
            checkoutBonusSpent.value = "0";
        }
    } catch (error) {
        showCheckoutWarning(error.message || "Не удалось оформить заказ.");
    } finally {
        checkoutSubmit.disabled = false;
    }
}

async function submitOrder(event) {
    event.preventDefault();
    event.stopImmediatePropagation();
    refreshSessionToken();

    const appApi = getAppApi();
    if (!appApi) {
        showCheckoutWarning("Не удалось подготовить заказ. Обновите страницу и попробуйте снова.");
        return;
    }

    const { entries, customerName, customerPhone } = buildOrderPayload(appApi);

    if (!entries.length) {
        window.alert("Сначала добавьте блюда в корзину.");
        return;
    }

    if (!customerName || !isValidCheckoutPhone(customerPhone)) {
        showCheckoutWarning("Заполните имя и телефон.");
        document.getElementById("checkout-phone")?.focus();
        return;
    }

    if (!validateCheckoutConsents()) {
        return;
    }

    if (!sessionToken) {
        openAuthRequiredModal();
        return;
    }

    await submitOrderWithSession();
}

function logout() {
    const refreshToken = readPersistentStorage(REFRESH_STORAGE_KEY);
    fetch("/api/auth/logout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
    }).catch(() => null).finally(() => {
        clearAuthTokens();
        currentBonusBalance = 0;
        latestCheckoutProfileUser = null;
        window.zamzamApp?.setAdminMode?.(false);
        closeAuthModal();
        closeAuthRequiredModal();
        closeAccountModal();
        updateLoginButton();
        syncBonusUi();
    });
}

async function handleLoginButtonClick(event) {
    event?.preventDefault?.();
    refreshSessionToken();
    if (sessionToken) {
        logout();
        return;
    }
    await window.openZamzamAuthModal("login");
}

if (loginButton) {
    loginButton.onclick = handleLoginButtonClick;
    loginButton.addEventListener("click", handleLoginButtonClick);
}

accountFloatingTrigger?.addEventListener("click", async () => {
    refreshSessionToken();
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
authForgotPassword?.addEventListener("click", () => {
    setAuthMode("recovery");
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
authRecoveryForm?.addEventListener("submit", requestPasswordRecovery);
authResetSubmit?.addEventListener("click", resetPassword);
authRegisterSubmit?.addEventListener(
    "click",
    (event) => {
        if (hasRegisterConsents()) {
            return;
        }

        event.preventDefault();
        event.stopImmediatePropagation();
        showRegisterConsentWarning();
    },
    true,
);
[authRegisterOfertaConsent, authRegisterPolicyConsent].forEach((consent) => {
    consent?.addEventListener("invalid", (event) => {
        event.preventDefault();
        showRegisterConsentWarning();
    });
    consent?.addEventListener("change", () => {
        if (hasRegisterConsents()) {
            authRegisterConsents?.classList.remove("is-attention");
            setHint("");
        }
    });
});
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

if (sessionToken) {
    loadAccount();
    syncPendingPayment();
}

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

window.setInterval(async () => {
    refreshSessionToken();
    if (!sessionToken || !isAccountModalOpen() || document.hidden || accountAutoRefreshInFlight) {
        return;
    }

    accountAutoRefreshInFlight = true;
    try {
        await loadAccount();
    } finally {
        accountAutoRefreshInFlight = false;
    }
}, 15000);
})();
