from django.db.models import Sum
from ambassador_registration.models import Ambassador
from registration.models import Form_Participant_Phase_1
from .models import HackathonTeam_Phase01

def get_phase01_tab_counts() -> dict:
    """Returns live registration counts for the Phase 1 Response Table folder tabs."""
    hackathon_totals = HackathonTeam_Phase01.objects.aggregate(
        total_people=Sum('team_size')
    )
    return {
        'participants_count': Form_Participant_Phase_1.objects.count(),
        'hackathon_teams_count': HackathonTeam_Phase01.objects.count(),
        'hackathon_people_count': hackathon_totals['total_people'] or 0,
        'ambassadors_count': Ambassador.objects.count(),
    }


def get_phase02_tab_counts() -> dict:
    """Returns live registration counts for the Phase 2 Response Table folder tabs."""
    from registration.models import Form_Participant_Phase_2
    from .models import HackathonTeam_Phase02

    hackathon_totals = HackathonTeam_Phase02.objects.aggregate(
        total_people=Sum('team_size')
    )
    return {
        'participants_count': Form_Participant_Phase_2.objects.count(),
        'hackathon_teams_count': HackathonTeam_Phase02.objects.count(),
        'hackathon_people_count': hackathon_totals['total_people'] or 0,
    }