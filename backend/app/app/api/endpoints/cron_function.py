from fastapi import APIRouter, Depends, Form, File, UploadFile
from app.models import *
from app.core.security import *
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List

router = APIRouter()


@router.post("/invite_mails")
async def invite_mails(db: Session = Depends(deps.get_db)):
    get_notification = (
        db.query(NotificationSmsEmail).filter(NotificationSmsEmail.status == 0).all()
    )
    for notify in get_notification:
        if notify.type == 1:  # SMS
            mobile_no = (
                str(notify.mobile_no_email_id).split(",")
                if notify.mobile_no_email_id
                else []
            )
            for mobile in mobile_no:
                if mobile != "":
                    send_sms = sendSMS(notify.mobile_no_email_id, notify.message)

        elif notify.type == 2:  # Mail
            mails = (
                str(notify.mobile_no_email_id).split(",")
                if notify.mobile_no_email_id
                else []
            )
            for mail in mails:
                if mails != "":
                    send_mail = await send_email(
                        db, mail, notify.subject, notify.message
                    )

        else:
            pass
