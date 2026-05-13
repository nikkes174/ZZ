import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.auth_recovery.email_sender import EmailDeliveryError
from backend.auth_recovery.recovery_service import PasswordRecoveryService
from dependency import get_recovery_service

templates = Jinja2Templates(directory="backend/templates")
logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/recovery",
    tags=["Password recovery"],
)


@router.post("/restore", response_class=HTMLResponse)
async def restore_password(
    request: Request,
    email: str = Form(...),
    service: PasswordRecoveryService = Depends(get_recovery_service),
):
    try:
        await service.request_recovery(email)
    except EmailDeliveryError as e:
        logger.warning(
            "Не удалось отправить письмо для восстановления пароля: %s",
            type(e.__cause__).__name__ if e.__cause__ else type(e).__name__,
        )
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": (
                    "Не удалось отправить письмо. Выключите VPN или "
                    "проверьте подключение к интернету и попробуйте ещё раз."
                ),
                "open_restore": True,
            },
        )

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "success": "Если email зарегистрирован, мы отправили код восстановления",
            "open_restore_confirm": True,
        },
    )


@router.post("/restore/confirm", response_class=HTMLResponse)
async def confirm_restore(
    request: Request,
    token: str = Form(..., min_length=1),
    password: str = Form(..., min_length=8),
    service: PasswordRecoveryService = Depends(get_recovery_service),
):
    ok = await service.confirm_recovery(token, password)

    if not ok:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Неверный или просроченный код восстановления",
            },
        )

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "success": "Пароль успешно изменён",
        },
    )
