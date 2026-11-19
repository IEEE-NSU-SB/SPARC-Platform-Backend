from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

# Create your models here

TEAM_NAME_VALIDATOR = RegexValidator(
    regex=r'^[A-Za-z0-9]+_[A-Za-z0-9]+$',
    message=(
        "Team name must be in the format InstitutionShortName_UniqueName "
        "(e.g., NSU_TechTitans) using only letters/numbers and exactly one underscore."
    ),
)

BANGLADESH_PHONE_VALIDATOR = RegexValidator(
    regex=r'^01[0-9]{9}$',
    message="Phone / WhatsApp number must be 11 digits starting with 01.",
)

IEEE_NUMBER_VALIDATOR = RegexValidator(
    regex=r'^\d{8}$',
    message="IEEE membership number must be exactly 8 digits.",
)


class HackathonFormStatus_Phase01(models.Model):
    """Independent publish/unpublish switch for IS AI COOKED? Phase 1 registration."""

    is_published = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hackathon Phase 1 Form Status"
        verbose_name_plural = "Hackathon Phase 1 Form Statuses"

    def __str__(self):
        return "Published" if self.is_published else "Unpublished"


class HackathonTeam_Phase01(models.Model):
    """Stores Section 1 (Team Details), Section 4 (Agreements), and Phase 1->2 state."""

    TEAM_SIZE_CHOICES = [
        (2, '2 Members'),
        (3, '3 Members'),
    ]

    UNIVERSITY_DISTRIBUTION_CHOICES = [
        ('single', 'One university'),
        ('multiple', 'More than one university'),
    ]

    # Section 1: Team Details
    team_name = models.CharField(
        max_length=150,
        unique=True,
        validators=[TEAM_NAME_VALIDATOR],
    )
    team_size = models.PositiveSmallIntegerField(choices=TEAM_SIZE_CHOICES)
    university_distribution = models.CharField(
        max_length=20,
        choices=UNIVERSITY_DISTRIBUTION_CHOICES,
    )
    leader_email = models.EmailField()
    leader_phone = models.CharField(
        max_length=20,
        validators=[BANGLADESH_PHONE_VALIDATOR],
    )

    # Section 4: Agreements & Declarations (All 7 required)
    agreed_enrolled_students = models.BooleanField(default=False)
    agreed_member_consent = models.BooleanField(default=False)
    agreed_composition_final = models.BooleanField(default=False)
    agreed_rules_plagiarism = models.BooleanField(default=False)
    agreed_originality = models.BooleanField(default=False)
    agreed_announcements = models.BooleanField(default=False)
    agreed_media_permission = models.BooleanField(default=False)
    leader_signature = models.CharField(
        max_length=200,
        help_text="Team Leader's full name typed as signature",
    )

    # Administrative & Phase 2 Transition Tracking
    is_selected = models.BooleanField(default=False)
    is_phase_2_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Hackathon Team (Phase 1)"
        verbose_name_plural = "Hackathon Teams (Phase 1)"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.team_name} ({self.team_size} members)"

    @property
    def leader(self):
        return self.members.filter(is_leader=True).first()

    def clean(self):
        super().clean()

        # Prevent duplicate team names differing only by capitalization
        if self.team_name:
            qs = HackathonTeam_Phase01.objects.filter(team_name__iexact=self.team_name)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {'team_name': "A team with this name already exists (names are case-insensitive)."}
                )

        required_agreements = [
            self.agreed_enrolled_students,
            self.agreed_member_consent,
            self.agreed_composition_final,
            self.agreed_rules_plagiarism,
            self.agreed_originality,
            self.agreed_announcements,
            self.agreed_media_permission,
        ]
        if not all(required_agreements):
            raise ValidationError(
                "All 7 agreement and declaration checkboxes must be confirmed before submission."
            )

        if not self.leader_signature or not self.leader_signature.strip():
            raise ValidationError(
                {'leader_signature': "Team Leader's full name signature is required."}
            )


class HackathonMember_Phase01(models.Model):
    """Stores Section 2 (Participant Details) and Section 3 (Conditional IEEE Details)."""

    MEMBER_ORDER_CHOICES = [
        (1, 'Team Leader'),
        (2, 'Member 2'),
        (3, 'Member 3'),
    ]

    YEAR_CHOICES = [
        ('1st', '1st year'),
        ('2nd', '2nd year'),
        ('3rd', '3rd year'),
        ('4th', '4th year'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]

    GRADE_CHOICES = [
        ('Student Member', 'Student Member'),
        ('Graduate Student Member', 'Graduate Student Member'),
        ('Member', 'Member'),
        ('Other', 'Other'),
    ]

    team = models.ForeignKey(
        HackathonTeam_Phase01,
        on_delete=models.CASCADE,
        related_name='members',
    )
    member_order = models.PositiveSmallIntegerField(choices=MEMBER_ORDER_CHOICES)
    is_leader = models.BooleanField(default=False)

    # Section 2: Participant Details 
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(
        max_length=20,
        validators=[BANGLADESH_PHONE_VALIDATOR],
    )
    university = models.CharField(max_length=200)
    department = models.CharField(max_length=200)
    academic_year = models.CharField(max_length=10, choices=YEAR_CHOICES)
    student_id = models.CharField(max_length=50)
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
    )
    is_ieee_member = models.BooleanField(default=False)

    # Section 3: IEEE Membership Details 
    ieee_membership_no = models.CharField(
        max_length=20,
        blank=True,
        default='',
        validators=[IEEE_NUMBER_VALIDATOR],
    )
    ieee_membership_grade = models.CharField(
        max_length=40,
        choices=GRADE_CHOICES,
        blank=True,
        default='',
    )
    ieee_student_branch = models.CharField(
        max_length=200,
        blank=True,
        default='',
    )
    ieee_volunteer_position = models.CharField(
        max_length=200,
        blank=True,
        default='',
    )

    class Meta:
        verbose_name = "Hackathon Member (Phase 1)"
        verbose_name_plural = "Hackathon Members (Phase 1)"
        ordering = ['member_order']
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'member_order'],
                name='unique_hackathon_p1_team_member_slot',
            )
        ]

    def __str__(self):
        role = "Team Leader" if self.is_leader else f"Member {self.member_order}"
        return f"{self.full_name} ({role}) - {self.team.team_name}"

    def clean(self):
        super().clean()

        # Keep is_leader strictly aligned with slot 1
        self.is_leader = (self.member_order == 1)

        # Prevent attaching a 3rd member to a 2-member team (including in Django Admin)
        if self.team_id and self.member_order and self.team.team_size:
            if self.member_order > self.team.team_size:
                raise ValidationError(
                    {'member_order': f"Cannot assign Member {self.member_order} to a {self.team.team_size}-member team."}
                )

        # Conditional Section 3 IEEE validation
        if self.is_ieee_member:
            errors = {}
            if not self.ieee_membership_no:
                errors['ieee_membership_no'] = "IEEE membership number (8 digits) is required for IEEE members."
            if not self.ieee_membership_grade:
                errors['ieee_membership_grade'] = "IEEE membership grade is required for IEEE members."
            if not self.ieee_student_branch or not self.ieee_student_branch.strip():
                errors['ieee_student_branch'] = "IEEE Student Branch is required for IEEE members."
            if errors:
                raise ValidationError(errors)
        else:
            # Scrub residual IEEE values if user switched from Yes back to No
            self.ieee_membership_no = ''
            self.ieee_membership_grade = ''
            self.ieee_student_branch = ''
            self.ieee_volunteer_position = ''


# Phase 2 models

class HackathonFormStatus_Phase02(models.Model):
    """Independent publish/unpublish switch for IS AI COOKED? Phase 2 registration."""

    is_published = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hackathon Phase 2 Form Status"
        verbose_name_plural = "Hackathon Phase 2 Form Statuses"

    def __str__(self):
        return "Published" if self.is_published else "Unpublished"


class HackathonTeam_Unique_Code_Phase_2(models.Model):
    """Stores unique access token generated when a Phase 1 team is selected for Phase 2."""

    team = models.ForeignKey(
        HackathonTeam_Phase01,
        on_delete=models.CASCADE,
        related_name="phase2_tokens",
    )
    unique_code = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Hackathon Unique Code for Phase 2"
        verbose_name_plural = "Hackathon Unique Codes for Phase 2"

    def __str__(self):
        return f"{self.team.team_name} - {self.unique_code}"


class HackathonTeam_Phase02(models.Model):
    """Stores Phase 2 registration details, payment verification, and links back to Phase 1 team."""

    PAYMENT_CHOICES = [
        ("Bkash", "Bkash"),
        ("Nagad", "Nagad"),
        ("Not Set", "Not Set"),
    ]

    phase1_team = models.OneToOneField(
        HackathonTeam_Phase01,
        on_delete=models.CASCADE,
        related_name="phase2_entry",
    )
    team_name = models.CharField(max_length=150)
    team_size = models.PositiveSmallIntegerField(
        choices=HackathonTeam_Phase01.TEAM_SIZE_CHOICES,
    )
    leader_email = models.EmailField()
    leader_phone = models.CharField(
        max_length=20,
        validators=[BANGLADESH_PHONE_VALIDATOR],
    )

    # Payment & Finalization
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default="Not Set",
    )
    sender_number = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Sender Bkash/Nagad wallet number",
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )
    comments = models.TextField(
        null=True,
        blank=True,
        default="",
    )

    is_payment_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hackathon Team (Phase 2)"
        verbose_name_plural = "Hackathon Teams (Phase 2)"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.team_name} (Phase 2) - {self.payment_method}"

    @property
    def leader(self):
        return self.members.filter(is_leader=True).first()


class HackathonMember_Phase02(models.Model):
    """Stores individual team member confirmation and T-Shirt size for Phase 2."""

    SIZE_CHOICES = [
        ("S", "S"),
        ("M", "M"),
        ("L", "L"),
        ("XL", "XL"),
        ("2XL", "2XL"),
        ("3XL", "3XL"),
    ]

    team = models.ForeignKey(
        HackathonTeam_Phase02,
        on_delete=models.CASCADE,
        related_name="members",
    )
    phase1_member = models.OneToOneField(
        HackathonMember_Phase01,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="phase2_profile",
    )
    member_order = models.PositiveSmallIntegerField(
        choices=HackathonMember_Phase01.MEMBER_ORDER_CHOICES,
    )
    is_leader = models.BooleanField(default=False)

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(
        max_length=20,
        validators=[BANGLADESH_PHONE_VALIDATOR],
    )
    university = models.CharField(max_length=200)
    department = models.CharField(max_length=200)
    academic_year = models.CharField(
        max_length=10,
        choices=HackathonMember_Phase01.YEAR_CHOICES,
    )
    student_id = models.CharField(max_length=50)
    gender = models.CharField(
        max_length=20,
        choices=HackathonMember_Phase01.GENDER_CHOICES,
        blank=True,
        null=True,
    )

    # IEEE Status
    is_ieee_member = models.BooleanField(default=False)
    ieee_membership_no = models.CharField(
        max_length=20,
        blank=True,
        default="",
    )

    # Phase 2 Specific: T-Shirt Size
    tshirt_size = models.CharField(
        max_length=5,
        choices=SIZE_CHOICES,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Hackathon Member (Phase 2)"
        verbose_name_plural = "Hackathon Members (Phase 2)"
        ordering = ["member_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["team", "member_order"],
                name="unique_hackathon_p2_team_member_slot",
            )
        ]

    def __str__(self):
        role = "Team Leader" if self.is_leader else f"Member {self.member_order}"
        return f"{self.full_name} ({role}, Size: {self.tshirt_size}) - {self.team.team_name}"

    def clean(self):
        super().clean()
        self.is_leader = (self.member_order == 1)
        if self.team_id and self.member_order and self.team.team_size:
            if self.member_order > self.team.team_size:
                raise ValidationError(
                    {"member_order": f"Cannot assign Member {self.member_order} to a {self.team.team_size}-member team."}
                )
