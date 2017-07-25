# EmailTracker Package

## Tools

Found in `emailtracker.tools`:

`reschedule_all(name=None)`

`queue_msg(msg, name, ident="", silent=True)`

If silent is True, will not raise Exception is message has been sent already.

For the following, kwargs will be used to construct the email.

`queue_email(name, ident="", silent=True, **kwargs)`

`render_to_queue(template, name, ident="", context={}, silent=True, **kwargs)`

`render_for_user(user, *args, **kwargs)`

Passes all args and kwargs to `render_to_queue`, after adjusting the context
to include the user, and setting the `to` field to the user's email address.

`render_for_users(users, *args, allow_failure=False, **kwargs)`

Calls `render_for_user` for each element of `users`, if `allow_failure` is
True, any exceptions raised will be caught, logged, and ignored.

## Utils

Found in `emailtracker.utils`:

`email_from_user(user)`

Returns a formatted `to` address from a user object.

`extract_address(to)`

Returns just the email from a formatted `to` string.

## Template Tags

Load `email`.

`image(fn, alt=Image)`

Requires the context to contain the message in `MESSAGE`.

`href(url, text, *args, **kwargs)`

The url will be reversed with the given args and kwargs.
