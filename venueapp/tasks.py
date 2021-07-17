from celery import shared_task

from importlib import import_module
import traceback as tb

from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
from django.db.models import Q
from django.conf import settings

from weasyprint import HTML, CSS
from PyPDF2 import PdfFileMerger, PdfFileReader
from io import BytesIO

from emailtracker.tools import render_msg

from config import config

import logging

LOGGER = logging.getLogger(__name__)

class _Bookmark:
    def __init__(self, bm):
        self.label = bm.label
        self.location = bm.destination[0]

    def __str__(self):
        return "{} @ {}".format(self.label, self.location)

    def __repr__(self):
        return "<_Bookmark: {}>".format(self)

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
        bookmark_tree = doc.make_bookmark_tree()
        bookmarks = list([_Bookmark(i) for i in bookmark_tree])
        app_pdf = BytesIO()
        doc.write_pdf(app_pdf)
        merger = PdfFileMerger()
        merger.append(app_pdf, import_bookmarks=False)
        for staff in app.staffmember_set.signed_on().filter(
                role__accepts_attachment=True).exclude(
                    Q(attachment=None) | Q(attachment="")):
            name = "{} {}'s ".format(staff.role_name, staff.person)
            try:
                if staff.attachment.size < max_bytes:
                    reader = PdfFileReader(staff.attachment.open(), False)
                    attachment_pages = reader.getNumPages()
                    page = None
                    for i, bookmark in enumerate(bookmarks):
                        if bookmark.label == name + "Supplement":
                            page = bookmarks[i + 1].location
                    if page:
                        merger.merge(page, staff.attachment.open(),
                                     import_bookmarks=False)
                        for i in bookmarks:
                            if i.location >= page:
                                i.location += attachment_pages
                    else:
                        merger.append(staff.attachment.open(),
                                      bookmark=name + "Attachment",
                                      import_bookmarks=False)
            except Exception as e:
                tb.print_exc()
        for i in bookmarks:
            merger.addBookmark(i.label, i.location)
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
            tb.print_exc()
        finally:
            merger.close()
