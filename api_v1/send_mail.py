"""
Email helpers for Cloud Attendance System.

Uses Django's built-in email framework (django.core.mail) so any
SMTP provider (Gmail, Outlook, Mailgun, SendGrid free tier, etc.)
works without changing this file — just set the env vars listed in
settings.py / the EB environment.

Required settings (set via environment variables):
  EMAIL_HOST            e.g. smtp.gmail.com
  EMAIL_PORT            e.g. 587
  EMAIL_USE_TLS         True
  EMAIL_HOST_USER       your-account@gmail.com
  EMAIL_HOST_PASSWORD   app-password-or-smtp-password
  DEFAULT_FROM_EMAIL    "CloudAttend <no-reply@yourdomain.com>"

Optional:
  ATTENDANCE_ADMIN_EMAILS  comma-separated list of admin emails to CC
  SITE_URL                 base URL shown in emails, e.g. https://myapp.com
"""

import logging

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives

logger = logging.getLogger(__name__)


def _log_email_config() -> None:
    """Log current email backend config (password masked) — useful for diagnosing issues."""
    backend = getattr(settings, 'EMAIL_BACKEND', '?')
    if 'smtp' in backend.lower():
        host  = getattr(settings, 'EMAIL_HOST', '?')
        port  = getattr(settings, 'EMAIL_PORT', '?')
        user  = getattr(settings, 'EMAIL_HOST_USER', '?')
        pwd   = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        tls   = getattr(settings, 'EMAIL_USE_TLS', '?')
        # Show last 4 chars only so logs are safe to share
        masked = ('*' * max(0, len(pwd) - 4) + pwd[-4:]) if pwd else '(empty)'
        logger.debug(
            "EMAIL_CONFIG | host=%s port=%s tls=%s user=%s password=%s",
            host, port, tls, user, masked,
        )
    else:
        logger.debug(
            "EMAIL_CONFIG | backend=%s — emails will be printed to console, not sent",
            backend,
        )


def _admin_emails() -> list[str]:
    """Return the list of admin CC emails from settings (may be empty)."""
    raw = getattr(settings, 'ATTENDANCE_ADMIN_EMAILS', '') or ''
    return [e.strip() for e in raw.split(',') if e.strip()]


def send_student_welcome(student) -> bool:
    """
    Send a welcome / credentials email to a newly registered student.

    Parameters
    ----------
    student : api_v1.models.Student
        The newly created Student instance.  Must have .email, .first_name,
        .last_name, .student_id attributes.

    Returns
    -------
    bool  True if the email was dispatched without exception, False otherwise.
    """
    _log_email_config()

    if not student.email:
        logger.warning(
            "EMAIL_SKIP | student_id=%s reason=no_email_address",
            student.student_id,
        )
        return False

    logger.info(
        "EMAIL_ATTEMPT | student_id=%s to=%s",
        student.student_id, student.email,
    )
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    password  = f"Student@{student.student_id[-4:]}"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'noreply@cloudattend.local')

    subject = "Welcome to Cloud Attendance System — Your Login Details"

    body_text = (
        f"Hi {student.first_name} {student.last_name},\n\n"
        f"You have been registered in the Cloud Attendance System.\n\n"
        f"Your login credentials:\n"
        f"  URL      : {site_url}\n"
        f"  Username : {student.student_id[:30]}\n"
        f"  Password : {password}\n\n"
        f"Please change your password after your first login.\n\n"
        f"Best regards,\n"
        f"CloudAttend Administration"
    )

    body_html = f"""
    <html>
    <body style="font-family:Inter,Arial,sans-serif;background:#f1f5f9;padding:2rem;">
      <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;padding:2rem;box-shadow:0 2px 8px rgba(0,0,0,.08);">
        <div style="text-align:center;margin-bottom:1.5rem;">
          <div style="display:inline-block;background:#6366f1;color:#fff;border-radius:10px;padding:.6rem 1.2rem;font-size:1.1rem;font-weight:700;">
            &#9729; CloudAttend
          </div>
        </div>
        <h2 style="color:#0f172a;margin:0 0 .5rem;">Welcome, {student.first_name}!</h2>
        <p style="color:#475569;margin:0 0 1.5rem;">
          You have been registered in the Cloud Attendance System. Here are your login details:
        </p>
        <table style="width:100%;border-collapse:collapse;margin-bottom:1.5rem;">
          <tr>
            <td style="padding:.5rem;color:#94a3b8;font-size:.85rem;width:90px;">URL</td>
            <td style="padding:.5rem;"><a href="{site_url}" style="color:#6366f1;">{site_url}</a></td>
          </tr>
          <tr style="background:#f8fafc;">
            <td style="padding:.5rem;color:#94a3b8;font-size:.85rem;">Username</td>
            <td style="padding:.5rem;font-family:monospace;font-weight:600;">{student.student_id[:30]}</td>
          </tr>
          <tr>
            <td style="padding:.5rem;color:#94a3b8;font-size:.85rem;">Password</td>
            <td style="padding:.5rem;font-family:monospace;font-weight:600;">{password}</td>
          </tr>
        </table>
        <p style="color:#94a3b8;font-size:.8rem;margin:0;">
          Please change your password after your first login.<br>
          If you have any questions, contact your administrator.
        </p>
      </div>
    </body>
    </html>
    """

    recipients = [student.email]
    cc = _admin_emails()

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=body_text,
            from_email=from_email,
            to=recipients,
            cc=cc,
        )
        msg.attach_alternative(body_html, "text/html")
        msg.send(fail_silently=False)
        logger.info(
            "Welcome email sent to %s (cc: %s)", student.email, cc or "none"
        )
        return True
    except Exception as exc:
        logger.error(
            "Failed to send welcome email to %s: %s", student.email, exc
        )
        return False


def send_attendance_summary(student, records: list) -> bool:
    """
    Send a weekly/custom attendance summary to a student.

    Parameters
    ----------
    student : api_v1.models.Student
    records : list of api_v1.models.Attendance
        Attendance records to include in the summary.

    Returns
    -------
    bool
    """
    if not student.email:
        return False

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@cloudattend.local')
    subject = f"Attendance Summary — {student.full_name}"

    rows = "\n".join(
        f"  {r.lecture_date}  {r.subject.title:<30}  {r.status}"
        for r in records
    )
    body_text = (
        f"Hi {student.first_name},\n\n"
        f"Here is your recent attendance summary:\n\n"
        f"{'Date':<12}  {'Subject':<30}  Status\n"
        f"{'-'*60}\n"
        f"{rows}\n\n"
        f"Best regards,\nCloudAttend Administration"
    )

    try:
        send_mail(
            subject=subject,
            message=body_text,
            from_email=from_email,
            recipient_list=[student.email],
            fail_silently=False,
        )
        logger.info("Attendance summary sent to %s", student.email)
        return True
    except Exception as exc:
        logger.error(
            "Failed to send attendance summary to %s: %s", student.email, exc
        )
        return False
