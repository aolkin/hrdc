from celery import shared_task

from importlib import import_module

from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
from django.db.models import Q
from django.conf import settings

from weasyprint import HTML, CSS
from PyPDF2 import PdfFileMerger
from io import BytesIO

from emailtracker.tools import render_msg

from config import config

import logging

LOGGER = logging.getLogger(__name__)

@shared_task(acks_late=True, ignore_result=True)
def render_and_send_app(pk):
    app = import_module('venueapp.models').Application.objects.get(pk=pk)
    cover = import_module('venueapp.views').make_cover_page(app)
    max_bytes = config.get_int("max_inline_attachment_bytes", 0)
    for venue in app.venues.all():
        html = render_to_string("venueapp/pdf_app.html", {
            "object": app, "cover": cover, "venue": venue,
            "logo": finders.find("logo.png"),
            "pdf": True, "max_attachment_size": max_bytes,
        })
        doc = HTML(string=html, base_url=settings.SITE_URL).render()
        bookmarks = doc.make_bookmark_tree()
        app_pdf = BytesIO()
        doc.write_pdf(app_pdf)
        merger = PdfFileMerger()
        merger.append(app_pdf)
        for staff in app.staffmember_set.signed_on().filter(
                role__accepts_attachment=True).exclude(
                    Q(attachment=None) | Q(attachment="")):
            name = "{} {}'s ".format(staff.role_name, staff.person)
            try:
                if staff.attachment.size < max_bytes:
                    page = None
                    for i, bookmark in enumerate(bookmarks):
                        if bookmark.label == name + "Supplement":
                            page = bookmarks[i + 1].destination[0]
                    if page:
                        merger.merge(page, staff.attachment.open())
                    else:
                        merger.append(staff.attachment.open(),
                                      bookmark=name + "Attachment")
            except Exception:
                pass
        pdf = BytesIO() # open("/tmp/{}.pdf".format(venue.venue), "wb")
        merger.write(pdf)
        msg = render_msg(
            "venueapp/email/submission.html", locals(),
            to=["{} <{}>".format(i.get_full_name(False), i.email) for i in
                venue.managers.all()],
            cc=["{} <{}>".format(i.get_full_name(False), i.email) for i in
                app.show.staff.all()],
            subject="Application for {} in {} Submitted".format(
                app, venue.venue),
            tags=["venueapp", "venueapp-submission"]
        )
        msg.attach("{} - {}.pdf".format(app, venue), BytesIO(pdf.getbuffer()),
                   "application/pdf")
        try:
            msg.send()
        except Exception as err:
            LOGGER.error("Application submission sending failed: {}".format(
                repr(err)))
        finally:
            merger.close()
