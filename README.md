# Dynamic Web Services for the HRDC

## Setting Up and Running

### Requirements

Run this on the latest version of Python 3 (3.7 as of this writing).

Python package requirements are in requirements.txt, install them with
`pip3 install -r requirements.txt`.

To use any of the timed or email-related features, you must also install
and configure a message broker. I use RabbitMQ. Many pages will hang trying to
connect to the message broker to enqueue an email if you do not do this.

### Setup

Make sure to clone the repository recursively, as it contains submodules.

Copy `sample.settings.py` to `settings.py` in the `hrdc` folder, then open your
new file and adjust your settings as appropriate. For development, I reccomend
the following:

- Set `SECRET_KEY` to anything
- You might want to delete some of the entries from `AUTH`
- If you want to send email, configure the `ANYMAIL` settings
- If necessary, adjust `SITE_URL`
- For debugging, you probably want to change `QUEUED_EMAIL_DEBUG` to `True`

Use `./manage.py migrate` and `./manage.py createsuperuser` as necessary.

### Running

As usual, use `./manage.py runserver` to run the development server. If you
want emails to be sent and timed tasks to occur, you must also run celery like
so: `celery worker -A hrdc -E -B`.

Make sure your desired message broker is running.

## Code Structure

Models generally applicable, such as users and spaces, are in `dramaorg`.
`config` and `basetemplates` are reusable submodules with their own
documentation. `casting` holds everything related to the Common Casting
application. `chat` provides a somewhat reusable chat model.

`emailtracker` provides email services, of which one should mostly just use the
`render_to_queue` and `render_for_user(s)` interfaces from `emailtracker.tools`.
`render_to_queue` provides the same interface as `render_for_user`, except
without the user argument. As such, you must provide a "to" argument yourself.

```render_for_user(user, template, name, ident=None, context={}, silent=True)```

Pass in a user object, a template to render, the email's category/name, a unique
identifier or None (the system will reject emails with the same identifier and
name sent to the same person to prevent sending duplicates), a template context
(to which the user will be added), and whether it should raise an error if a
matching email has been sent already.

## Documentation

The `docs` folder contains some markdown writeups of how to use this site.
Unfortunately, they have not been updated since their initial writing.
