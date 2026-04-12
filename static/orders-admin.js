const ordersAdminModal = document.getElementById("orders-admin-modal");
const ordersAdminOpen = document.getElementById("orders-admin-open");
const ordersAdminClose = document.getElementById("orders-admin-close");
const ordersAdminPhone = document.getElementById("orders-admin-phone");
const ordersAdminSearch = document.getElementById("orders-admin-search");
const ordersAdminRefresh = document.getElementById("orders-admin-refresh");
const ordersAdminResults = document.getElementById("orders-admin-results");
const adminBackdropShared = document.getElementById("admin-backdrop");

function getAdminHeaders(extraHeaders = {}) {
    const token = window.sessionStorage.getItem("zamzam_session_token") || "";
    return token ? { ...extraHeaders, Authorization: `Bearer ${token}` } : { ...extraHeaders };
}

let ordersAdminPhoneFilter = "";
let ordersAdminStatusOptions = {
    pickup: ["Готовится", "Готов к выдаче", "Выдан", "Отменен"],
    delivery: ["Готовится", "Заказ отправлен", "Доставлен", "Отменен"],
};

function ensureOrdersAdminPhoneValue() {
    if (typeof window.zamzamEnsurePhonePrefix === "function") {
        return window.zamzamEnsurePhonePrefix(ordersAdminPhone);
    }
    return ordersAdminPhone?.value || "";
}

function openOrdersAdminModal() {
    if (!ordersAdminModal || !adminBackdropShared) {
        return;
    }

    adminBackdropShared.classList.add("is-open");
    ordersAdminModal.classList.add("is-open");
    ordersAdminModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("admin-open");
}

function closeOrdersAdminModal() {
    if (!ordersAdminModal) {
        return;
    }

    ordersAdminModal.classList.remove("is-open");
    ordersAdminModal.setAttribute("aria-hidden", "true");
    if (!document.querySelector(".admin-modal.is-open")) {
        adminBackdropShared?.classList.remove("is-open");
        document.body.classList.remove("admin-open");
    }
}

window.zamzamOrdersAdmin = {
    close: closeOrdersAdminModal,
};

function formatOrdersAdminDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "" : date.toLocaleString("ru-RU");
}

function getCheckoutTypeLabel(checkoutType) {
    return checkoutType === "delivery" ? "Доставка" : "Самовывоз";
}

function getPaymentTypeLabel(paymentType) {
    return paymentType === "cash" ? "Наличные" : "Безналичные";
}

function getStatusOptions(checkoutType) {
    return ordersAdminStatusOptions[checkoutType] || ["Готовится"];
}

function renderOrdersAdmin(orders) {
    if (!ordersAdminResults) {
        return;
    }

    if (!orders.length) {
        ordersAdminResults.innerHTML = '<div class="account-order-empty">Заказы по выбранному фильтру не найдены.</div>';
        return;
    }

    ordersAdminResults.innerHTML = orders
        .map((order) => {
            const itemsText = order.items.map((item) => `${item.title} x ${item.quantity}`).join(", ");
            const addressText = order.delivery_address || "Не требуется";
            const iikoText = order.iiko_order_id
                ? `iiko: ${order.iiko_creation_status || "unknown"} | order ${order.iiko_order_id} | correlation ${order.iiko_correlation_id || "-"}`
                : "iiko: no data";
            const statusOptions = getStatusOptions(order.checkout_type)
                .map((status) => `<option value="${status}" ${status === order.status ? "selected" : ""}>${status}</option>`)
                .join("");

            return `
                <article class="account-order-card" data-order-id="${order.id}">
                    <div class="account-order-head">
                        <strong>Заказ №${order.id}</strong>
                        <span class="account-order-status">${order.status}</span>
                    </div>
                    <div class="order-admin-meta-grid">
                        <div class="order-admin-meta-card">
                            <span>Клиент</span>
                            <strong>${order.customer_name}</strong>
                        </div>
                        <div class="order-admin-meta-card">
                            <span>Телефон</span>
                            <strong>${order.customer_phone}</strong>
                        </div>
                        <div class="order-admin-meta-card">
                            <span>Тип заказа</span>
                            <strong>${getCheckoutTypeLabel(order.checkout_type)}</strong>
                        </div>
                        <div class="order-admin-meta-card">
                            <span>Оплата</span>
                            <strong>${getPaymentTypeLabel(order.payment_type)}</strong>
                        </div>
                    </div>
                    <div class="account-order-meta">Создан: ${formatOrdersAdminDate(order.created_at)}</div>
                    <div class="account-order-meta">Сумма: ${order.total_amount} руб. • Бонусы: +${order.bonus_awarded}</div>
                    <div class="account-order-meta">Адрес: ${addressText}</div>
                    <div class="account-order-meta">${iikoText}</div>
                    <div class="order-admin-items">${itemsText}</div>
                    <form class="order-admin-actions" data-order-status-form>
                        <label class="admin-field">
                            <span>Статус заказа</span>
                            <select data-order-status-select>${statusOptions}</select>
                        </label>
                        <button class="admin-save" type="submit">Сохранить</button>
                    </form>
                </article>
            `;
        })
        .join("");
}

async function loadOrdersAdmin(phone = "") {
    const params = new URLSearchParams();
    params.set("limit", "30");
    if (phone) {
        params.set("phone", phone);
    }

    const response = await fetch(`/api/orders/admin?${params.toString()}`, {
        headers: getAdminHeaders(),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(payload?.detail || "Не удалось загрузить список заказов.");
    }

    ordersAdminStatusOptions = (payload.status_options || []).reduce((acc, item) => {
        if (item?.checkout_type && Array.isArray(item.statuses)) {
            acc[item.checkout_type] = item.statuses;
        }
        return acc;
    }, { ...ordersAdminStatusOptions });

    renderOrdersAdmin(payload.items || []);
}

async function openAndLoadOrdersAdmin(phone = "") {
    openOrdersAdminModal();
    if (ordersAdminResults) {
        ordersAdminResults.innerHTML = '<div class="account-order-empty">Загружаем заказы...</div>';
    }
    await loadOrdersAdmin(phone);
}

async function searchOrdersAdmin() {
    const phone = ensureOrdersAdminPhoneValue().trim();
    ordersAdminPhoneFilter = phone;
    await openAndLoadOrdersAdmin(phone);
}

async function refreshOrdersAdmin() {
    ordersAdminPhoneFilter = "";
    if (ordersAdminPhone) {
        ordersAdminPhone.value = "+7";
    }
    await openAndLoadOrdersAdmin("");
}

ordersAdminOpen?.addEventListener("click", async () => {
    try {
        if (!document.body.classList.contains("admin-mode")) {
            document.getElementById("admin-toggle")?.click();
        }
        await openAndLoadOrdersAdmin(ordersAdminPhoneFilter);
    } catch (error) {
        window.alert(error.message || "Не удалось открыть управление заказами.");
    }
});

ordersAdminClose?.addEventListener("click", closeOrdersAdminModal);
ordersAdminSearch?.addEventListener("click", async () => {
    try {
        await searchOrdersAdmin();
    } catch (error) {
        window.alert(error.message || "Не удалось найти заказы.");
    }
});
ordersAdminRefresh?.addEventListener("click", async () => {
    try {
        await refreshOrdersAdmin();
    } catch (error) {
        window.alert(error.message || "Не удалось обновить заказы.");
    }
});
adminBackdropShared?.addEventListener("click", closeOrdersAdminModal);

ordersAdminResults?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const form = event.target.closest("[data-order-status-form]");
    const orderCard = event.target.closest("[data-order-id]");
    const select = form?.querySelector("[data-order-status-select]");
    const submitButton = form?.querySelector('button[type="submit"]');
    const orderId = orderCard?.dataset.orderId;
    const status = select?.value || "";

    if (!orderId || !status || !submitButton) {
        return;
    }

    submitButton.disabled = true;

    try {
        const response = await fetch(`/api/orders/${orderId}/status`, {
            method: "PATCH",
            headers: getAdminHeaders({
                "Content-Type": "application/json",
            }),
            body: JSON.stringify({ status }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.detail || "Не удалось обновить статус.");
        }

        await loadOrdersAdmin(ordersAdminPhoneFilter);
        if (typeof window.loadZamzamAccount === "function") {
            await window.loadZamzamAccount();
        }
    } catch (error) {
        window.alert(error.message || "Не удалось обновить статус.");
    } finally {
        submitButton.disabled = false;
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeOrdersAdminModal();
    }
});

ensureOrdersAdminPhoneValue();
