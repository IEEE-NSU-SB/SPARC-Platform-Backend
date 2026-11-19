
import json
import random
import string

from django.http import JsonResponse
from core.models import Registered_Participant, Token_Participant, Token_Session
from django.db.models import Count, F, Prefetch, Value
from django.db.models.functions import Coalesce

from registration.models import Form_Participant_Phase_2

class Core:

    def get_active_token_sessions():
        '''Gets token sessions that have `is_active` set to True, ordered by the `order_of_session`'''

        return Token_Session.objects.filter(is_active=True).order_by('order_of_session')

    def get_all_token_sessions():
        '''Gets all token sessions, ordered by the `order_of_session`'''
        
        return Token_Session.objects.all().order_by('order_of_session')

    def get_all_token_sessions_with_participant_counts():
        '''Gets all token sessions along with the participant counts for each session, ordered by the `order_of_session`.\n
            It returns a list with `session_name`, `sessionid` and `participant_count`'''
        
        return Token_Session.objects.values('session_name',sessionid=F('id')).annotate(participant_count=Coalesce(Count('token_participant'), Value(0))).order_by('order_of_session')

    def get_all_participant_universities():
        '''Gets all distinct participant universities.'''
        
        return Registered_Participant.objects.values('university').distinct()
    
    def get_all_reg_participants_with_sessions():
        '''Gets all registered_participants along with their token session data.\n
            Returns a list of registered_participants with each participant having a list of `tokens` that have been scanned already.'''

        registered_participants = Registered_Participant.objects.prefetch_related(
            Prefetch(
                'token_participant_set',  # Related name for Token_Participant
                queryset=Token_Participant.objects.only('token_session'),
                to_attr='tokens'
            )
        )
        return registered_participants
    
    def get_new_token_session_scans(last_updated_date_time):
        '''Gets token sessions with `date_time` greater than the param-`last_updated_date_time`.'''
        
        return Token_Participant.objects.filter(date_time__gte=last_updated_date_time).values('token_session', 'registered_participant')
    
    def process_qr_data(request):
        '''Processes the scanned QR data. It returns a JSON response:\n
            -`status` accepted or rejected\n
            -`session` the session name for which the qr is scanned\n
            -`session_id` the session id for which the qr is scanned\n
            -`participant.sl` the participant id for which the qr is scanned\n
            -`participant.name` the participant name for which the qr is scanned'''
        
        try:
            # Get the POST data from the request body
            print(f"Received RAW QR Data: {request.body}")
            # Get the session id from header
            sessionid=request.headers.get('session-id')
            # Get the data from request body
            data = json.loads(request.body)

            # Get the participant using the unique qr code from data
            participant = Registered_Participant.objects.get(unique_code=data.get('unqc'))
            # Get the session using sessionid
            session = Token_Session.objects.get(id=sessionid)

            # If the participant is already scanned/added for this session then reject it
            if len(Token_Participant.objects.filter(registered_participant=participant,token_session=sessionid)) > 0:
                return JsonResponse({'status': 'rejected', 'session':session.session_name, 'session_id':session.id, 'participant': {'sl':participant.id, 'name': participant.name}})
            else:
                # Accept and add the participant for this session
                Token_Participant.objects.create(registered_participant=participant,token_session=session)
                return JsonResponse({'status': 'accepted', 'session':session.session_name, 'session_id':session.id, 'participant': {'sl':participant.id, 'name': participant.name}})
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return JsonResponse({'status': 'error','error': 'Invalid JSON'})
        
    def update_session(sessions):
        '''Sets sessions to active or inactive. The param `sessions` is a list of session ids that need to be active.'''

        # Get all token sessions
        all_sessions = Core.get_all_token_sessions()

        # For each session in all sessions
        for session in all_sessions:
            # If the session id is in sessions
            if str(session.id) in sessions:
                # Set it to active
                session.is_active = True
            else:
                # Set it to inactive
                session.is_active = False
            
            session.save()
        
        return True
    
    def update_participant_session(participant_id, session_id, status):
        '''Updates token_session for a participant without scanning. It takes the parameters:\n
            -`participant_id` for which to update the token_session\n
            -`session_id` for which to update the token_session\n
            -`status` accepted or rejected\n\n
            
            It returns a JSON response:\n
            -`message` accepted, rejected or other\n
            -`session` the session name for which the qr is scanned\n
            -`participant.sl` the participant id for which the qr is scanned\n
            -`participant.name` the participant name for which the qr is scanned'''

        # Get the participant using the participant_id
        participant = Registered_Participant.objects.get(id=participant_id)
        # Get the token session using the session_id
        session = Token_Session.objects.get(id=session_id)
        
        if(status == 'accepted'):
            # If the participant is not scanned already, then add it
            if len(Token_Participant.objects.filter(registered_participant=participant, token_session=session)) == 0:
                Token_Participant.objects.create(registered_participant=participant,token_session=session)
                return JsonResponse({'message':'Accepted', 'session':session.session_name, 'participant': {'sl':participant.id, 'name': participant.name}})
            else:
                # The participant is already scanned/added previously, hence reject it
                return JsonResponse({'message':'Participant is already in session', 'session':session.session_name, 'participant': {'sl':participant.id, 'name': participant.name}})
        elif(status == 'rejected'):
            # If the participant is already scanned/added previously, then remove it
            if len(Token_Participant.objects.filter(registered_participant=participant, token_session=session)) != 0:
                Token_Participant.objects.get(registered_participant=participant,token_session=session).delete()
                return JsonResponse({'message':'Rejected', 'session':session.session_name, 'participant': {'sl':participant.id, 'name': participant.name}})
            else:
                # The participant has not been scanned/added for this session
                return JsonResponse({'message':'Participant is not session', 'session':session.session_name, 'participant': {'sl':participant.id, 'name': participant.name}})
    
    def generate_unique_code(name: str, university: str) -> str:
        # Function to pick a random part of a string
        def get_random_part(s):
            if len(s) > 1:  # Ensure there are at least 2 characters to pick from
                start = random.randint(0, len(s) - 1)
                end = random.randint(start + 1, len(s))  # Ensure end > start
                return s[start:end]
            return s  # Return the whole string if it's too short
        
        # Pick random parts of the name and university
        name_part = get_random_part(name.replace(" ", "").replace(".", ""))
        university_part = get_random_part(university.replace(" ", "").replace(".", ""))
        
        # Combine the random parts
        base_string = name_part + university_part
        
        # Randomly shuffle the base string
        shuffled = ''.join(random.sample(base_string, len(base_string)))
        
        # Add random characters to make the code between 13 and 16 characters
        random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        
        # Combine shuffled string with random characters
        combined = shuffled + random_chars
        
        # Ensure the length is between 13 and 16 characters
        unique_code = combined[:random.randint(13, 16)]
        
        return unique_code
    
    def import_participants_from_reg():
        '''Imports all confirmed participants and hackathon team members to registered_participant table and generates their unique codes.
            This is done when participants/teams are confirmed for event.'''
        from registration.models import Form_Participant_Phase_2
        from hackathon.models import HackathonTeam_Phase02

        existing_emails = set(
            Registered_Participant.objects.exclude(email__isnull=True)
            .exclude(email='')
            .values_list('email', flat=True)
        )
        existing_codes = set(
            Registered_Participant.objects.values_list('unique_code', flat=True)
        )

        objects = []

        # 1. General Participants from Registration Phase 2
        p2_qs = Form_Participant_Phase_2.objects.all()
        if p2_qs.filter(is_payment_confirmed=True).exists():
            p2_qs = p2_qs.filter(is_payment_confirmed=True)

        for participant in p2_qs:
            email_clean = (participant.email or '').strip().lower()
            if email_clean and email_clean in existing_emails:
                continue

            unique_code = Core.generate_unique_code(participant.name, participant.institution or 'University')
            while unique_code in existing_codes:
                unique_code = Core.generate_unique_code(participant.name, participant.institution or 'University')
            existing_codes.add(unique_code)

            if email_clean:
                existing_emails.add(email_clean)

            objects.append(
                Registered_Participant(
                    name=participant.name,
                    university=participant.institution,
                    contact_no=participant.contact_number,
                    email=participant.email,
                    role="Participant",
                    t_shirt_size=participant.tshirt_size,
                    unique_code=unique_code,
                )
            )

        # 2. Hackathon Team Members from Hackathon Phase 2
        h2_qs = HackathonTeam_Phase02.objects.prefetch_related('members').all()
        if h2_qs.filter(is_payment_confirmed=True).exists():
            h2_qs = h2_qs.filter(is_payment_confirmed=True)

        for team in h2_qs:
            for member in team.members.all().order_by('member_order'):
                m_email = (member.email or '').strip().lower()
                if m_email and m_email in existing_emails:
                    continue

                role_label = f"Hackathon - {team.team_name} ({'Leader' if member.is_leader else f'Member {member.member_order}'})"
                unique_code = Core.generate_unique_code(member.full_name, member.university or 'University')
                while unique_code in existing_codes:
                    unique_code = Core.generate_unique_code(member.full_name, member.university or 'University')
                existing_codes.add(unique_code)

                if m_email:
                    existing_emails.add(m_email)

                objects.append(
                    Registered_Participant(
                        name=member.full_name,
                        university=member.university,
                        contact_no=member.phone_number,
                        email=member.email,
                        role=role_label,
                        t_shirt_size=member.tshirt_size,
                        unique_code=unique_code,
                    )
                )

        if objects:
            Registered_Participant.objects.bulk_create(objects)
            try:
                from core.qrgenerator import generate_qr
                generate_qr()
            except Exception as e:
                print(f"QR generation notice: {e}")

        return len(objects)
        