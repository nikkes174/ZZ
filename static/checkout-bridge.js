(function () {
    window.zamzamAccountCheckoutEnabled = true;

    const SESSION_STORAGE_KEY = "zamzam_session_token";
    const REFRESH_STORAGE_KEY = "zamzam_refresh_token";
    const PENDING_PAYMENT_STORAGE_KEY = "zamzam_pending_payment_id";
    const checkoutForm = document.getElementById("checkout-form");
    const checkoutSubmit = document.getElementById("checkout-submit");
    const checkoutName = document.getElementById("checkout-name");
    const checkoutPhone = document.getElementById("checkout-phone");
    const checkoutAddress = document.getElementById("checkout-address");
    const checkoutEntrance = document.getElementById("checkout-entrance");
    const checkoutComment = document.getElementById("checkout-comment");
    const checkoutBonusSpent = document.getElementById("checkout-bonus-spent");
    const checkoutOfertaConsent = document.getElementById("checkout-oferta-consent");
    const checkoutPolicyConsent = document.getElementById("checkout-policy-consent");
    const checkoutConsents = document.querySelector(".checkout-consents");
    let consentPopupTimeoutId = null;
    let checkoutWarningTimeoutId = null;

    function showConsentPopup() {
        let popup = document.getElementById("checkout-consent-popup");
        if (!popup) {
            popup = document.createElement("div");
            popup.id = "checkout-consent-popup";
            popup.className = "checkout-consent-popup";
            popup.setAttribute("role", "alert");
            document.body.appendChild(popup);
        }

        popup.textContent = "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u0435 \u0441\u043e\u0433\u043b\u0430\u0441\u0438\u0435 \u0441 \u043e\u0444\u0435\u0440\u0442\u043e\u0439 \u0438 \u043f\u043e\u043b\u0438\u0442\u0438\u043a\u043e\u0439 \u043a\u043e\u043d\u0444\u0438\u0434\u0435\u043d\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u0438.";
        popup.classList.add("is-visible");
        checkoutConsents?.classList.add("is-attention");

        if (consentPopupTimeoutId) {
            window.clearTimeout(consentPopupTimeoutId);
        }

        consentPopupTimeoutId = window.setTimeout(() => {
            popup.classList.remove("is-visible");
            checkoutConsents?.classList.remove("is-attention");
        }, 3200);
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

    function hasCheckoutConsents() {
        return Boolean(checkoutOfertaConsent?.checked && checkoutPolicyConsent?.checked);
    }

    function getSessionToken() {
        return window.sessionStorage.getItem(SESSION_STORAGE_KEY) || "";
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

    function getBonusSpentValue() {
        return Math.max(0, Number(checkoutBonusSpent?.value || 0));
    }

    function isValidCheckoutPhone(phone) {
        const digits = String(phone || "").replace(/\D/g, "");
        return digits.length === 11 && digits[0] === "7";
    }

    function getResponseErrorMessage(payload, fallbackMessage) {
        return typeof payload?.detail === "string" ? payload.detail : fallbackMessage;
    }

    function buildOrderPayload() {
        const appApi = window.zamzamApp || null;
        if (!appApi) {
            throw new Error("Не удалось подготовить заказ. Обновите страницу и попробуйте снова.");
        }

        const entries = appApi.getCartEntries();
        const checkoutState = appApi.getCheckoutState();
        const customerName = checkoutName?.value.trim() || "";
        const customerPhone = ensurePhonePrefixValue(checkoutPhone).trim();
        const deliveryAddress = checkoutAddress?.value.trim() || "";
        const entrance = checkoutEntrance?.value.trim() || "";
        const comment = checkoutComment?.value.trim() || "";
        const bonusSpent = getBonusSpentValue();

        return {
            appApi,
            entries,
            customerName,
            customerPhone,
            payload: {
                customer_name: customerName,
                customer_phone: customerPhone,
                checkout_type: checkoutState.checkoutType,
                payment_type: checkoutState.checkoutPayment,
                delivery_address: deliveryAddress || null,
                entrance: entrance || null,
                comment: comment || null,
                cutlery_count: checkoutState.cutleryItemsCount,
                bonus_spent: bonusSpent,
                items: entries.map((item) => ({
                    id: item.id,
                    title: item.title,
                    price: item.price,
                    quantity: item.quantity,
                })),
            },
        };
    }

    function validateCheckoutConsents() {
        if (hasCheckoutConsents()) {
            return true;
        }
        showConsentPopup();
        return false;

        if (!checkoutOfertaConsent?.checked || !checkoutPolicyConsent?.checked) {
            window.alert("Подтвердите согласие с офертой и политикой конфиденциальности.");
            return false;
        }
        return true;
    }

    async function submitCheckout(event) {
        event.preventDefault();
        event.stopImmediatePropagation();

        const sessionToken = getSessionToken();
        if (!sessionToken) {
            window.alert("Сначала войдите в кабинет.");
            return;
        }

        let orderData;
        try {
            orderData = buildOrderPayload();
        } catch (error) {
            window.alert(error.message || "Не удалось подготовить заказ.");
            return;
        }

        if (!orderData.entries.length) {
            window.alert("Сначала добавьте блюда в корзину.");
            return;
        }

        if (!orderData.customerName || !isValidCheckoutPhone(orderData.customerPhone)) {
            showCheckoutWarning("Заполните имя и телефон.");
            checkoutPhone?.focus();
            return;
        }

        if (!validateCheckoutConsents()) {
            return;
        }

        if (checkoutSubmit) {
            checkoutSubmit.disabled = true;
        }

        try {
            const response = await fetch("/api/orders", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${sessionToken}`,
                },
                body: JSON.stringify(orderData.payload),
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(getResponseErrorMessage(payload, "Не удалось оформить заказ."));
            }

            if (payload?.order_id && !payload?.confirmation_url) {
                if (checkoutBonusSpent) {
                    checkoutBonusSpent.value = "0";
                }
                orderData.appApi.resetAfterOrder();
                window.loadZamzamAccount?.();
                return;
            }

            if (!payload?.confirmation_url) {
                throw new Error("Не удалось получить ссылку на оплату.");
            }
            if (payload.payment_id) {
                window.sessionStorage.setItem(PENDING_PAYMENT_STORAGE_KEY, payload.payment_id);
            }
            window.location.href = payload.confirmation_url;
            if (checkoutBonusSpent) {
                checkoutBonusSpent.value = "0";
            }
        } catch (error) {
            showCheckoutWarning(error.message || "Не удалось оформить заказ.");
        } finally {
            if (checkoutSubmit) {
                checkoutSubmit.disabled = false;
            }
        }
    }

    checkoutForm?.addEventListener("submit", submitCheckout, true);
    checkoutSubmit?.addEventListener(
        "click",
        (event) => {
            if (hasCheckoutConsents()) {
                return;
            }

            event.preventDefault();
            event.stopImmediatePropagation();
            showConsentPopup();

            const missingConsent = !checkoutOfertaConsent?.checked
                ? checkoutOfertaConsent
                : checkoutPolicyConsent;
            missingConsent?.focus();
        },
        true,
    );
    [checkoutOfertaConsent, checkoutPolicyConsent].forEach((consent) => {
        consent?.addEventListener("invalid", (event) => {
            event.preventDefault();
            showConsentPopup();
        });
        consent?.addEventListener("change", () => {
            if (hasCheckoutConsents()) {
                checkoutConsents?.classList.remove("is-attention");
            }
        });
    });
})();
