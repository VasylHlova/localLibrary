import smtplib
from celery import shared_task

from django.core.mail import send_mail
from django.utils import timezone
from django.utils.html import strip_tags
from django.urls import reverse
from django.conf import settings

from catalog.models import BookInstance 
from catalog.choices import InstanceStatus

@shared_task(
        name='catalog.send_return_reminder_email', 
        bind=True,
        autoretry_for=(smtplib.SMTPException, TimeoutError, ConnectionRefusedError),
        retry_kwargs={'max_retries': 3},
        retry_backoff=True, 
        retry_jitter=True
)
def send_return_reminder_email(self, book_instance_id: str): 
    try:
        book_instance = BookInstance.objects.select_related('book', 'borrower').get(id=book_instance_id)
    except BookInstance.DoesNotExist:
        return "BookInstance not found."

    if book_instance.status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
        return f"Book {book_instance_id} is not on loan. Email aborted."
        
    if not book_instance.borrower or not book_instance.borrower.email:
         return f"No borrower or email for instance {book_instance_id}."

    today = timezone.now().date()
    days_left = (book_instance.due_back - today).days

    if days_left < 0:
        days_text = "The deadline has already passed!"
    else:
        days_text = f"Days left: {days_left}"

    domain = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    
    book_url = f"{domain}{reverse('book-detail', kwargs={'pk': str(book_instance.book.pk)})}"
    book_title = book_instance.book.title
    book_status = 'loan' if book_instance.status == InstanceStatus.ON_LOAN else 'reservation'
    
    receiver_email = book_instance.borrower.email 

    html_message = f"""
    <html>
        <body>
            <h3>Book Return Reminder</h3>
            <p>Hello {book_instance.borrower.first_name},</p>
            <p>Your {book_status} deadline for the book <a href="{book_url}"><b>{book_title}</b></a> is expiring soon.</p>
            <p style="color: red; font-weight: bold;">{days_text}</p>
        </body>
    </html>
    """

    plain_message = strip_tags(html_message)

    send_mail(
        subject=f'Your {book_status} period for "{book_title}" is expiring soon!',
        message=plain_message,          
        html_message=html_message,     
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[receiver_email],
        fail_silently=False,            
    )