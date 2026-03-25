"""
Marketplace utility functions
"""

from .models import Employer


def get_employer_for_user(user):
    """
    Return marketplace Employer for this user, creating one when allowed (sponsor or employer role).
    """
    try:
        if getattr(user, 'employer_profile', None):
            return user.employer_profile
    except Employer.DoesNotExist:
        pass

    from users.models import UserRole

    has_marketplace_role = user.user_roles.filter(
        role__name__in=['employer', 'sponsor_admin', 'sponsor'],
        is_active=True,
    ).exists()
    if not has_marketplace_role:
        return None

    company_name = user.get_full_name() or (user.email.split('@')[0] if user.email else 'Company')
    org = getattr(user, 'org_id', None)
    if org is not None:
        try:
            company_name = org.name or company_name
        except Exception:
            pass

    employer, _created = Employer.objects.get_or_create(
        user=user,
        defaults={
            'company_name': company_name[:255],
            'description': 'Employer marketplace profile (auto-created)',
        },
    )
    return employer

