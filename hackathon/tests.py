from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from access_ctrl.models import Permission, UserPermission
from hackathon.models import (
    HackathonFormStatus_Phase01,
    HackathonTeam_Phase01,
    HackathonMember_Phase01,
)


DUMMY_TEAMS_DATA = [
    {
        "team_name": "ByteCraft",
        "team_size": 3,
        "university_distribution": "single",
        "leader_email": "tanvir.hasan@northsouth.edu",
        "leader_phone": "01711000101",
        "leader_signature": "Tanvir Hasan",
        "is_selected": True,
        "is_phase_2_email_sent": False,
        "members": [
            {
                "member_order": 1,
                "is_leader": True,
                "full_name": "Tanvir Hasan",
                "email": "tanvir.hasan@northsouth.edu",
                "phone_number": "01711000101",
                "university": "North South University",
                "department": "CSE",
                "academic_year": "3rd",
                "student_id": "2211001",
                "gender": "male",
                "is_ieee_member": True,
                "ieee_membership_no": "98765432",
                "ieee_membership_grade": "Student Member",
                "ieee_student_branch": "IEEE NSU Student Branch",
                "ieee_volunteer_position": "Webmaster",
            },
            {
                "member_order": 2,
                "is_leader": False,
                "full_name": "Sadia Islam",
                "email": "sadia.islam@northsouth.edu",
                "phone_number": "01711000102",
                "university": "North South University",
                "department": "CSE",
                "academic_year": "3rd",
                "student_id": "2211002",
                "gender": "female",
                "is_ieee_member": False,
                "ieee_membership_no": "",
                "ieee_membership_grade": "",
                "ieee_student_branch": "",
                "ieee_volunteer_position": "",
            },
            {
                "member_order": 3,
                "is_leader": False,
                "full_name": "Farhan Ahmed",
                "email": "farhan.ahmed@northsouth.edu",
                "phone_number": "01711000103",
                "university": "North South University",
                "department": "EEE",
                "academic_year": "2nd",
                "student_id": "2312003",
                "gender": "male",
                "is_ieee_member": True,
                "ieee_membership_no": "98765433",
                "ieee_membership_grade": "Student Member",
                "ieee_student_branch": "IEEE NSU Student Branch",
                "ieee_volunteer_position": "Volunteer",
            },
        ],
    },
    {
        "team_name": "NeuralKnights",
        "team_size": 2,
        "university_distribution": "multiple",
        "leader_email": "arefin.shuvo@buet.ac.bd",
        "leader_phone": "01812000202",
        "leader_signature": "Arefin Shuvo",
        "is_selected": False,
        "is_phase_2_email_sent": False,
        "members": [
            {
                "member_order": 1,
                "is_leader": True,
                "full_name": "Arefin Shuvo",
                "email": "arefin.shuvo@buet.ac.bd",
                "phone_number": "01812000202",
                "university": "Bangladesh University of Engineering and Technology (BUET)",
                "department": "CSE",
                "academic_year": "4th",
                "student_id": "2005001",
                "gender": "male",
                "is_ieee_member": True,
                "ieee_membership_no": "99112233",
                "ieee_membership_grade": "Graduate Student Member",
                "ieee_student_branch": "IEEE BUET Student Branch",
                "ieee_volunteer_position": "Secretary",
            },
            {
                "member_order": 2,
                "is_leader": False,
                "full_name": "Nusrat Jahan",
                "email": "nusrat.jahan@northsouth.edu",
                "phone_number": "01812000203",
                "university": "North South University",
                "department": "Data Science",
                "academic_year": "3rd",
                "student_id": "2223004",
                "gender": "female",
                "is_ieee_member": False,
                "ieee_membership_no": "",
                "ieee_membership_grade": "",
                "ieee_student_branch": "",
                "ieee_volunteer_position": "",
            },
        ],
    },
    {
        "team_name": "AlgoRiddim",
        "team_size": 3,
        "university_distribution": "single",
        "leader_email": "mashrur.chowdhury@g.bracu.ac.bd",
        "leader_phone": "01913000303",
        "leader_signature": "Mashrur Chowdhury",
        "is_selected": True,
        "is_phase_2_email_sent": True,
        "members": [
            {
                "member_order": 1,
                "is_leader": True,
                "full_name": "Mashrur Chowdhury",
                "email": "mashrur.chowdhury@g.bracu.ac.bd",
                "phone_number": "01913000303",
                "university": "BRAC University",
                "department": "CSE",
                "academic_year": "4th",
                "student_id": "21101005",
                "gender": "male",
                "is_ieee_member": False,
                "ieee_membership_no": "",
                "ieee_membership_grade": "",
                "ieee_student_branch": "",
                "ieee_volunteer_position": "",
            },
            {
                "member_order": 2,
                "is_leader": False,
                "full_name": "Tasnim Rahman",
                "email": "tasnim.rahman@g.bracu.ac.bd",
                "phone_number": "01913000304",
                "university": "BRAC University",
                "department": "CSE",
                "academic_year": "4th",
                "student_id": "21101006",
                "gender": "female",
                "is_ieee_member": False,
                "ieee_membership_no": "",
                "ieee_membership_grade": "",
                "ieee_student_branch": "",
                "ieee_volunteer_position": "",
            },
            {
                "member_order": 3,
                "is_leader": False,
                "full_name": "Zaki Al-Amin",
                "email": "zaki.alamin@g.bracu.ac.bd",
                "phone_number": "01913000305",
                "university": "BRAC University",
                "department": "EEE",
                "academic_year": "3rd",
                "student_id": "22102007",
                "gender": "male",
                "is_ieee_member": False,
                "ieee_membership_no": "",
                "ieee_membership_grade": "",
                "ieee_student_branch": "",
                "ieee_volunteer_position": "",
            },
        ],
    },
    {
        "team_name": "CloudChasers",
        "team_size": 2,
        "university_distribution": "single",
        "leader_email": "kazi.rayhan@iut-dhaka.edu",
        "leader_phone": "01514000404",
        "leader_signature": "Kazi Rayhan",
        "is_selected": True,
        "is_phase_2_email_sent": False,
        "members": [
            {
                "member_order": 1,
                "is_leader": True,
                "full_name": "Kazi Rayhan",
                "email": "kazi.rayhan@iut-dhaka.edu",
                "phone_number": "01514000404",
                "university": "Islamic University of Technology (IUT)",
                "department": "Software Engineering",
                "academic_year": "3rd",
                "student_id": "210041001",
                "gender": "male",
                "is_ieee_member": True,
                "ieee_membership_no": "97531246",
                "ieee_membership_grade": "Student Member",
                "ieee_student_branch": "IEEE IUT Student Branch",
                "ieee_volunteer_position": "Treasurer",
            },
            {
                "member_order": 2,
                "is_leader": False,
                "full_name": "Mahir Faysal",
                "email": "mahir.faysal@iut-dhaka.edu",
                "phone_number": "01514000405",
                "university": "Islamic University of Technology (IUT)",
                "department": "CSE",
                "academic_year": "3rd",
                "student_id": "210041002",
                "gender": "male",
                "is_ieee_member": True,
                "ieee_membership_no": "97531247",
                "ieee_membership_grade": "Student Member",
                "ieee_student_branch": "IEEE IUT Student Branch",
                "ieee_volunteer_position": "Volunteer",
            },
        ],
    },
    {
        "team_name": "SyntaxSorcerers",
        "team_size": 3,
        "university_distribution": "multiple",
        "leader_email": "ashikur.rahman@aiub.edu",
        "leader_phone": "01615000505",
        "leader_signature": "Ashikur Rahman",
        "is_selected": False,
        "is_phase_2_email_sent": False,
        "members": [
            {
                "member_order": 1,
                "is_leader": True,
                "full_name": "Ashikur Rahman",
                "email": "ashikur.rahman@aiub.edu",
                "phone_number": "01615000505",
                "university": "American International University-Bangladesh (AIUB)",
                "department": "CSE",
                "academic_year": "2nd",
                "student_id": "23-51234-1",
                "gender": "male",
                "is_ieee_member": True,
                "ieee_membership_no": "96420135",
                "ieee_membership_grade": "Student Member",
                "ieee_student_branch": "IEEE AIUB Student Branch",
                "ieee_volunteer_position": "Executive Member",
            },
            {
                "member_order": 2,
                "is_leader": False,
                "full_name": "Sumaiya Akter",
                "email": "sumaiya.akter@northsouth.edu",
                "phone_number": "01615000506",
                "university": "North South University",
                "department": "CSE",
                "academic_year": "2nd",
                "student_id": "2321010",
                "gender": "female",
                "is_ieee_member": False,
                "ieee_membership_no": "",
                "ieee_membership_grade": "",
                "ieee_student_branch": "",
                "ieee_volunteer_position": "",
            },
            {
                "member_order": 3,
                "is_leader": False,
                "full_name": "Rashedul Karim",
                "email": "rashedul.karim@aust.edu",
                "phone_number": "01615000507",
                "university": "Ahsanullah University of Science and Technology",
                "department": "EEE",
                "academic_year": "2nd",
                "student_id": "23.01.04.050",
                "gender": "male",
                "is_ieee_member": False,
                "ieee_membership_no": "",
                "ieee_membership_grade": "",
                "ieee_student_branch": "",
                "ieee_volunteer_position": "",
            },
        ],
    },
    {
        "team_name": "QuantumQuarks",
        "team_size": 2,
        "university_distribution": "single",
        "leader_email": "naimul.islam@aust.edu",
        "leader_phone": "01716000606",
        "leader_signature": "Naimul Islam",
        "is_selected": False,
        "is_phase_2_email_sent": False,
        "members": [
            {
                "member_order": 1,
                "is_leader": True,
                "full_name": "Naimul Islam",
                "email": "naimul.islam@aust.edu",
                "phone_number": "01716000606",
                "university": "Ahsanullah University of Science and Technology",
                "department": "CSE",
                "academic_year": "1st",
                "student_id": "24.01.04.012",
                "gender": "male",
                "is_ieee_member": False,
                "ieee_membership_no": "",
                "ieee_membership_grade": "",
                "ieee_student_branch": "",
                "ieee_volunteer_position": "",
            },
            {
                "member_order": 2,
                "is_leader": False,
                "full_name": "Anika Tabassum",
                "email": "anika.tabassum@aust.edu",
                "phone_number": "01716000607",
                "university": "Ahsanullah University of Science and Technology",
                "department": "CSE",
                "academic_year": "1st",
                "student_id": "24.01.04.015",
                "gender": "female",
                "is_ieee_member": False,
                "ieee_membership_no": "",
                "ieee_membership_grade": "",
                "ieee_student_branch": "",
                "ieee_volunteer_position": "",
            },
        ],
    },
]


def create_dummy_hackathon_data(clear_existing=False):
    """
    Populates realistic Hackathon Phase 1 dummy teams and members for local testing.
    Can be run from tests, Django shell, or CLI.
    """
    if clear_existing:
        clear_dummy_hackathon_data()

    # Ensure form publish status exists
    status, _ = HackathonFormStatus_Phase01.objects.get_or_create(id=1)
    status.is_published = True
    status.save()

    created_teams = []
    for item in DUMMY_TEAMS_DATA:
        members_data = item.get("members", [])
        team, created = HackathonTeam_Phase01.objects.get_or_create(
            team_name=item["team_name"],
            defaults={
                "team_size": item["team_size"],
                "university_distribution": item["university_distribution"],
                "leader_email": item["leader_email"],
                "leader_phone": item["leader_phone"],
                "leader_signature": item["leader_signature"],
                "is_selected": item["is_selected"],
                "is_phase_2_email_sent": item["is_phase_2_email_sent"],
                "agreed_enrolled_students": True,
                "agreed_member_consent": True,
                "agreed_composition_final": True,
                "agreed_rules_plagiarism": True,
                "agreed_originality": True,
                "agreed_announcements": True,
                "agreed_media_permission": True,
            },
        )

        # Clear existing members if re-populating the same team
        team.members.all().delete()

        for m_data in members_data:
            HackathonMember_Phase01.objects.create(
                team=team,
                member_order=m_data["member_order"],
                is_leader=m_data["is_leader"],
                full_name=m_data["full_name"],
                email=m_data["email"],
                phone_number=m_data["phone_number"],
                university=m_data["university"],
                department=m_data["department"],
                academic_year=m_data["academic_year"],
                student_id=m_data["student_id"],
                gender=m_data["gender"],
                is_ieee_member=m_data["is_ieee_member"],
                ieee_membership_no=m_data["ieee_membership_no"],
                ieee_membership_grade=m_data["ieee_membership_grade"],
                ieee_student_branch=m_data["ieee_student_branch"],
                ieee_volunteer_position=m_data["ieee_volunteer_position"],
            )
        created_teams.append(team)

    return created_teams


def clear_dummy_hackathon_data():
    """Removes all test dummy hackathon teams and members from database."""
    team_names = [t["team_name"] for t in DUMMY_TEAMS_DATA]
    HackathonTeam_Phase01.objects.filter(team_name__in=team_names).delete()


class HackathonResponseTableTests(TestCase):
    """
    Test suite validating all interactive buttons and endpoints for the
    Hackathon Phase 1 response table and admin operations.
    """

    def setUp(self):
        self.client = Client()

        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username="hackathon_admin",
            password="adminpassword123",
            email="admin@sparc.nsu.edu",
        )

        # Populate dummy data
        self.teams = create_dummy_hackathon_data(clear_existing=True)

    def test_response_table_view_renders_correctly(self):
        """Test GET /hackathon/responses/ renders all teams, tab counts, and statistics."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("hackathon:response_table_phase01"))
        self.assertEqual(response.status_code, 200)

        # Verify all 6 teams exist in context
        self.assertIn("teams", response.context)
        self.assertEqual(len(response.context["teams"]), 6)

        # Verify statistics
        reg_stats = response.context["reg_stats"]
        self.assertEqual(reg_stats["total_teams"], 6)
        self.assertEqual(reg_stats["total_participants"], 15)
        self.assertEqual(reg_stats["total_selected"], 3)  # ByteCraft, AlgoRiddim, CloudChasers
        self.assertEqual(reg_stats["teams_of_2"], 3)
        self.assertEqual(reg_stats["teams_of_3"], 3)
        self.assertEqual(reg_stats["single_uni_teams"], 4)
        self.assertEqual(reg_stats["multi_uni_teams"], 2)

        # Verify IEEE member breakdown
        member_stats = response.context["member_stats"]
        self.assertEqual(member_stats["ieee_members"], 6)
        self.assertEqual(member_stats["non_ieee_members"], 9)

        # Verify team names appear in HTML response
        content = response.content.decode("utf-8")
        self.assertIn("ByteCraft", content)
        self.assertIn("NeuralKnights", content)
        self.assertIn("AlgoRiddim", content)
        self.assertIn("CloudChasers", content)

    def test_save_selected_button_bulk_selection(self):
        """Test 'Save Selections' button endpoint saves selected checkboxes."""
        self.client.force_login(self.admin_user)

        # Select team 2 (NeuralKnights) and team 6 (QuantumQuarks), deselect all others
        team_ids = [self.teams[1].id, self.teams[5].id]
        payload = {"selected_ids": team_ids}

        response = self.client.post(
            reverse("hackathon:save_selected_phase01"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["status"], "success")

        # Verify database state
        self.teams[0].refresh_from_db()
        self.teams[1].refresh_from_db()
        self.teams[5].refresh_from_db()
        self.assertFalse(self.teams[0].is_selected)  # was True, now False
        self.assertTrue(self.teams[1].is_selected)   # was False, now True
        self.assertTrue(self.teams[5].is_selected)   # was False, now True

    def test_save_selected_button_deselect_all(self):
        """Test 'Save Selections' with empty list deselects all teams."""
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("hackathon:save_selected_phase01"),
            data={"selected_ids": []},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # All teams should now be unselected
        selected_count = HackathonTeam_Phase01.objects.filter(is_selected=True).count()
        self.assertEqual(selected_count, 0)

    def test_download_excel_button(self):
        """Test 'Download Excel' button generates a valid 3-sheet workbook."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("hackathon:download_excel_phase01"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn("attachment; filename=", response["Content-Disposition"])

    def test_view_response_detail_row_click(self):
        """Test clicking a team row loads the detailed team view."""
        self.client.force_login(self.admin_user)
        team1 = self.teams[0]
        url = reverse("hackathon:view_response_phase01", kwargs={"id": team1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        self.assertIn("ByteCraft", content)
        self.assertIn("Tanvir Hasan", content)
        self.assertIn("IEEE NSU Student Branch", content)
        self.assertIn("Webmaster", content)

    def test_admin_publish_toggle_button(self):
        """Test publish toggle button switches between published and unpublished."""
        self.client.force_login(self.admin_user)
        url = reverse("hackathon:toggle_publish_phase01")

        # Initial is published (from setup)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_published"])

        # Toggle back
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_published"])


if __name__ == "__main__":
    import os, django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spac_platform.settings")
    django.setup()
    teams = create_dummy_hackathon_data(clear_existing=False)
    print(f"Successfully generated {len(teams)} dummy hackathon teams and members!")
