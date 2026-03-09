def user_role(request):
    """Expose user role to all templates."""
    is_student = (
        request.user.is_authenticated
        and request.user.groups.filter(name='Student').exists()
    )
    return {'user_is_student': is_student}
