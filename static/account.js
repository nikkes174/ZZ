const SESSION_STORAGE_KEY = "zamzam_session_token";
window.zamzamAuthFallbackBound = true;

const authModal = document.getElementById("auth-modal");
const authBackdrop = document.getElementById("auth-backdrop");
const authBack = document.getElementById("auth-back");
const authClose = document.getElementById("auth-close");
const authHint = document.getElementById("auth-hint");
const authPhone = document.getElementById("auth-phone");
const authCode = document.getElementById("auth-code");
const authCodeMessage = document.getElementById("auth-code-message");
const authRequestForm = document.getElementById("auth-request-form");
const authVerifyForm = document.getElementById("auth-verify-form");
const authRequestSubmit = document.getElementById("auth-request-submit");
const authVerifySubmit = document.getElementById("auth-verify-submit");
const accountSection = document.getElementById("account");
const accountBonusBalance = document.getElementById("account-bonus-balance");
const accountUserPhone = document.getElementById("account-user-phone");
const accountOrderStatus = document.getElementById("account-order-status");
const accountOrdersCount = document.getElementById("account-orders-count");
const accountOrdersList = document.getElementById("account-orders-list");
const accountRefresh = document.getElementById("account-refresh");
const loginButton = document.getElementById("cart-open-topbar");
const checkoutForm = document.getElementById("checkout-form");
const checkoutBonusSpent = document.getElementById("checkout-bonus-spent");
const checkoutBonusBalanceText = document.getElementById("checkout-bonus-balance-text");
const checkoutPreviewTotal = document.getElementById("checkout-preview-total");
const checkoutButton = document.getElementById("checkout-button");

let currentPhone = "";
let sessionToken = window.sessionStorage.getItem(SESSION_STORAGE_KEY) || "";
let authContext = "login";
let pendingOrderAfterVerify = false;
let currentBonusBalance = 0;

function getAppApi() {
    return window.zamzamApp || null;
}

function getCheckoutPhone() {
    return document.getElementById("checkout-phone")?.value.trim() || "";
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

function setAuthStep(step) {
    authRequestForm?.classList.toggle("is-hidden", step !== "request");
    authVerifyForm?.classList.toggle("is-hidden", step !== "verify");
    if (authBack) {
        authBack.style.visibility = step === "verify" ? "visible" : "hidden";
    }
}

function openAuthModal(context = "login") {
    authContext = context;
    authBackdrop?.classList.add("is-open");
    authModal?.classList.add("is-open");
    authModal?.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
    setAuthStep("request");
    setHint("");

    if (authCode) {
        authCode.value = "";
    }

    if (context === "order" && authPhone) {
        authPhone.value = getCheckoutPhone();
    }

    if (authVerifySubmit) {
        authVerifySubmit.textContent = context === "order" ? "Подтвердить и оформить" : "Подтвердить";
    }
}

window.openZamzamAuthModal = function openZamzamAuthModal() {
    if (sessionToken) {
        pendingOrderAfterVerify = false;
        showAccountSection();
        loadAccount();
        return false;
    }

    openAuthModal("login");
    return false;
};

function closeAuthModal() {
    authBackdrop?.classList.remove("is-open");
    authModal?.classList.remove("is-open");
    authModal?.setAttribute("aria-hidden", "true");
    document.body.classList.remove("admin-open");
    setHint("");
    authContext = "login";
}

function updateLoginButton() {
    if (!loginButton) {
        return;
    }

    loginButton.textContent = sessionToken ? "Личный кабинет" : "Войти";
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

function renderOrders(orders) {
    if (!accountOrdersList) {
        return;
    }

    if (!orders.length) {
        accountOrdersList.innerHTML = '<div class="account-order-empty">После первого подтвержденного заказа история появится здесь.</div>';
        return;
    }

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
    accountSection?.classList.remove("is-hidden");
    accountSection?.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadAccount() {
    if (!sessionToken) {
        currentBonusBalance = 0;
        updateLoginButton();
        syncBonusUi();
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
            accountSection?.classList.add("is-hidden");
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
        if (accountOrderStatus) {
            accountOrderStatus.textContent = dashboard.latest_order_status || "Заказов пока нет";
        }
        if (accountOrdersCount) {
            accountOrdersCount.textContent = `Активных заказов: ${dashboard.active_orders_count}`;
        }

        renderOrders(ordersPage.items || []);
        updateLoginButton();
        syncBonusUi();

        if (window.location.hash === "#account" || sessionToken) {
            accountSection?.classList.remove("is-hidden");
        }
    } catch (error) {
        console.error(error);
    }
}

async function requestCode(event) {
    event.preventDefault();

    const phone = authPhone?.value.trim() || getCheckoutPhone();
    if (!phone) {
        setHint("Введите номер телефона.", true);
        return;
    }

    authRequestSubmit.disabled = true;
    setHint("");

    try {
        const response = await fetch("/api/user/auth/request-code", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phone }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось отправить код.");
        }

        currentPhone = payload.phone;
        if (authPhone) {
            authPhone.value = payload.phone;
        }
        if (authCodeMessage) {
            authCodeMessage.textContent =
                authContext === "order"
                    ? `${payload.message} Введите код, и заказ оформится автоматически. Демо-код: ${payload.code}`
                    : `${payload.message} Код для демо-подтверждения: ${payload.code}`;
        }
        setAuthStep("verify");
        setHint("Проверьте сообщение и введите код.");
    } catch (error) {
        setHint(error.message || "Не удалось отправить код.", true);
    } finally {
        authRequestSubmit.disabled = false;
    }
}

async function verifyCode(event) {
    event.preventDefault();

    const code = authCode?.value.trim() || "";
    const fullName = getCheckoutName();
    if (!currentPhone || !code) {
        setHint("Введите код подтверждения.", true);
        return;
    }

    authVerifySubmit.disabled = true;
    setHint("");

    try {
        const response = await fetch("/api/user/auth/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                phone: currentPhone,
                code,
                full_name: fullName || null,
            }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось подтвердить номер.");
        }

        sessionToken = payload.session_token;
        window.sessionStorage.setItem(SESSION_STORAGE_KEY, sessionToken);
        updateLoginButton();
        closeAuthModal();
        await loadAccount();

        if (pendingOrderAfterVerify) {
            pendingOrderAfterVerify = false;
            await submitOrderWithSession();
            return;
        }

        showAccountSection();
    } catch (error) {
        setHint(error.message || "Не удалось подтвердить номер.", true);
    } finally {
        authVerifySubmit.disabled = false;
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
        pendingOrderAfterVerify = true;
        openAuthModal("order");
        setHint("Подтвердите номер телефона, и заказ оформится автоматически.", true);
        return;
    }

    pendingOrderAfterVerify = false;
    await submitOrderWithSession();
}

loginButton?.addEventListener(
    "click",
    (event) => {
        event.preventDefault();
        event.stopImmediatePropagation();
        window.openZamzamAuthModal();
    },
    true,
);

authBackdrop?.addEventListener("click", () => {
    pendingOrderAfterVerify = false;
    closeAuthModal();
});
authClose?.addEventListener("click", () => {
    pendingOrderAfterVerify = false;
    closeAuthModal();
});
authBack?.addEventListener("click", () => {
    setAuthStep("request");
    setHint("");
    pendingOrderAfterVerify = false;
});
authRequestForm?.addEventListener("submit", requestCode);
authVerifyForm?.addEventListener("submit", verifyCode);
accountRefresh?.addEventListener("click", loadAccount);
checkoutForm?.addEventListener("submit", submitOrder, true);

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        pendingOrderAfterVerify = false;
        closeAuthModal();
    }
});

updateLoginButton();
syncBonusUi();
loadAccount();

if (window.location.hash === "#account" && sessionToken) {
    accountSection?.classList.remove("is-hidden");
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
