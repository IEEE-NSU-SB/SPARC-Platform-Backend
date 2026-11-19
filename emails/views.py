import base64
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
from time import sleep
import uuid
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from dotenv import set_key
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from core.models import Registered_Participant
from registration.models import Form_Participant_Phase_1, Form_Participant_Unique_Code_Phase_2
from hackathon.models import (
    HackathonTeam_Phase01,
    HackathonTeam_Unique_Code_Phase_2,
    HackathonTeam_Phase02,
)
from spac_platform import settings
from django.contrib import messages
from django.shortcuts import render

from system_administration.utils import log_exception

# Create your views here.
@login_required
def send_emails(request):

    credentials = get_credentials()
    # if not credentials:
    #     print("NOT OKx")
    #     return False
    # try:
    service = build(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, credentials=credentials)
    print(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, 'service created successfully')

    registered_participants = Registered_Participant.objects.all()
    for participant in registered_participants:
        try:
            message = MIMEMultipart()

            message["From"] = "IEEE NSU SB Portal <ieeensusb.portal@gmail.com>"
            message["To"] = participant.email
            message["Cc"] = 'nujhat.saleh@northsouth.edu'
            message["Subject"] = 'Registration Confirmation & Event Guidelines for PowerExpress 2.0'

            message.attach(MIMEText(render_to_string('email_template.html', {'name':participant.name}), 'html'))

            content_file = open(f"Participant Files/Participant_QR/{participant.id}.png", "rb")

            part = MIMEBase('application', 'octet-stream')
            part.set_payload(content_file.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={participant.name}.png',
            )
            message.attach(part)

            content_file2 = open(f"Participant Files/PowerExpress 2.0 Timeline.pdf", "rb")

            part2 = MIMEBase('application', 'octet-stream')
            part2.set_payload(content_file2.read())
            encoders.encode_base64(part2)
            part2.add_header(
                'Content-Disposition',
                f'attachment; filename=PowerExpress 2.0 Timeline.pdf',
            )
            message.attach(part2)

            content_file3 = open(f"Participant Files/PowerExpressBanner.png", "rb")

            part3 = MIMEBase('application', 'octet-stream')
            part3.set_payload(content_file3.read())
            encoders.encode_base64(part3)
            part3.add_header(
                'Content-Disposition',
                f'attachment; filename=PowerExpressBanner.png',
            )
            message.attach(part3)

            # encoded message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            create_message = {"raw": encoded_message}

            send_message = (
                service.users()
                .messages()
                .send(userId="me", body=create_message)
                .execute()
            )

            print(f'Serial: {participant.id}, Message Id: {send_message["id"]}')
            sleep(3)
        except Exception as e:
            print(e)
            return JsonResponse({'message':'error'})

    return JsonResponse({'message':'success'})

@login_required
def send_email(request):
    
    credentials = get_credentials()

    data = json.loads(request.body)
    if not credentials:
        return JsonResponse({'message':'Please re-authorise google api'})
    try:
        service = build(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, credentials=credentials)
        print(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, 'service created successfully')
        message = MIMEMultipart()
        message["From"] = "IEEE NSU SB Portal <ieeensusb.portal@gmail.com>"
        message["To"] = data['emailAddr']
        message["Subject"] = "QR Code for SPARC 2026"
        message.attach(MIMEText(f'''Dear Participant,
                                
Your QR code for SPARC 2026 event is attached in this email.
This QR code is essential to collect your food and goodies.
                                
Best regards,
                                
IEEE NSU SB.''', 'plain'))
        
        qr_file_path = f"Participant Files/Participant_QR/{data['participant_id']}.png"
        if not os.path.exists(qr_file_path):
            os.makedirs("Participant Files/Participant_QR", exist_ok=True)
            from core.models import Registered_Participant
            import qrcode
            p_obj = Registered_Participant.objects.filter(id=data['participant_id']).first()
            if p_obj:
                img = qrcode.make(json.dumps({"unqc": p_obj.unique_code}))
                img.save(qr_file_path)

        content_file = open(qr_file_path, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(content_file.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={data["participant_id"]}.png',
        )
        message.attach(part)
        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        create_message = {"raw": encoded_message}
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
    except Exception as e:
        return JsonResponse({'message':'error'})
    
    return JsonResponse({'message':'success'})

def send_registration_email_phase01(request, name, email):
    credentials = get_credentials()

    if not credentials:
        return JsonResponse({'message':'Please re-authorise google api'})
    try:
        service = build(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, credentials=credentials)
        print(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, 'service created successfully')
        message = MIMEMultipart()
        message["From"] = "IEEE NSU SB Portal <ieeensusb.portal@gmail.com>"
        message["To"] = str(email)
        message["Subject"] = "SPAC25 - Phase-1 - Registration Successful"

        scheme = "https" if request.is_secure() else "http"
        # ics_link = f"{scheme}://{request.get_host()}/media_files/event.ics"
        banner_image_url = f"{scheme}://{request.get_host()}/media_files/SPAC25LogoMin.png"
        # print(ics_link)
        message.attach(MIMEText(render_to_string('phase1_submission_email_template.html', {'participant_name':name, 'banner_image_url':banner_image_url}), 'html'))

        # content_file = open(f"Participant Files/event.ics", "rb")
        # part = MIMEBase('application', 'octet-stream')
        # part.set_payload(content_file.read())
        # encoders.encode_base64(part)
        # part.add_header(
        #     'Content-Disposition',
        #     f'attachment; filename=PowerExpress2.0.ics',
        # )
        # message.attach(part)
        
        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        create_message = {"raw": encoded_message}
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
    except Exception as e:
        print(e)
        return JsonResponse({'message':'error'})
    
    return JsonResponse({'message':'success'})

def send_registration_email_phase02(request, name, email):
    credentials = get_credentials()

    if not credentials:
        return JsonResponse({'message':'Please re-authorise google api'})
    try:
        service = build(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, credentials=credentials)
        print(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, 'service created successfully')
        message = MIMEMultipart()
        message["From"] = "IEEE NSU SB Portal <ieeensusb.portal@gmail.com>"
        message["To"] = str(email)
        message["Subject"] = "SPAC25 - Phase-2 - Registration Successful"

        scheme = "https" if request.is_secure() else "http"
        banner_image_url = f"{scheme}://{request.get_host()}/media_files/SPAC25LogoMin.png"
        message.attach(MIMEText(render_to_string('phase2_submission_email_template.html', {'participant_name':name, 'banner_image_url':banner_image_url}), 'html'))
        
        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        create_message = {"raw": encoded_message}
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
    except Exception as e:
        print(e)
        return JsonResponse({'message':'error'})
    
    return JsonResponse({'message':'success'})

def send_participant_phase02_email(request, form_participants):

    credentials = get_credentials()
    # if not credentials:
    #     print("NOT OKx")
    #     return False
    # try:
    service = build(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, credentials=credentials)
    print(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, 'service created successfully')

    for form_participant in form_participants:
        if not form_participant.is_phase_2_email_sent:
            print(form_participant)
            if not Form_Participant_Unique_Code_Phase_2.objects.filter(participant=form_participant).exists():
                form_participant_unique_code_p02 = Form_Participant_Unique_Code_Phase_2.objects.create(participant=form_participant, unique_code=str(uuid.uuid4()), is_active=True)
            else:
                form_participant_unique_code_p02 = Form_Participant_Unique_Code_Phase_2.objects.get(participant=form_participant)
            try:
                print(f'Sending email to {form_participant.id}!')

                # SEND EMAIL HERE
                message = MIMEMultipart()

                message["From"] = "IEEE NSU SB Portal <ieeensusb.portal@gmail.com>"
                message["To"] = form_participant.email
                message["Subject"] = 'SPAC25 - Phase-2 - Accepted'

                scheme = "https" if request.is_secure() else "http"
                form_link = f"{scheme}://{request.get_host()}/phase-2/?token={form_participant_unique_code_p02.unique_code}"
                banner_image_url = f"{scheme}://{request.get_host()}/media_files/SPAC25LogoMin.png"

                message.attach(MIMEText(render_to_string('phase2_acceptance.html', {'participant_name':form_participant.name, 'phase2_registration_link':form_link, 'banner_image_url':banner_image_url}), 'html'))

                # encoded message
                encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                
                create_message = {"raw": encoded_message}

                send_message = (
                    service.users()
                    .messages()
                    .send(userId="me", body=create_message)
                    .execute()
                )

                print(f'Serial: {form_participant.id}, Message Id: {send_message["id"]}')
                sleep(3)

                form_participant.is_phase_2_email_sent = True
                form_participant.save()
            except:
                print(f'Sending email to {form_participant.id} FAILED!')

    return JsonResponse({'message':'success'})

def send_hackathon_email_phase01(request, team):
    """
    Sends Phase 01 registration acknowledgement email to ALL members of the hackathon team.
    """
    credentials = get_credentials()
    if not credentials:
        print("Google Mail API credentials not found or invalid.")
        return JsonResponse({'message': 'Please re-authorise google api'})
    try:
        service = build(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, credentials=credentials)
        scheme = "https" if request.is_secure() else "http"
        banner_image_url = f"{scheme}://{request.get_host()}/media_files/SPAC25LogoMin.png"

        members = team.members.all()
        for member in members:
            if not member.email:
                continue
            try:
                message = MIMEMultipart()
                message["From"] = "IEEE NSU SB Portal <ieeensusb.portal@gmail.com>"
                message["To"] = str(member.email).strip()
                message["Subject"] = f"SPARC 2026 - Hackathon Phase 01 Registration Received - {team.team_name}"

                context = {
                    'recipient_name': member.full_name,
                    'team': team,
                    'member': member,
                    'banner_image_url': banner_image_url,
                }
                html_content = render_to_string('hackathon_phase1_submission_email.html', context)
                message.attach(MIMEText(html_content, 'html'))

                encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                create_message = {"raw": encoded_message}

                send_message = (
                    service.users()
                    .messages()
                    .send(userId="me", body=create_message)
                    .execute()
                )
                print(f'Hackathon Phase 1 email sent to {member.email}, message Id: {send_message.get("id")}')
                sleep(1)
            except Exception as e:
                print(f'Failed sending Hackathon Phase 1 email to {member.email}: {e}')
                log_exception(e, request)

        return JsonResponse({'message': 'success'})
    except Exception as e:
        print(f"send_hackathon_email_phase01 error: {e}")
        log_exception(e, request)
        return JsonResponse({'message': 'error'})

def send_hackathon_phase02_email(request, selected_teams):
    """
    Sends Phase 02 acceptance & finalization invitation email ONLY to the Team Leader of selected teams.
    Generates a unique single-use token link for each team.
    """
    credentials = get_credentials()
    if not credentials:
        return JsonResponse({'message': 'Please re-authorise google api', 'status': 'error'})

    try:
        service = build(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, credentials=credentials)
        scheme = "https" if request.is_secure() else "http"
        banner_image_url = f"{scheme}://{request.get_host()}/media_files/SPAC25LogoMin.png"

        sent_count = 0
        for team in selected_teams:
            if not team.is_phase_2_email_sent:
                if not HackathonTeam_Unique_Code_Phase_2.objects.filter(team=team).exists():
                    unique_code_obj = HackathonTeam_Unique_Code_Phase_2.objects.create(
                        team=team,
                        unique_code=str(uuid.uuid4()),
                        is_active=True,
                    )
                else:
                    unique_code_obj = HackathonTeam_Unique_Code_Phase_2.objects.get(team=team)

                try:
                    leader_name = team.leader.full_name if team.leader else (team.leader_signature or "Team Leader")
                    form_link = f"{scheme}://{request.get_host()}/hackathon/phase-2/?token={unique_code_obj.unique_code}"

                    message = MIMEMultipart()
                    message["From"] = "IEEE NSU SB Portal <ieeensusb.portal@gmail.com>"
                    message["To"] = str(team.leader_email).strip()
                    message["Subject"] = f"SPARC 2026 - Hackathon Phase 02 Invitation & Finalization - {team.team_name}"

                    context = {
                        'leader_name': leader_name,
                        'team': team,
                        'phase2_registration_link': form_link,
                        'banner_image_url': banner_image_url,
                    }
                    html_content = render_to_string('hackathon_phase2_acceptance.html', context)
                    message.attach(MIMEText(html_content, 'html'))

                    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                    create_message = {"raw": encoded_message}

                    send_message = (
                        service.users()
                        .messages()
                        .send(userId="me", body=create_message)
                        .execute()
                    )
                    print(f'Phase 2 acceptance email sent to leader {team.leader_email}, message Id: {send_message.get("id")}')
                    sleep(2)

                    team.is_phase_2_email_sent = True
                    team.save(update_fields=['is_phase_2_email_sent'])
                    sent_count += 1
                except Exception as e:
                    print(f'Failed sending Phase 2 email to {team.leader_email}: {e}')
                    log_exception(e, request)

        return JsonResponse({'message': f'Successfully emailed Phase 2 invitation to {sent_count} team leader(s)!', 'status': 'success'})
    except Exception as e:
        print(f"send_hackathon_phase02_email error: {e}")
        log_exception(e, request)
        return JsonResponse({'message': 'Error sending Phase 2 invitation emails.', 'status': 'error'})

def send_hackathon_email_phase02(request, phase2_team):
    """
    Sends Phase 02 registration & payment confirmation email to ALL members of the hackathon team.
    """
    credentials = get_credentials()
    if not credentials:
        print("Google Mail API credentials not found or invalid.")
        return JsonResponse({'message': 'Please re-authorise google api'})

    try:
        service = build(settings.GOOGLE_MAIL_API_NAME, settings.GOOGLE_MAIL_API_VERSION, credentials=credentials)
        scheme = "https" if request.is_secure() else "http"
        banner_image_url = f"{scheme}://{request.get_host()}/media_files/SPAC25LogoMin.png"

        members = phase2_team.members.all()
        for member in members:
            if not member.email:
                continue
            try:
                message = MIMEMultipart()
                message["From"] = "IEEE NSU SB Portal <ieeensusb.portal@gmail.com>"
                message["To"] = str(member.email).strip()
                message["Subject"] = f"SPARC 2026 - Hackathon Phase 02 Registration & Payment Received - {phase2_team.team_name}"

                context = {
                    'recipient_name': member.full_name,
                    'team': phase2_team,
                    'member': member,
                    'banner_image_url': banner_image_url,
                }
                html_content = render_to_string('hackathon_phase2_submission_email.html', context)
                message.attach(MIMEText(html_content, 'html'))

                encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                create_message = {"raw": encoded_message}

                send_message = (
                    service.users()
                    .messages()
                    .send(userId="me", body=create_message)
                    .execute()
                )
                print(f'Hackathon Phase 2 confirmation sent to {member.email}, message Id: {send_message.get("id")}')
                sleep(1)
            except Exception as e:
                print(f'Failed sending Hackathon Phase 2 confirmation to {member.email}: {e}')
                log_exception(e, request)

        return JsonResponse({'message': 'success'})
    except Exception as e:
        print(f"send_hackathon_email_phase02 error: {e}")
        log_exception(e, request)
        return JsonResponse({'message': 'error'})

@login_required
def authorize(request):

    credentials = get_credentials()
    if not credentials:
        flow = get_google_auth_flow(request)
        if(request.META['HTTP_HOST'] == "127.0.0.1:8000" or request.META['HTTP_HOST'] == "localhost:8000"):
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
            )
        else:
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                login_hint='ieeensusb.portal@gmail.com'
            )
        request.session['state'] = state
        return redirect(authorization_url)

    # if credentials != None:
        # messages.success(request, "Already authorized!")    
    return redirect('core:dashboard')

def oauth2callback(request):
    try:
        if(request.META['HTTP_HOST'] == "127.0.0.1:8000" or request.META['HTTP_HOST'] == "localhost:8000"):
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        state = request.GET.get('state')
        if state != request.session.pop('state', None):
            return HttpResponseBadRequest('Invalid state parameter')
        
        flow = get_google_auth_flow(request)
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials
        save_credentials(credentials)
        # messages.success(request, "Authorized")
        return redirect('core:dashboard')
    except:
        # messages.warning(request, "Access Denied!")
        return redirect('core:dashboard')
    
def get_google_auth_flow(request):
    client_config = {
        'web': {
            'client_id': settings.GOOGLE_CLOUD_CLIENT_ID,
            'project_id': settings.GOOGLE_CLOUD_PROJECT_ID,
            'auth_uri': settings.GOOGLE_CLOUD_AUTH_URI,
            'token_uri': settings.GOOGLE_CLOUD_TOKEN_URI,
            'auth_provider_x509_cert_url': settings.GOOGLE_CLOUD_AUTH_PROVIDER_x509_cert_url,
            'client_secret': settings.GOOGLE_CLOUD_CLIENT_SECRET,
        }
    }
    if(request.META['HTTP_HOST'] == "127.0.0.1:8000" or request.META['HTTP_HOST'] == "localhost:8000"):
        redirect_uri=f"http://{request.META['HTTP_HOST']}/init/oauth2callback"
    else:
        redirect_uri=f"https://{request.META['HTTP_HOST']}/init/oauth2callback"

    return Flow.from_client_config(
        client_config,
        settings.SCOPES,
        redirect_uri=redirect_uri
    )

def save_credentials(credentials):
        set_key('.env', 'GOOGLE_CLOUD_TOKEN', credentials.token)
        settings.GOOGLE_CLOUD_TOKEN = credentials.token
        if(credentials.refresh_token):
            set_key('.env', 'GOOGLE_CLOUD_REFRESH_TOKEN', credentials.refresh_token)
            settings.GOOGLE_CLOUD_REFRESH_TOKEN = credentials.refresh_token
        if(credentials.expiry):
            set_key('.env', 'GOOGLE_CLOUD_EXPIRY', credentials.expiry.isoformat())
            settings.GOOGLE_CLOUD_EXPIRY = credentials.expiry.isoformat()


def get_credentials():
    
        creds = None

        if settings.GOOGLE_CLOUD_TOKEN:
            creds = Credentials.from_authorized_user_info({
                'token':settings.GOOGLE_CLOUD_TOKEN,
                'refresh_token':settings.GOOGLE_CLOUD_REFRESH_TOKEN,
                'token_uri':settings.GOOGLE_CLOUD_TOKEN_URI,
                'client_id':settings.GOOGLE_CLOUD_CLIENT_ID,
                'client_secret':settings.GOOGLE_CLOUD_CLIENT_SECRET,
                'expiry':settings.GOOGLE_CLOUD_EXPIRY
            },scopes=settings.SCOPES)

        if not creds or not creds.valid:

            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    save_credentials(creds)
                except:
                    print("NOT OK")
                    return None
            
            return creds

        return creds
