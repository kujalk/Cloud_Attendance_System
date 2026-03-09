import logging

from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Student

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Student)
def create_student_user_account(sender, instance, created, **kwargs):
    """
    When a new Student is saved and has no linked User account,
    automatically create one, add it to the 'Student' group,
    and send a welcome email with login credentials.
    Default password is Student@<last4 of student_id>.
    """
    if not (created and instance.user is None):
        return

    student_id = instance.student_id
    username = student_id[:30]
    password = f"Student@{student_id[-4:]}"

    logger.info(
        "SIGNAL_CREATE_USER | student_id=%s username=%s email=%s",
        student_id, username, instance.email,
    )

    user = User.objects.create_user(
        username=username,
        email=instance.email,
        password=password,
        first_name=instance.first_name,
        last_name=instance.last_name,
    )
    logger.debug("SIGNAL_USER_CREATED | user_id=%s username=%s", user.pk, user.username)

    # Ensure the Student group exists and assign
    student_group, group_created = Group.objects.get_or_create(name='Student')
    if group_created:
        logger.info("SIGNAL_GROUP_CREATED | name=Student")
    student_group.user_set.add(user)
    logger.debug("SIGNAL_GROUP_ASSIGNED | user=%s group=Student", user.username)

    # Link user back to student (use update to avoid re-triggering signal)
    Student.objects.filter(pk=instance.pk).update(user=user)
    instance.user = user
    logger.info("SIGNAL_STUDENT_LINKED | student_id=%s user_id=%s", student_id, user.pk)

    # Send welcome email — non-blocking; errors are logged, not raised
    logger.info("SIGNAL_EMAIL_TRIGGER | student_id=%s to=%s", student_id, instance.email)
    try:
        from .send_mail import send_student_welcome
        ok = send_student_welcome(instance)
        if ok:
            logger.info("SIGNAL_EMAIL_SENT | student_id=%s to=%s", student_id, instance.email)
        else:
            logger.warning(
                "SIGNAL_EMAIL_SKIPPED | student_id=%s to=%s "
                "(no email address or send returned False)",
                student_id, instance.email,
            )
    except Exception as exc:
        logger.error(
            "SIGNAL_EMAIL_FAILED | student_id=%s to=%s error=%s",
            student_id, instance.email, exc,
        )
