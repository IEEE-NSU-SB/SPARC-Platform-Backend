from threading import Thread

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render

from ambassador_email.models import MailJob
from ambassador_email.sender import process_job_in_thread

from .forms import AmbassadorForm, DUPLICATE_EMAIL_MSG
from .ratelimit import is_rate_limited

RATE_LIMIT_MSG = 'Too many submissions from this IP address. Please wait before trying again.'


def _is_ajax(request):
    """form.js marks its fetch() calls with X-Requested-With: XMLHttpRequest."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _errors_for_json(form):
    """Shape the errors for form.js renderErrors(): {field: ['msg', ...]}."""
    return {
        field: [err['message'] for err in messages]
        for field, messages in form.errors.get_json_data().items()
    }


def ambassador_apply(request):
    """Show and process the SPARC Ambassador application form.

    GET  -> render the empty form.
    POST -> validate with AmbassadorForm; on success save the application
            FIRST and answer immediately. The background mail job
            is created and dispatched via transaction.on_commit. AJAX callers get
            JSON; plain browser posts get the /thanks/ page or the form
            re-rendered with field errors.
    """
    if request.method == 'POST':
        if is_rate_limited(request, action='ambassador_apply'):
            if _is_ajax(request):
                return JsonResponse({
                    'success': False,
                    'message': RATE_LIMIT_MSG,
                    'errors': {'__all__': [RATE_LIMIT_MSG]},
                }, status=429)
            form = AmbassadorForm(request.POST, request.FILES)
            form.add_error(None, RATE_LIMIT_MSG)
            return render(request, 'ambassador_registration/apply.html', {'form': form}, status=429)

        form = AmbassadorForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                with transaction.atomic():
                    ambassador = form.save()

                    job, _ = MailJob.objects.get_or_create(
                        campaign='ambassador_received',
                        ambassador=ambassador,
                        defaults={'to_email': ambassador.email})
                    transaction.on_commit(lambda: Thread(
                        target=process_job_in_thread, args=(job.id,),
                        daemon=True).start())
            except IntegrityError:
                form.add_error('email', DUPLICATE_EMAIL_MSG)
                if _is_ajax(request):
                    return JsonResponse({'success': False,
                                         'errors': _errors_for_json(form)},
                                        status=400)
                return render(request, 'ambassador_registration/apply.html',
                              {'form': form})

            if _is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Application received. Thank you!',
                })
            return redirect('ambassador_registration:thanks')

        if _is_ajax(request):
            return JsonResponse({'success': False,
                                 'errors': _errors_for_json(form)}, status=400)

        # Non-JavaScript path: re-render with the submitted values and the
        # server-rendered error lists (the template shows {{ form.x.errors }}).
        return render(request, 'ambassador_registration/apply.html', {'form': form})

    return render(request, 'ambassador_registration/apply.html', {'form': AmbassadorForm()})


def thanks(request):
    """Confirmation page for non-JavaScript submissions."""
    return render(request, 'ambassador_registration/thanks.html')
