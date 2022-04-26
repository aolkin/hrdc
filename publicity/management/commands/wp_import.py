import re
import sys
from xml.etree import ElementTree
from lxml.html.clean import Cleaner
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import nltk

from django.utils.text import slugify
from django.utils.timezone import get_default_timezone
from django.db.models import Q
from django.db.utils import IntegrityError

from django.core.management.base import BaseCommand, CommandError

from dramaorg.models import Show, Space, Building, User, Season
from publicity.models import PublicityInfo, ShowPerson, PerformanceDate

HEADER_RE = re.compile(r"^\s*([A-Z &,]{4,})\s*$", re.MULTILINE)
YEAR_RE = re.compile(r"^(.+) (20|')(\d{2})\D*$")
RUNTIME_RE = re.compile(r"^Run ?time:? (.+?)(?:\. (\S+.*))?$", re.IGNORECASE)
SPLIT_RE = re.compile(r"\s*(?:(?:, ??)|(?:&| and )\s*)+(?=\w)", re.IGNORECASE)
PRESENTED_RE = re.compile(r"^Presented by:? (?:the )?(.+)$", re.IGNORECASE)
CREDIT_PATTERN = r"(?:Written|Book|Music|Libretto|Lyrics|Adapted|Created)"
AUTHOR_RE = re.compile(r"^({0}(?: and (?:{0}|Directed|Music Directed))? by):? (.+)$".format(CREDIT_PATTERN), re.IGNORECASE)
DAY_RE = re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),? ", re.IGNORECASE)
TIME_PATTERN = r"([0-2]?[0-9])[:.]?([0-5][0-9])? ?(?i:([ap]\.?m\.?))?"
DATE_RE = re.compile(r"^[A-Z][a-z]+,? *([A-Z][a-z]{2,}) ([0-3]?\d)(?i:th|rd|nd|st)?,?\s+" +
                     r"(?:(?i:@|at)? ?{0}(?: ?(?:and|&|,) ?{0})?)?\.? ?\(?(\*|.+?)?\)?$".format(TIME_PATTERN))
PEOPLE_RE = re.compile(r"^(?:(\S+?\s*?.*?) ?(?:…|:|\.{3,}) ?)?(\S*?\s*?.*?)$")
THEATRE_THEATRE_RE = re.compile("(Theat)re", re.IGNORECASE)

class ParsingException(CommandError): pass
class InvalidState(ParsingException): pass
class UnexpectedInput(ParsingException): pass
class UnexpectedHeader(UnexpectedInput): pass

def season_name(season):
    return Season.SEASONS[season][1]

def confirm(prompt="Are you sure (y/n)? "):
    try:
        choice = input(prompt)
    except (EOFError, KeyboardInterrupt):
        raise CommandError("Cancelled")
    if not sys.stdin.isatty():
        print()
    return choice.lower().startswith("y")

def choose(question, choices: dict):
    print("\n".join([f"\t{i}) {label}" for i, label in choices.items()]))
    try:
        choice = input(question)
    except (EOFError, KeyboardInterrupt):
        raise CommandError("Cancelled")
    if not sys.stdin.isatty():
        print()
        return min(choices.keys())
    return choice

def get_stop_words():
    try:
        return set(nltk.corpus.stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords")
    return set(nltk.corpus.stopwords.words("english"))

def remove_stopwords(text):
    tokenized = re.sub(r"[,./<>?\[\]\\{}|=_+`~!;':\"-]*", "", text).split()
    return " ".join([w for w in tokenized if not w.lower() in get_stop_words()])

def plus_one_year(dt: datetime):
    return dt.replace(year=dt.year + 1)

class Person:
    def __init__(self, type_, name, role=None, year=None):
        self.type = type_
        self.name = name
        self.role = role
        self.year = year

    def __repr__(self):
        return f"<Person type={self.type} name={self.name} role={self.role} year={self.year}>"

class ShowParser:
    MASTHEAD = "masthead"
    BLURB = "blurb"
    DATES = "dates"
    PEOPLE = "people"
    STAFF = ShowPerson.TYPE_CHOICES[1][0]
    CAST = ShowPerson.TYPE_CHOICES[2][0]
    BAND = ShowPerson.TYPE_CHOICES[3][0]

    def __init__(self, text, year):
        self.year = year
        self.text = text

        self.performances = []
        self.people = []
        self.people_role = ""
        self.band_term = ""
        self.masthead = ""
        self.presented_by = ""
        self.authors = []
        self.blurb = ""
        self.blurb_suffix = ""
        self.venue = ""
        self.runtime = ""
        self.performance_note = ""
        self.prod_type = Show.TYPES[-1][0]
        self.state = self.MASTHEAD
        self.people_state = ShowPerson.TYPE_CHOICES[0][0]

    def parse(self):
        for line in self.text.split("\n"):
            self.parse_line(line)

    def parse_line(self, text: str):
        line = text.strip()
        runtime = RUNTIME_RE.match(line)
        if HEADER_RE.match(line) and line != "OBERON":
            self.update_state(line.lower())
        elif runtime:
            if self.runtime:
                raise InvalidState(f"Found runtime \"{line}\" but runtime was "
                                   f"already present: \"{self.runtime}\"")
            self.runtime = runtime.group(1)
            if runtime.group(2):
                self.blurb_suffix += runtime.group(2) + "\n"
        elif DAY_RE.match(line):
            self.parse_date(line)
        elif self.state == self.MASTHEAD:
            if line == "":
                self.state = self.BLURB
            else:
                self.masthead += line + "\n"
                presented = PRESENTED_RE.match(line)
                author = AUTHOR_RE.match(line)
                if presented:
                    self.presented_by = presented.group(1)
                    if "dance" in line.lower() or "ballet" in line.lower():
                        self.prod_type = "dance"
                elif author:
                    self.authors.append(author.groups())
                    if "Written" in author.group(1):
                        self.prod_type = "play"
                    elif (author.group(1) in ("Book by", "Music by", "Libretto by")
                          or "Lyrics" in author.group(1)):
                        self.prod_type = "musical"
        elif self.state == self.BLURB:
            self.blurb += line + "\n"
        elif self.state == self.DATES:
            if self.venue:
                if (not self.performance_note) and (line.startswith("*") or "asterisk" in line.lower()):
                    self.performance_note = line
                else:
                    self.blurb_suffix += line + "\n"
            else:
                if not ("tbd" in line.lower() or "tba" in line.lower()):
                    self.venue = line
        elif self.state == self.PEOPLE:
            if line and not any([i in line.lower() for i in ("tbd", "tba", "to be announced")]):
                self.parse_person(line)
        else:
            raise UnexpectedInput(f'In state "{self.state}" ({self.people_state}), got: "{line}"')

    def parse_person(self, line):
        match = PEOPLE_RE.match(line)
        roles = match.group(1)
        people = match.group(2) or ""
        roles = roles.strip() if roles else self.people_role
        for role in (SPLIT_RE.split(roles) if self.people_state != self.CAST else (roles,)):
            for name in SPLIT_RE.split(people):
                year = YEAR_RE.match(name)
                if year:
                    name = year.group(1)
                    year = 2000 + int(year.group(3))
                if name.strip():
                    self.people.append(Person(self.people_state, name.strip(), role, year))

    def parse_date(self, line):
        match = DATE_RE.match(line)
        if not match:
            raise UnexpectedInput(f"Failed to parse date from \"{line}\"")
        month = datetime.strptime(match.group(1), "%b" if len(match.group(1)) == 3 else "%B").month
        day = int(match.group(2))
        hour, minute = self.get_time(match.group(3), match.group(4), match.group(5))
        note = match.group(9) or ""
        try:
            date = datetime(self.year, month, day, hour, minute, 0, 0)
            date = get_default_timezone().localize(date)
            self.performances.append((date, note))
            if match.group(6):
                hour, minute = self.get_time(match.group(6), match.group(7), match.group(8))
                date = datetime(self.year, month, day, hour, minute, 0, 0)
                date = get_default_timezone().localize(date)
                self.performances.append((date, note))
        except ValueError as e:
            raise UnexpectedInput(f"Unable to parse date from \"{line}\"")

    def get_time(self, hour, minute, am):
        if not hour:
            return 0, 0
        hour = int(hour)
        minute = int(minute) if minute else 0
        if not (am and am.lower().startswith("a")):
            if hour == 12:
                hour = 0
            else:
                hour += 12  # Shift to PM
        return hour, minute

    def update_state(self, header):
        self.people_role = ""
        if header in ("cast",):
            self.state = self.PEOPLE
            self.people_state = self.CAST
        elif header in ("staff",) or "crew" in header:
            self.state = self.PEOPLE
            self.people_state = self.STAFF
        elif header in ("pit", "band", "orchestra",) or "music" in header:
            self.band_term = header
            self.state = self.PEOPLE
            self.people_state = self.BAND
        elif "dates" in header or "ticket" in header or "performances" in header:
            self.state = self.DATES
        elif "about" in header:
            self.state = self.BLURB
        elif header.endswith("s"):
            self.state = self.PEOPLE
            self.people_state = self.CAST
            self.people_role = header.title()
        elif self.state == self.MASTHEAD:
            self.masthead += header.upper() + "\n"
        else:
            raise UnexpectedHeader(header)

    def get_masthead(self):
        return self.masthead.strip()

    def get_blurb(self):
        if self.blurb_suffix:
            return self.blurb.strip() + "\n\n" + self.blurb_suffix.strip()
        return self.blurb.strip()

class Command(BaseCommand):
    help = 'Import Shows from a WordPress post export'
    requires_migrations_checks = True
    requires_system_checks = True

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)
        parser.add_argument('--only', type=str, required=False)
        parser.add_argument('--okay', type=str, nargs="+")

    def handle(self, filename, *args, only=None, okay=[], **options):
        self.okay = list([i.lower() for i in okay])
        results = []

        ns = dict([node for _, node in ElementTree.iterparse(filename, events=['start-ns'])])

        tree = ElementTree.parse(filename)
        root = tree.getroot()
        posts = root.iter("item")

        cleaner = Cleaner(allow_tags=["p", "br", "div", "li", "tr"])

        for post in posts:
            name = post.findtext("title")
            slug = post.findtext("wp:post_name", namespaces=ns)

            if only and slug != only:
                continue

            post_date = post.findtext("wp:post_date", namespaces=ns)
            date = datetime.strptime(post_date + " +0000", "%Y-%m-%d %H:%M:%S %z")
            year = date.year
            season = Season.SEASONS[1][0] if date.month < 6 else Season.SEASONS[3][0]

            body = post.findtext("content:encoded", namespaces=ns)
            cleaned = cleaner.clean_html(body)
            soup = BeautifulSoup(cleaned, 'lxml')
            text = soup.get_text("\n", True).replace("\u00A0", " ")

            # sections = HEADER_RE.split(text)
            # print("\n\n\n==========", name, "==========")
            # print("\n**********\n".join(sections))

            parser = ShowParser(text, year)
            try:
                parser.parse()
            except ParsingException as e:
                self.stderr.write(self.style.ERROR(f"Error while parsing \"{name}\""))
                raise e

            results.append([name, slug, year, season, parser])

        shows = []
        for entry in results:
            show = self.get_or_create_show(*entry)
            if show:
                shows.append((entry[-1], show))

        infos = []
        for parser, show in shows:
            pub = self.get_or_create_publicity_info(show, parser)
            if pub:
                infos.append((parser, pub))

        for parser, info in infos:
            self.update_performance_dates(info, parser.performances, parser.performance_note)

            show: Show = info.show
            if show.season == 3 and show.residency_starts:
                if show.residency_starts.year == show.year and show.residency_starts.month < 6:
                    show.residency_starts = plus_one_year(show.residency_starts)
                    show.residency_ends = plus_one_year(show.residency_ends)
                    show.save()

        for parser, info in infos:
            self.add_people(info, parser.people)

    def log_parsed(self, name, slug, year, season, parser):
        self.log(f"\n\nSHOW: {name} ({slug}) - {year}/{season_name(season)} - {parser.venue}\n")
        self.log(f"\t{parser.runtime} - {parser.performance_note} - {parser.band_term}")
        self.log(f"\t{parser.presented_by} - {parser.authors}\n")
        self.log(f"\tMASTHEAD: {parser.masthead}")
        self.log(f"\tBLURB: {parser.blurb}\t| {parser.blurb_suffix}")
        self.log(f"\tPERFORMANCES: {parser.performances}")
        self.log(f"\tPEOPLE: {parser.people}")

    def get_or_create_show(self, name, slug, year, season, parser):
        show_args = {"year": year, "season": season}
        unstopped_slug = slugify(remove_stopwords(name))
        existing = Show.objects.filter(Q(**show_args) &
                                       (Q(slug=slug) | Q(title__contains=name.partition(":")[0]) |
                                        Q(slug=unstopped_slug)))
        if existing.exists():
            show = existing.first()
            self.log(f"Found matching show: {show} - {season_name(show.season)} {show.year}")
            return show
        else:
            author = (parser.authors[0][1] if len(parser.authors) == 1 else
                      ", ".join([" ".join(i) for i in parser.authors]))
            show_args = {**show_args, "title": name, "creator_credit": author, "slug": slug,
                         "affiliation": parser.presented_by, "prod_type": parser.prod_type,
                         "space": self.get_or_create_venue(parser)}

            if len(parser.performances):
                performances = list(sorted(parser.performances))
                show_args["residency_starts"] = performances[0][0].date()
                show_args["residency_ends"] = performances[-1][0].date()
            if not self.okay_to_create(Show, show_args, False):
                return None
            show = Show(**show_args)
            show.save()
            return show

    def get_or_create_venue(self, parser: ShowParser):
        if parser.venue:
            venue_name = remove_stopwords(parser.venue.partition(",")[0])
            if "loeb mainstage" in venue_name.lower():
                venue_name = "Loeb Proscenium"
            elif "loeb experimental" in venue_name.lower():
                venue_name = "Loeb Ex"
            elif "OBERON" in venue_name:
                venue_name = "OBERON"
            venue_name = THEATRE_THEATRE_RE.sub(lambda match: match.group(1) + "er", venue_name)
        else:
            blurb = parser.get_blurb()
            if "intheex" in blurb or "Loeb Ex" in blurb:
                venue_name = "Loeb Ex"
            elif "inthepool" in blurb:
                venue_name = "Adams Pool Theater"
            else:
                self.warn(f"Unknown Venue")
                return None
        spaces = Space.objects.filter(Q(name__icontains=venue_name) | Q(nickname__icontains=venue_name))
        if spaces.exists():
            self.log(f"Found matching venue: {spaces.first()}")
            return spaces.first()
        else:
            if self.okay_to_create(Space, {"name": parser.venue}, False):
                building = Building.objects.create(name=parser.venue)
                return Space.objects.create(name=parser.venue, building=building, order=99)
            return None

    def get_or_create_publicity_info(self, show, parser):
        try:
            pub: PublicityInfo = show.publicity_info
            self.log(f"PublicityInfo already exists for {show}")
            if not pub.credits:
                pub.credits = parser.get_masthead()
            if not pub.blurb:
                pub.blurb = parser.get_blurb()
            if not pub.runtime:
                pub.runtime = parser.runtime
            pub.save()
        except Show.publicity_info.RelatedObjectDoesNotExist:
            pub_args = {"show": show, "credits": parser.get_masthead(), "runtime": parser.runtime,
                        "blurb": parser.get_blurb()}
            if parser.band_term:
                if "band" in parser.band_term.lower():
                    pub_args["band_term"] = "Band"
                elif "orchestra" in parser.band_term.lower():
                    pub_args["band_term"] = "Orchestra"
                else:
                    pub_args["band_term"] = "Musicians"
            if not self.okay_to_create(PublicityInfo, pub_args, False):
                return None
            pub = PublicityInfo(**pub_args)
            pub.save()
        return pub

    def update_performance_dates(self, info, performances, general_note):
        preexisting = info.performancedate_set.all()
        dates = preexisting.values_list("performance", flat=True)
        existing = []
        tocreate = []
        for date, note in performances:
            if note.strip() == "*":
                note = general_note
            (existing if date in dates else tocreate).append({"performance": date, "note": note})
        self.warn(f"Found existing dates for {info}: {existing}")
        if self.okay_to_create(PerformanceDate, tocreate, False):
            PerformanceDate.objects.bulk_create([PerformanceDate(show=info, **kwargs) for kwargs in tocreate])

    def add_people(self, info, people):
        users_to_create = []
        show_people = []
        order = 0
        for person in people:
            first, _, last = person.name.replace("’", "'").rpartition(" ")

            showperson_query = Q(person__first_name__iexact=first, person__last_name__iexact=last,
                                 type=person.type, position__iexact=person.role, show=info)
            query = Q(first_name__iexact=first, last_name__iexact=last)
            if person.year:
                showperson_query &= (Q(person__year=None) | Q(person__year=person.year))
                query &= (Q(year=None) | Q(year=person.year))

            showperson = ShowPerson.objects.filter(showperson_query)
            if showperson.exists():
                self.log(f"Found matching ShowPerson: {showperson.first()}")
                continue

            users = User.objects.filter(query)

            if users.count() > 1:
                with_years = users.exclude(year=None)
                if with_years.exists():
                    users = with_years
            if users.count() > 1:
                choices = dict([(user.id, f"{user} ({user.email})") for user in users])
                users = users.filter(id=choose(f"Choose a user for {person.role}: ", choices))

            if users.exists():
                self.log(f"Found matching user: {users.first()}")
                show_people.append({"person": users.first(), "show": info, "position": person.role or "",
                                    "type": person.type, "order": order})
            else:
                fake_email_year = f".{person.year}" if person.year else ""
                fake_email = f"{slugify(first)}.{slugify(last)}" + fake_email_year + "@wp-import.hrdctheater.org"
                fake_user = User.objects.filter(email=fake_email)
                if fake_user.exists():
                    show_people.append({"person": fake_user.first(), "show": info, "position": person.role or "",
                                        "type": person.type, "order": order})
                else:
                    users_to_create.append(({"first_name": first, "last_name": last,
                                             "email": fake_email, "year": person.year}, person, order))
            order += 1

        if self.okay_to_create(User, map(lambda x: x[0], users_to_create)):
            for kwargs, person, order in users_to_create:
                try:
                    user, created = User.objects.get_or_create(
                        **kwargs, defaults={"is_active": False, "source": "wp-import"})
                except IntegrityError as e:
                    existing = User.objects.get(email=kwargs["email"])
                    self.warn(f"Unable to save user: {kwargs} (found {existing})")
                    raise e
                show_people.append({"person": user, "show": info, "position": person.role or "",
                                    "type": person.type, "order": order})
        if self.okay_to_create(ShowPerson, show_people):
            for person in show_people:
                order = person.pop("order")
                show_person, created = ShowPerson.objects.get_or_create(
                    **person, defaults={"order": order})
                if not created:
                    self.warn(f"Found matching person, did not create: {person}")

    def get_okay_to_create_obj(self, cls, args):
        argstr = ", ".join([f"{self.style.SQL_KEYWORD(k)}={self.style.SQL_COLTYPE(repr(v))}" for k, v in args.items()])
        return f"{self.style.SQL_TABLE(cls.__name__)}({argstr})"

    def okay_to_create(self, cls, args, failfast=True):
        if type(args) != dict:
            args = list(args)
            if len(args) < 1:
                return False
            objstr = ", ".join([self.get_okay_to_create_obj(cls, i) for i in args])
        else:
            objstr = self.get_okay_to_create_obj(cls, args)
        if cls.__name__.lower() in self.okay:
            self.warn(f"Automatically creating {objstr}...")
            return True
        result = confirm(f"Okay to create {objstr}? (y/n):")
        if failfast and not result:
            raise CommandError("Operation cancelled")
        return result

    def warn(self, output: str):
        self.stdout.write(self.style.WARNING(output))

    def log(self, output: str):
        self.stdout.write(self.style.SUCCESS(output))
