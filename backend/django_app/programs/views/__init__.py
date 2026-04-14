"""
Programs views package.
"""
from .director_advanced_analytics_views import DirectorAdvancedAnalyticsViewSet
from .director_calendar_views import DirectorCalendarViewSet
from .director_certificate_views import DirectorCertificateViewSet
from .director_lifecycle_views import DirectorCohortLifecycleViewSet
from .director_management_views import (
    DirectorCohortManagementViewSet,
    DirectorMentorManagementViewSet,
    DirectorProgramManagementViewSet,
    DirectorTrackManagementViewSet,
)
from .director_reports_views import DirectorReportsViewSet
from .director_rules_views import DirectorProgramRulesViewSet
from .mentor_assignment_views import MentorAssignmentViewSet
from .program_management_views import ProgramManagementViewSet
from .rules_views import DirectorProgramRuleViewSet
from .standard_views import (
    CertificateViewSet,
    CohortViewSet,
    MentorshipCycleViewSet,
    MilestoneViewSet,
    ModuleViewSet,
    ProgramRuleViewSet,
    ProgramViewSet,
    TrackViewSet,
    director_dashboard,
)

__all__ = [
    'ProgramViewSet', 'TrackViewSet', 'CohortViewSet',
    'ProgramRuleViewSet', 'CertificateViewSet',
    'MilestoneViewSet', 'ModuleViewSet',
    'MentorshipCycleViewSet',
    'DirectorProgramRuleViewSet',
    'ProgramManagementViewSet',
    'DirectorProgramManagementViewSet',
    'DirectorTrackManagementViewSet',
    'DirectorCohortManagementViewSet',
    'DirectorMentorManagementViewSet',
    'DirectorCalendarViewSet',
    'DirectorCohortLifecycleViewSet',
    'DirectorProgramRulesViewSet',
    'DirectorReportsViewSet',
    'DirectorAdvancedAnalyticsViewSet',
    'DirectorCertificateViewSet',
    # 'MentorAssignmentViewSet',  # Temporarily disabled due to syntax errors
    'director_dashboard',
]

