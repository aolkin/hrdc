
import re

EXTRACTION_RE = re.compile(r'^([^<]+|"[^<]+") <([^>]+)>$')

def email_from_user(user):
    name = user.get_full_name(False)
    if name:
        return '"{}" <{}>'.format(name, user.email)
    else:
        return user.email

def extract_address(to):
    match = EXTRACTION_RE.match(to)
    if match:
        return match.groups()[1]
    else:
        return to
