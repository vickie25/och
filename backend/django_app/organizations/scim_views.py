import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from users.models import User

from .institutional_models import InstitutionalContract
from .institutional_service import InstitutionalBillingService
from .scim_models import InstitutionalSCIMEvent, InstitutionalSCIMToken, InstitutionalSCIMUser

logger = logging.getLogger(__name__)


def _get_bearer_token(request):
    auth = request.META.get('HTTP_AUTHORIZATION', '') or ''
    if not auth.lower().startswith('bearer '):
        return None
    return auth.split(' ', 1)[1].strip()


def _authenticate_scim(request, contract):
    raw = _get_bearer_token(request)
    if not raw:
        return False
    token_obj = getattr(contract, 'scim_token', None)
    if not token_obj or not token_obj.is_active:
        return False
    candidate = InstitutionalSCIMToken.hash_token(raw)
    ok = constant_time_compare(candidate, token_obj.token_hash)
    if ok:
        token_obj.last_used_at = timezone.now()
        token_obj.save(update_fields=['last_used_at'])
    return ok


def _scim_user_resource(mapping: InstitutionalSCIMUser):
    u = mapping.user
    primary_email = (u.email or '').strip().lower()
    return {
        'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
        'id': mapping.external_id,
        'externalId': mapping.external_id,
        'userName': primary_email,
        'active': bool(mapping.is_active and u.is_active and u.account_status == 'active'),
        'name': {
            'givenName': u.first_name or '',
            'familyName': u.last_name or '',
        },
        'emails': [{'value': primary_email, 'primary': True}],
        'meta': {
            'resourceType': 'User',
        },
    }


def _extract_scim_profile(payload):
    username = (payload.get('userName') or '').strip().lower()
    emails = payload.get('emails') or []
    email = ''
    if username and '@' in username:
        email = username
    if not email and isinstance(emails, list) and emails:
        primary = next((e for e in emails if isinstance(e, dict) and e.get('primary')), None)
        candidate = primary or next((e for e in emails if isinstance(e, dict) and e.get('value')), None)
        if candidate:
            email = (candidate.get('value') or '').strip().lower()

    name = payload.get('name') or {}
    first = (name.get('givenName') or '').strip()
    last = (name.get('familyName') or '').strip()
    active = payload.get('active', True)
    return email, first, last, bool(active)


@api_view(['GET'])
@permission_classes([AllowAny])
def scim_service_provider_config(request, contract_id):
    contract = get_object_or_404(InstitutionalContract, id=contract_id)
    if not _authenticate_scim(request, contract):
        return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(
        {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig'],
            'patch': {'supported': True},
            'bulk': {'supported': False},
            'filter': {'supported': True, 'maxResults': 200},
            'changePassword': {'supported': False},
            'sort': {'supported': False},
            'etag': {'supported': False},
            'authenticationSchemes': [
                {
                    'type': 'oauthbearertoken',
                    'name': 'OAuth Bearer Token',
                    'description': 'Bearer token authentication',
                    'specUri': 'https://www.rfc-editor.org/rfc/rfc6750',
                    'primary': True,
                }
            ],
        }
    )


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def scim_users(request, contract_id):
    contract = get_object_or_404(InstitutionalContract, id=contract_id)
    if not _authenticate_scim(request, contract):
        return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        # Basic list; supports minimal filter by userName eq "email"
        q = contract.scim_users.select_related('user').all()
        flt = request.query_params.get('filter') or ''
        if 'userName' in flt and 'eq' in flt:
            # naive parse: userName eq "x"
            parts = flt.split('eq', 1)
            rhs = parts[1].strip().strip('"').strip("'")
            rhs = rhs.lower()
            q = q.filter(user__email__iexact=rhs)

        resources = [_scim_user_resource(m) for m in q[:200]]
        return Response(
            {
                'schemas': ['urn:ietf:params:scim:api:messages:2.0:ListResponse'],
                'totalResults': len(resources),
                'startIndex': 1,
                'itemsPerPage': len(resources),
                'Resources': resources,
            }
        )

    # POST create
    payload = request.data or {}
    external_id = (payload.get('externalId') or payload.get('id') or '').strip() or None
    if not external_id:
        return Response({'detail': 'externalId is required'}, status=status.HTTP_400_BAD_REQUEST)

    email, first, last, active = _extract_scim_profile(payload)
    if not email:
        return Response({'detail': 'userName or emails.value is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'username': email, 'first_name': first, 'last_name': last, 'is_active': True, 'account_status': 'active', 'email_verified': True},
            )
            if not created:
                if first:
                    user.first_name = first
                if last:
                    user.last_name = last
                if user.account_status != 'active':
                    user.account_status = 'active'
                if not user.is_active:
                    user.is_active = True
                user.email_verified = True
                user.save()

            mapping, _ = InstitutionalSCIMUser.objects.update_or_create(
                contract=contract,
                external_id=external_id,
                defaults={'user': user, 'is_active': active, 'raw_profile': payload},
            )

            if active:
                try:
                    InstitutionalBillingService.enroll_student(contract.id, user.id, enrollment_type='scim', created_by=None)
                except Exception:
                    # Seat constraints or contract state may prevent enrollment; keep mapping.
                    pass
            else:
                # Deactivate access in this contract scope
                InstitutionalStudent = contract.enrolled_students.model
                InstitutionalStudent.objects.filter(contract=contract, user=user, is_active=True).update(is_active=False)

            InstitutionalSCIMEvent.objects.create(contract=contract, external_id=external_id, event_type='create', success=True, payload=payload)
            return Response(_scim_user_resource(mapping), status=status.HTTP_201_CREATED)
    except Exception as e:
        InstitutionalSCIMEvent.objects.create(contract=contract, external_id=external_id, event_type='create', success=False, error=str(e), payload=payload)
        return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PATCH', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def scim_user_detail(request, contract_id, external_id):
    contract = get_object_or_404(InstitutionalContract, id=contract_id)
    if not _authenticate_scim(request, contract):
        return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    mapping = get_object_or_404(InstitutionalSCIMUser.objects.select_related('user'), contract=contract, external_id=external_id)

    if request.method == 'GET':
        return Response(_scim_user_resource(mapping))

    if request.method in ('PATCH', 'PUT'):
        payload = request.data or {}
        email, first, last, active = _extract_scim_profile(payload)
        try:
            with transaction.atomic():
                u = mapping.user
                if email and email != (u.email or '').lower():
                    # Keep local email immutable for safety; store in raw_profile only.
                    pass
                if first:
                    u.first_name = first
                if last:
                    u.last_name = last
                if active:
                    if u.account_status != 'active':
                        u.account_status = 'active'
                    if not u.is_active:
                        u.is_active = True
                u.save()

                mapping.is_active = active
                mapping.raw_profile = payload or mapping.raw_profile
                mapping.save(update_fields=['is_active', 'raw_profile', 'updated_at'])

                if active:
                    try:
                        InstitutionalBillingService.enroll_student(contract.id, u.id, enrollment_type='scim', created_by=None)
                    except Exception:
                        pass
                    evt = 'reactivate' if mapping.is_active else 'update'
                else:
                    InstitutionalStudent = contract.enrolled_students.model
                    InstitutionalStudent.objects.filter(contract=contract, user=u, is_active=True).update(is_active=False)
                    evt = 'deactivate'

                InstitutionalSCIMEvent.objects.create(contract=contract, external_id=external_id, event_type=evt, success=True, payload=payload)
                return Response(_scim_user_resource(mapping))
        except Exception as e:
            InstitutionalSCIMEvent.objects.create(contract=contract, external_id=external_id, event_type='update', success=False, error=str(e), payload=payload)
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # DELETE => deprovision
    try:
        with transaction.atomic():
            mapping.is_active = False
            mapping.save(update_fields=['is_active', 'updated_at'])
            u = mapping.user
            InstitutionalStudent = contract.enrolled_students.model
            InstitutionalStudent.objects.filter(contract=contract, user=u, is_active=True).update(is_active=False)
            InstitutionalSCIMEvent.objects.create(contract=contract, external_id=external_id, event_type='deactivate', success=True, payload={})
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        InstitutionalSCIMEvent.objects.create(contract=contract, external_id=external_id, event_type='deactivate', success=False, error=str(e), payload={})
        return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

