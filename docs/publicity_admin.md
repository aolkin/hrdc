---
title: HRDC Publicity Administration
description: Administrator's Manual
---

* TOC
{:toc}

# The HRDC Publicity Manager

The HRDC Publicity Manager web portal allows PDSM teams to directly manage their
listing on the HRDC website and list their performances for inclusion in the
calendar and list of upcoming performances. This works by allowing you to embed
pages from the app into the primary site.

The publicity manager also allows anyone to submit announcements for the HRDC
newsletter.

For more information about using the publicity manager as a PDSM, please read
the [Publicity Manager User Manual](publicity.html).

# Shows and Webpages

To allow a show's team to use the publicity manager, each show must first be
initialized by an administrator. This can be done by going to "Publicity" ->
"Publicity-Enabled Show", and then selecting "Add Publicity-Enabled Show". The
only information you need to provide is the show you are enabling, and the
website page it is embedded in (more on that later - this can be left blank for
now). Most shows should already be in the system from their venue applications,
but if a show is not, you can add it manually via the green plus next to the
dropdown.

Once you have selected the show to enable, click "Save and continue editing" at
the bottom of the page. You will now be provided with the "embed code", a small
snippet of HTML that is used to embed the show's information into another
webpage. Simply copy this code and paste it into the HTML page editor for the
webpage you would like to insert it into (the show's page on the main website).
After this is done, any information the team adds to their show will be
displayed whereever that code was embedded.

Finally, once you have created the webpage containing the embed, copy its URL
and paste it into the "Website page" field. This tells the system where to find
the website page, and allows the calendar and upcoming performances views to
link back to the performance page.

If need be, you can also edit any of the show's information from the admin as
well.

## WordPress Integration

MyHRDC makes it easy to create the embedding webpages for several shows at once
via the WordPress export function. To do this, first make sure the
`publicity_website_page_prefix` configuration variable is set correctly. Then,
from the "Publicity-Enabled Show" admin, select a number of shows and use the
"Download for WordPress" action. This will set the website page field on the
selected shows based on the prefix set above and each show's "slug" page. It
will then export a CSV containing the show id, show title, show's embed code,
and slug. This can then be imported into WordPress via a CSV-based post
importing tool.

## Season List (Sidebar)

To embed an auto-generated list of shows onto another website, insert this
snippet:

	`<script src="https://app.hrdctheater.org/publicity/season/?year=2019&season=Fall"></script>`

Adjust the year and season as needed. In order for this to generate properly,
you must have filled in the "Website page" field as described previously.
Additionally, only shows with a venue and a residency start date will be
included in the list.

To change the order in which the venues are listed, adjust the "Order" column
in "Base Data" -> "Spaces" in the admin. Spaces with lower numbers will be
listed first.

## Calendar and Upcoming Performances

The Calendar available through the app is automatically generated from the
performance dates supplied by PDSMs in the app.

An embeddable version of the calendar can be found [here](https://app.hrdctheater.org/publicity/calendar/?embed=1).
This version does not have any header or footer, just the calendar itself.

When there are performances in the next couple weeks, a list of upcoming
performances will also be displayed. An embeddable version of that list can be
found [here](https://app.hrdctheater.org/publicity/calendar/?upcoming=1).

Note that, in order for the show titles in the calendar to be linked and
clickable, the "Website page" field must be filled out for that show.

### Adding Custom Events

For events that are not attached to a show, you can use the "Publicity" ->
"Events" page in the admin to add additional events that will be displayed on
the calendar and in the upcoming events section just like performances. If
desired, such events can be linked to a webpage by filling in that field.

### VenueApp Deadlines

Due dates for live Venue Applications will also appear on the calendar. To hide
these dates, the application must be made to no longer be live.

# Newsletter Submissions

To view submitted announcements, navigate to "Announcements" under the
"Publicity" heading in the site admin. From there, you can click on an
announcement to view its full content.

The "Active" column in the list will display a green check for announcements
that should be running as of the current date based on the supplied start and
end dates.

Once an announcement has been included in the newsletter, check the "Published"
checkbox and save in order to prevent the user from making further modifications
to that announcement.

# Help and Support

If you run into problems or have a question about how to use this site, please
email [support@app.hrdctheater.org](mailto:support@app.hrdctheater.org). If you
encounter an error, please include when the error occurred, and as much
specific information about what happened as possible.
