(function () {
    const SESSION_STORAGE_KEY = "zamzam_session_token";
    const REFRESH_STORAGE_KEY = "zamzam_refresh_token";

    const authModal = document.getElementById("auth-modal");
    const authBackdrop = document.getElementById("auth-backdrop");
    const authHint = document.getElementById("auth-hint");
    const authLoginForm = document.getElementById("auth-login-form");
    const authRegisterForm = document.getElementById("auth-register-form");
    const authPhone = document.getElementById("auth-phone");
    const authPassword = document.getElementById("auth-password");
    const authRegisterName = document.getElementById("auth-register-name");
    const authRegisterPhone = document.getElementById("auth-register-phone");
    const authRegisterPassword = document.getElementById("auth-register-password");
    const authLoginSubmit = document.getElementById("auth-login-submit");
    const authRegisterSubmit = document.getElementById("auth-register-submit");
    const loginButton = document.getElementById("cart-open-topbar");
    const accountFloatingTrigger = document.getElementById("account-floating-trigger");
    const floatingTools = document.querySelector(".floating-tools");
    const checkoutName = document.getElementById("checkout-name");
    const checkoutPhone = document.getElementById("checkout-phone");

    function getSessionToken() {
        return window.sessionStorage.getItem(SESSION_STORAGE_KEY) || "";
    }

    function setSessionToken(value) {
        if (value) {
            window.sessionStorage.setItem(SESSION_STORAGE_KEY, value);
        } else {
            window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
        }
    }

    function setAuthTokens(payload) {
        setSessionToken(payload?.access_token || "");
        if (payload?.refresh_token) {
            window.sessionStorage.setItem(REFRESH_STORAGE_KEY, payload.refresh_token);
        }
    }

    function clearAuthTokens() {
        setSessionToken("");
        window.sessionStorage.removeItem(REFRESH_STORAGE_KEY);
    }

    function setHint(message, isError) {
        if (!authHint) {
            return;
        }
        authHint.textContent = message || "";
        authHint.style.color = isError ? "#9f2d0f" : "";
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

    function closeAuthModal() {
        authModal?.classList.remove("is-open");
        authModal?.setAttribute("aria-hidden", "true");
        authBackdrop?.classList.remove("is-open");
        document.body.classList.remove("admin-open");
    }

    function syncAuthorizedUi(user) {
        const sessionToken = getSessionToken();
        if (loginButton) {
            loginButton.textContent = sessionToken ? "Выйти" : "Войти";
        }
        accountFloatingTrigger?.classList.toggle("is-hidden", !sessionToken);
        if (sessionToken) {
            floatingTools?.classList.remove("is-hidden");
        }

        if (user?.full_name && checkoutName && !checkoutName.value.trim()) {
            checkoutName.value = user.full_name;
        }
        if (user?.phone && checkoutPhone && !checkoutPhone.value.trim()) {
            checkoutPhone.value = user.phone;
            ensurePhonePrefixValue(checkoutPhone);
        }
    }

    async function fetchCurrentUser() {
        const sessionToken = getSessionToken();
        if (!sessionToken) {
            syncAuthorizedUi(null);
            return;
        }

        try {
            const response = await fetch("/api/user/me", {
                headers: { Authorization: `Bearer ${sessionToken}` },
            });
            if (!response.ok) {
                throw new Error("unauthorized");
            }

            const payload = await response.json();
            syncAuthorizedUi(payload.user || null);
        } catch (_) {
            clearAuthTokens();
            syncAuthorizedUi(null);
        }
    }

    async function submitLogin(event) {
        event.preventDefault();
        event.stopImmediatePropagation();

        const phone = ensurePhonePrefixValue(authPhone).trim();
        const password = authPassword?.value.trim() || "";
        if (!phone || !password) {
            setHint("Введите номер телефона и пароль.", true);
            return;
        }

        if (authLoginSubmit) {
            authLoginSubmit.disabled = true;
        }
        setHint("", false);

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

            setAuthTokens(payload);
            closeAuthModal();
            await fetchCurrentUser();
        } catch (error) {
            setHint(error.message || "Не удалось выполнить вход.", true);
        } finally {
            if (authLoginSubmit) {
                authLoginSubmit.disabled = false;
            }
        }
    }

    async function submitRegister(event) {
        event.preventDefault();
        event.stopImmediatePropagation();

        const phone = ensurePhonePrefixValue(authRegisterPhone).trim();
        const password = authRegisterPassword?.value.trim() || "";
        const fullName = authRegisterName?.value.trim() || checkoutName?.value.trim() || null;
        if (!phone || !password) {
            setHint("Введите номер телефона и пароль.", true);
            return;
        }

        if (authRegisterSubmit) {
            authRegisterSubmit.disabled = true;
        }
        setHint("", false);

        try {
            const response = await fetch("/api/auth/register", {
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

            setAuthTokens(payload);
            closeAuthModal();
            await fetchCurrentUser();
        } catch (error) {
            setHint(error.message || "Не удалось завершить регистрацию.", true);
        } finally {
            if (authRegisterSubmit) {
                authRegisterSubmit.disabled = false;
            }
        }
    }

    async function logout(event) {
        event?.preventDefault?.();
        event?.stopImmediatePropagation?.();

        const sessionToken = getSessionToken();
        if (!sessionToken) {
            syncAuthorizedUi(null);
            return;
        }

        try {
            await fetch("/api/auth/logout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh_token: window.sessionStorage.getItem(REFRESH_STORAGE_KEY) || "" }),
            });
        } catch (_) {
        } finally {
            clearAuthTokens();
            syncAuthorizedUi(null);
        }
    }

    authLoginForm?.addEventListener("submit", submitLogin, true);
    authRegisterForm?.addEventListener("submit", submitRegister, true);
    loginButton?.addEventListener("click", (event) => {
        if (!getSessionToken()) {
            return;
        }
        logout(event);
    }, true);

    fetchCurrentUser();
})();
