from django.db.models import Sum
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
    }