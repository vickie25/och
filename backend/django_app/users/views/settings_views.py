"""
User Settings API Views
Handles user preferences and settings like portfolio visibility
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_settings(request):
    """
    GET /api/v1/settings
    PATCH /api/v1/settings

    Get or update user settings (portfolio visibility, etc.)
    """
    user = request.user

    if request.method == 'GET':
        # Get user settings from user.metadata JSONField
        settings = {}
        community_profile = {}

        # Get from user.metadata (now that we've added the field)
        if user.metadata and isinstance(user.metadata, dict):
            settings = user.metadata.get('settings', {})
            community_profile = user.metadata.get('community_profile', {})

        # Return defaults if not set
        default_settings = {
            'portfolioVisibility': 'private',  # Default to private
            'communityDisplayName': None,
            'country': getattr(user, 'country', None),
            'timezone': getattr(user, 'timezone', 'UTC'),
        }

        if community_profile and isinstance(community_profile, dict):
            default_settings['communityDisplayName'] = community_profile.get('display_name')

        # Merge with defaults
        result = {**default_settings, **settings}

        return Response(result, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        # Update user settings
        updates = request.data

        # Get current settings from metadata
        current_settings = {}
        if user.metadata and isinstance(user.metadata, dict) and 'settings' in user.metadata:
            current_settings = user.metadata['settings']

        # Merge updates
        updated_settings = {**current_settings, **updates}

        community_display_name = updates.get('communityDisplayName', None)
        country = updates.get('country', None)
        tz = updates.get('timezone', None)

        # Validate portfolioVisibility
        if 'portfolioVisibility' in updates:
            valid_values = ['private', 'public', 'unlisted']
            if updates['portfolioVisibility'] not in valid_values:
                return Response(
                    {'detail': f'portfolioVisibility must be one of: {", ".join(valid_values)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if 'country' in updates:
            if country is not None and not isinstance(country, str):
                return Response(
                    {'detail': 'country must be a string (ISO 3166-1 alpha-2) or null'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if isinstance(country, str):
                c = country.strip().upper()
                if c and len(c) != 2:
                    return Response(
                        {'detail': 'country must be a 2-letter ISO code (e.g. KE)'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        if 'timezone' in updates:
            if tz is not None and not isinstance(tz, str):
                return Response(
                    {'detail': 'timezone must be a string or null'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if isinstance(tz, str) and len(tz.strip()) > 50:
                return Response(
                    {'detail': 'timezone is too long (max 50 characters)'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Save to user.metadata
        try:
            # Ensure metadata is a dict
            if not user.metadata or not isinstance(user.metadata, dict):
                user.metadata = {}

            user.metadata['settings'] = updated_settings

            if 'communityDisplayName' in updates:
                if community_display_name is not None and not isinstance(community_display_name, str):
                    return Response(
                        {'detail': 'communityDisplayName must be a string or null'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if isinstance(community_display_name, str) and len(community_display_name.strip()) > 80:
                    return Response(
                        {'detail': 'communityDisplayName is too long (max 80 characters)'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                profile = user.metadata.get('community_profile')
                if not profile or not isinstance(profile, dict):
                    profile = {}
                profile['display_name'] = community_display_name.strip() if isinstance(community_display_name, str) else None
                user.metadata['community_profile'] = profile

            update_fields = ['metadata']
            if 'country' in updates:
                user.country = country.strip().upper() if isinstance(country, str) and country.strip() else None
                update_fields.append('country')
            if 'timezone' in updates:
                user.timezone = tz.strip() if isinstance(tz, str) and tz.strip() else 'UTC'
                update_fields.append('timezone')

            user.save(update_fields=update_fields)
            logger.info(f"Updated user settings for user {user.id}")
        except Exception as e:
            logger.error(f"Error saving user settings: {e}", exc_info=True)
            return Response(
                {'detail': f'Failed to save settings: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        result = dict(updated_settings)
        if 'communityDisplayName' in updates:
            result['communityDisplayName'] = user.metadata.get('community_profile', {}).get('display_name')
        if 'country' in updates:
            result['country'] = user.country
        if 'timezone' in updates:
            result['timezone'] = user.timezone
        return Response(result, status=status.HTTP_200_OK)
