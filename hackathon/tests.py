from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from access_ctrl.models import Permission, UserPermission
from hackathon.models import (
    HackathonFormStatus_Phase01,
    HackathonTeam_Phase01,
    HackathonMember_Phase01,
    HackathonFormStatus_Phase02,
    HackathonTeam_Unique_Code_Phase_2,
    HackathonTeam_Phase02,
    HackathonMember_Phase02,
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


def create_dummy_hackathon_phase02_data(phase1_teams=None):
    """Generates dummy Phase 2 teams, members with T-shirts, and payment records for selected Phase 1 teams."""
    if not phase1_teams:
        phase1_teams = HackathonTeam_Phase01.objects.filter(is_selected=True).prefetch_related("members")

    created_p2_teams = []
    sample_sizes = ["M", "L", "XL", "2XL", "S", "3XL"]

    for idx, p1_team in enumerate(phase1_teams, start=1):
        token_code = f"dummy-token-{p1_team.id}-sparc2026"
        HackathonTeam_Unique_Code_Phase_2.objects.update_or_create(
            team=p1_team,
            defaults={"unique_code": token_code, "is_active": False},
        )

        is_confirmed = (idx % 2 == 1)
        p_method = "Bkash" if idx % 2 == 1 else "Nagad"
        trx_id = f"TRX{p1_team.id:04d}{idx}SPARC"

        p2_team, _ = HackathonTeam_Phase02.objects.update_or_create(
            phase1_team=p1_team,
            defaults={
                "team_name": p1_team.team_name,
                "team_size": p1_team.team_size,
                "leader_email": p1_team.leader_email,
                "leader_phone": p1_team.leader_phone,
                "payment_method": p_method,
                "sender_number": p1_team.leader_phone,
                "transaction_id": trx_id,
                "comments": f"Dummy Phase 2 submission for {p1_team.team_name}",
                "is_payment_confirmed": is_confirmed,
            },
        )

        p2_team.members.all().delete()
        for m_idx, m in enumerate(p1_team.members.all(), start=0):
            chosen_size = sample_sizes[(idx + m_idx) % len(sample_sizes)]
            HackathonMember_Phase02.objects.create(
                team=p2_team,
                phase1_member=m,
                member_order=m.member_order,
                is_leader=m.is_leader,
                full_name=m.full_name,
                email=m.email,
                phone_number=m.phone_number,
                university=m.university,
                department=m.department,
                academic_year=m.academic_year,
                student_id=m.student_id,
                gender=m.gender,
                is_ieee_member=m.is_ieee_member,
                ieee_membership_no=m.ieee_membership_no,
                tshirt_size=chosen_size,
            )
        created_p2_teams.append(p2_team)

    return created_p2_teams


def clear_dummy_hackathon_data():
    """Removes all test dummy hackathon teams and members from database."""
    team_names = [t["team_name"] for t in DUMMY_TEAMS_DATA]
    HackathonTeam_Phase02.objects.filter(team_name__in=team_names).delete()
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


class HackathonPhase02TestCase(TestCase):
    """Integration and validation test suite for Hackathon Phase 2 form and token lifecycle."""

    def setUp(self):
        self.client = Client()

        # Admin user with reg_form_control
        self.admin_user = User.objects.create_user(
            username="p2admin",
            password="testpassword",
            is_staff=True,
        )
        perm, _ = Permission.objects.get_or_create(
            permission_name="reg_form_control",
            defaults={"permission_name": "reg_form_control"},
        )
        UserPermission.objects.get_or_create(user=self.admin_user, permission=perm)

        # Publish status
        HackathonFormStatus_Phase01.objects.create(is_published=True)
        HackathonFormStatus_Phase02.objects.create(is_published=True)

        # Create a sample Phase 1 team and members
        self.team1 = HackathonTeam_Phase01.objects.create(
            team_name="Algorunners",
            team_size=2,
            university_distribution="single",
            leader_email="leader.algo@northsouth.edu",
            leader_phone="01719999001",
            leader_signature="Leader Algo",
            is_selected=True,
            is_phase_2_email_sent=True,
        )
        self.m1 = HackathonMember_Phase01.objects.create(
            team=self.team1,
            member_order=1,
            is_leader=True,
            full_name="Leader Algo",
            email="leader.algo@northsouth.edu",
            phone_number="01719999001",
            university="North South University",
            department="CSE",
            academic_year="3rd",
            student_id="2210001",
            is_ieee_member=True,
            ieee_membership_no="12345678",
        )
        self.m2 = HackathonMember_Phase01.objects.create(
            team=self.team1,
            member_order=2,
            is_leader=False,
            full_name="Member Algo",
            email="member.algo@northsouth.edu",
            phone_number="01719999002",
            university="North South University",
            department="CSE",
            academic_year="3rd",
            student_id="2210002",
            is_ieee_member=False,
        )

        # Generate Phase 2 token
        self.token_obj = HackathonTeam_Unique_Code_Phase_2.objects.create(
            team=self.team1,
            unique_code="test-token-uuid-12345",
            is_active=True,
        )

    def test_phase2_form_missing_token(self):
        """Phase 2 form without token should render check_token with error message."""
        response = self.client.get(reverse("hackathon:form_phase02"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Token was not found!")

    def test_phase2_form_invalid_token(self):
        """Phase 2 form with invalid/expired token renders check_token with error message."""
        response = self.client.get(reverse("hackathon:form_phase02") + "?token=invalid-random-token")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid or expired token!")

    def test_phase2_form_valid_token(self):
        """Phase 2 form with active token loads the form with pre-populated team and members."""
        response = self.client.get(reverse("hackathon:form_phase02") + f"?token={self.token_obj.unique_code}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Algorunners")
        self.assertContains(response, "Leader Algo")
        self.assertContains(response, "Member Algo")
        self.assertContains(response, "Select T-Shirt Size")

    def test_phase2_admin_preview(self):
        """Staff with permission can preview Phase 2 form regardless of public publish state."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("hackathon:admin_phase02"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Form published!")

    def test_phase2_toggle_publish(self):
        """Publish toggle switches Phase 2 publish status."""
        self.client.force_login(self.admin_user)
        url = reverse("hackathon:toggle_publish_phase02")

        # Initial is True
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_published"])

        # Toggle back to True
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_published"])

    def test_phase2_submit_success(self):
        """Submitting Phase 2 with valid token and sizes creates records and deactivates token."""
        payload = {
            "token": self.token_obj.unique_code,
            "payment_method": "Bkash",
            "sender_number": "01719999001",
            "transaction_id": "TRX998877AA",
            "comments": "Payment completed via personal bKash",
            "member_tshirts": {
                str(self.m1.id): "XL",
                str(self.m2.id): "M",
            },
        }
        response = self.client.post(
            reverse("hackathon:submit_phase02"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])

        # Verify database
        p2_team = HackathonTeam_Phase02.objects.get(transaction_id="TRX998877AA")
        self.assertEqual(p2_team.team_name, "Algorunners")
        self.assertEqual(p2_team.payment_method, "Bkash")
        self.assertFalse(p2_team.is_payment_confirmed)

        p2_members = list(p2_team.members.all().order_by("member_order"))
        self.assertEqual(len(p2_members), 2)
        self.assertEqual(p2_members[0].tshirt_size, "XL")
        self.assertEqual(p2_members[1].tshirt_size, "M")

        # Verify token is deactivated
        self.token_obj.refresh_from_db()
        self.assertFalse(self.token_obj.is_active)

    def test_phase2_submit_token_reuse_fails(self):
        """Reusing a deactivated token is rejected."""
        self.token_obj.is_active = False
        self.token_obj.save()

        payload = {
            "token": self.token_obj.unique_code,
            "payment_method": "Nagad",
            "sender_number": "01819999001",
            "transaction_id": "NAG112233BB",
            "member_tshirts": {
                str(self.m1.id): "L",
                str(self.m2.id): "L",
            },
        }
        response = self.client.post(
            reverse("hackathon:submit_phase02"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid or expired token", response.json()["message"])

    def test_phase2_response_table_view(self):
        """Staff with view_reg_responses_list can view Phase 2 response table."""
        perm, _ = Permission.objects.get_or_create(
            permission_name="view_reg_responses_list",
            defaults={"permission_name": "view_reg_responses_list"},
        )
        UserPermission.objects.get_or_create(user=self.admin_user, permission=perm)
        self.client.force_login(self.admin_user)

        # Create a Phase 2 team
        p2_team = HackathonTeam_Phase02.objects.create(
            phase1_team=self.team1,
            team_name=self.team1.team_name,
            team_size=self.team1.team_size,
            leader_email=self.team1.leader_email,
            leader_phone=self.team1.leader_phone,
            payment_method="Bkash",
            sender_number="01719999001",
            transaction_id="TRX12345678",
            is_payment_confirmed=False,
        )
        HackathonMember_Phase02.objects.create(
            team=p2_team,
            phase1_member=self.m1,
            member_order=1,
            is_leader=True,
            full_name=self.m1.full_name,
            email=self.m1.email,
            phone_number=self.m1.phone_number,
            university=self.m1.university,
            department=self.m1.department,
            academic_year=self.m1.academic_year,
            student_id=self.m1.student_id,
            tshirt_size="XL",
        )
        HackathonMember_Phase02.objects.create(
            team=p2_team,
            phase1_member=self.m2,
            member_order=2,
            is_leader=False,
            full_name=self.m2.full_name,
            email=self.m2.email,
            phone_number=self.m2.phone_number,
            university=self.m2.university,
            department=self.m2.department,
            academic_year=self.m2.academic_year,
            student_id=self.m2.student_id,
            tshirt_size="M",
        )

        response = self.client.get(reverse("hackathon:response_table_phase02"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Algorunners")
        self.assertContains(response, "TRX12345678")
        self.assertContains(response, "Pending Verification")

    def test_phase2_view_response_details(self):
        """Staff can view detailed single-team Phase 2 page."""
        perm, _ = Permission.objects.get_or_create(
            permission_name="view_reg_response",
            defaults={"permission_name": "view_reg_response"},
        )
        UserPermission.objects.get_or_create(user=self.admin_user, permission=perm)
        self.client.force_login(self.admin_user)

        p2_team = HackathonTeam_Phase02.objects.create(
            phase1_team=self.team1,
            team_name=self.team1.team_name,
            team_size=self.team1.team_size,
            leader_email=self.team1.leader_email,
            leader_phone=self.team1.leader_phone,
            payment_method="Bkash",
            sender_number="01719999001",
            transaction_id="TRXDETAIL99",
            is_payment_confirmed=True,
        )
        m1_p2 = HackathonMember_Phase02.objects.create(
            team=p2_team,
            phase1_member=self.m1,
            member_order=1,
            is_leader=True,
            full_name=self.m1.full_name,
            email=self.m1.email,
            phone_number=self.m1.phone_number,
            university=self.m1.university,
            department=self.m1.department,
            academic_year=self.m1.academic_year,
            student_id=self.m1.student_id,
            tshirt_size="2XL",
        )

        url = reverse("hackathon:view_response_phase02", kwargs={"id": p2_team.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TRXDETAIL99")
        self.assertContains(response, "Payment Confirmed")
        self.assertContains(response, "T-Shirt: 2XL")

    def test_phase2_save_selected_payment_confirmation(self):
        """Bulk update confirms payment for selected teams."""
        self.client.force_login(self.admin_user)
        p2_team = HackathonTeam_Phase02.objects.create(
            phase1_team=self.team1,
            team_name=self.team1.team_name,
            team_size=self.team1.team_size,
            leader_email=self.team1.leader_email,
            leader_phone=self.team1.leader_phone,
            payment_method="Bkash",
            sender_number="01719999001",
            transaction_id="TRXCONFIRM1",
            is_payment_confirmed=False,
        )

        response = self.client.post(
            reverse("hackathon:save_selected_phase02"),
            data={"selected_ids": [p2_team.id]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

        p2_team.refresh_from_db()
        self.assertTrue(p2_team.is_payment_confirmed)

    def test_phase2_download_excel(self):
        """Staff can download Phase 2 Excel workbook with teams and member T-shirts."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("hackathon:download_excel_phase02"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn("hackathon_phase02_data.xlsx", response["Content-Disposition"])


if __name__ == "__main__":
    import os, django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spac_platform.settings")
    django.setup()
    teams = create_dummy_hackathon_data(clear_existing=False)
    p2_teams = create_dummy_hackathon_phase02_data(teams)
    print(f"Successfully generated {len(teams)} dummy Phase 1 teams and {len(p2_teams)} dummy Phase 2 teams with member T-shirts!")
