from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

# Create your models here

# phone regex
BANGLADESH_PHONE_VALIDATOR = RegexValidator(
    regex=r'^01[0-9]{9}$',
    message="Phone number must be 11 digits starting with 01."
)

# team name regex
TEAM_NAME_VALIDATOR = RegexValidator(
    regex=r'^[A-Za-z0-9]+_[A-Za-z0-9]+$',
    message=(
        "Team name must follow InstitutionShortName_UniqueName "
        "(e.g., NSU_TechTitans) using letters/numbers and exactly one underscore."
    )
)

IEEE_NUMBER_VALIDATOR = RegexValidator(
    regex=r'^\d{8}$',
    message="IEEE membership number must be exactly 8 digits."
)


class HackathonFormStatus(models.Model):
    """Controls whether the IS AI COOKED? registration form is publicly open."""
    is_published = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hackathon Form Status"
        verbose_name_plural = "Hackathon Form Statuses"

    def __str__(self):
        return "Published" if self.is_published else "Unpublished"


class HackathonTeam(models.Model):
    UNIVERSITY_CHOICES = [
        ('single', 'One university'),
        ('multiple', 'More than one university'),
    ]

    # Team Details
    team_name = models.CharField(
        max_length=150,
        unique=True,
        validators=[TEAM_NAME_VALIDATOR]
    )
    team_size = models.PositiveSmallIntegerField(
        choices=[(2, '2 Members'), (3, '3 Members')]
    )
    university_distribution = models.CharField(
        max_length=20,
        choices=UNIVERSITY_CHOICES
    )
    leader_email = models.EmailField()
    leader_phone = models.CharField(
        max_length=20,
        validators=[BANGLADESH_PHONE_VALIDATOR]
    )

    # Agreements and Declarations
    agreed_enrolled_students = models.BooleanField(default=False)
    agreed_member_consent = models.BooleanField(default=False)
    agreed_composition_final = models.BooleanField(default=False)
    agreed_rules_plagiarism = models.BooleanField(default=False)
    agreed_originality = models.BooleanField(default=False)
    agreed_announcements = models.BooleanField(default=False)
    agreed_media_permission = models.BooleanField(default=False)
    leader_signature = models.CharField(
        max_length=200,
        help_text="Team Leader's full name typed as signature"
    )

    # Administrative Tracking
    is_selected = models.BooleanField(default=False)
    is_confirmation_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Hackathon Team"
        verbose_name_plural = "Hackathon Teams"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.team_name} ({self.team_size} members)"

    @property
    def leader(self):
        return self.members.filter(is_leader=True).first()

    def clean(self):
        super().clean()
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
            raise ValidationError("All 7 declarations and agreements must be accepted.")
        if not self.leader_signature or not self.leader_signature.strip():
            raise ValidationError("Team Leader's typed signature is required.")


class HackathonMember(models.Model):
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
    TSHIRT_CHOICES = [
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
    ]
    GRADE_CHOICES = [
        ('Student Member', 'Student Member'),
        ('Graduate Student Member', 'Graduate Student Member'),
        ('Member', 'Member'),
        ('Other', 'Other'),
    ]

    team = models.ForeignKey(
        HackathonTeam,
        on_delete=models.CASCADE,
        related_name='members'
    )
    member_order = models.PositiveSmallIntegerField(
        choices=[(1, 'Team Leader'), (2, 'Member 2'), (3, 'Member 3')]
    )
    is_leader = models.BooleanField(default=False)

    # Participant Details
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(
        max_length=20,
        validators=[BANGLADESH_PHONE_VALIDATOR]
    )
    university = models.CharField(max_length=200)
    department = models.CharField(max_length=200)
    academic_year = models.CharField(max_length=10, choices=YEAR_CHOICES)
    student_id = models.CharField(max_length=50)
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )
    tshirt_size = models.CharField(max_length=10, choices=TSHIRT_CHOICES)
    is_ieee_member = models.BooleanField(default=False)

    # IEEE Membership Details (Conditional)
    ieee_membership_no = models.CharField(
        max_length=20,
        blank=True,
        default='',
        validators=[IEEE_NUMBER_VALIDATOR]
    )
    ieee_membership_grade = models.CharField(
        max_length=40,
        choices=GRADE_CHOICES,
        blank=True,
        default=''
    )
    ieee_student_branch = models.CharField(
        max_length=200,
        blank=True,
        default=''
    )
    ieee_volunteer_position = models.CharField(
        max_length=200,
        blank=True,
        default=''
    )

    class Meta:
        verbose_name = "Hackathon Member"
        verbose_name_plural = "Hackathon Members"
        ordering = ['member_order']
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'member_order'],
                name='unique_team_member_slot'
            )
        ]

    def __str__(self):
        role = "Leader" if self.is_leader else f"Member {self.member_order}"
        return f"{self.full_name} ({role}) - {self.team.team_name}"

    def clean(self):
        super().clean()
        if self.is_ieee_member:
            if not self.ieee_membership_no:
                raise ValidationError(
                    {'ieee_membership_no': "IEEE membership number is required for IEEE members."}
                )
            if not self.ieee_membership_grade:
                raise ValidationError(
                    {'ieee_membership_grade': "Membership grade is required for IEEE members."}
                )
            if not self.ieee_student_branch:
                raise ValidationError(
                    {'ieee_student_branch': "IEEE Student Branch is required for IEEE members."}
                )
        else:
            self.ieee_membership_no = ''
            self.ieee_membership_grade = ''
            self.ieee_student_branch = ''
            self.ieee_volunteer_position = ''