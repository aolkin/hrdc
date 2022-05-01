import csv
from collections import defaultdict
from datetime import date

from django.utils.text import slugify
from django.utils.timezone import get_default_timezone
from django.db.models import Q
from django.db.utils import IntegrityError

from django.core.management.base import CommandError

from dramaorg.models import Show, Space, Building, User, Season
from publicity.management.commands.utils import season_name, remove_stopwords, choose, ImportCommand, \
    confirm, season_from_month, prompt
from publicity.models import PublicityInfo, ShowPerson

def get_slug(prod_id, show_id, name=""):
    slug = slugify(name) + f"-htdb{prod_id}"
    if show_id and show_id != "0":
        slug += f"-s{show_id}"
    return slug

class Command(ImportCommand):
    help = 'Import Shows from a WordPress post export'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--encoding', type=str, required=False)
        parser.add_argument('--skip-empty', required=False, action='store_const',
                            default=False, const=True)

    def handle(self, filename, *args, only=None, okay=None, encoding=None, skip_empty=False, **options):
        super().handle(filename, *args, only=only, okay=okay, **options)
        self.skip_empty = skip_empty

        with open(filename, encoding=encoding) as fd:
            reader = csv.DictReader(fd)

            if "person_id" in reader.fieldnames:
                self.import_people(reader)
            else:
                if okay and okay != ["PublicityInfo"] and not skip_empty:
                    if not confirm("Automatic object creation enabled but skip-empty disabled, are you sure? "):
                        raise CommandError("Import cancelled")
                self.import_shows(reader)

    def import_shows(self, reader: csv.DictReader):
        for row in reader:
            name = row["showname"]
            if row["name_prefix"]:
                name = row["name_prefix"].strip() + " " + name

            if row["space_name"]:
                space = self.get_or_create_venue(row["space_name"])
            else:
                space = None
                if self.skip_empty:
                    self.warn(f"Skipping {name}, no space specified...")
                    continue

            slug = get_slug(row["production_id"], row["show_id"], name)
            show = self.get_or_create_show(slug, name, row["name"], space, row)
            if show:
                self.get_or_create_publicity_info(show)

    def import_people(self, reader: csv.DictReader):
        mastheads = defaultdict(set)
        for row in reader:
            slug = get_slug(row["prod_id"], row["show_id"])
            try:
                show = PublicityInfo.objects.get(show__slug__endswith=slug)
                user = self.get_or_create_user(row["person_id"], row["firstname"], row["lastname"],
                                               row["class"].rpartition("-")[2], row["email"])
                if user:
                    person = self.get_or_create_person(show, user, row["charactername"],
                                                       row["rolename"], row["type"], row["role_rank"])
                    if person:
                        if person.type == 0:
                            mastheads[show].add(person)
                    else:
                        mastheads[show] = False
            except PublicityInfo.DoesNotExist:
                self.warn(f"Matching show does not exist in database for {slug}...")
        for show, showpeople in mastheads.items():
            if showpeople is False:
                self.warn(f"Skipped importing some people for {show}, cannot update masthead...")
            elif show.credits:
                self.warn(f"Masthead for {show} already present, will not replace...")
            else:
                credits = []
                for position, people in ShowPerson.collate(showpeople):
                    rank = int(people[0].order) if people[0].order else 0
                    names = ", ".join([str(i.person) for i in people])
                    if position.lower().endswith("by"):
                        credits.append((rank, position + " ", names))
                    elif position == "Author":
                        credits.append((rank, "Written by ", names))
                    elif position.endswith("Writer"):
                        credits.append((rank, position[:-2] + "ten by ", names))
                    elif position.endswith("or") or position.endswith("er"):
                        credits.append((rank, position[:-2] + "ed by ", names))
                    else:
                        credits.append((rank, position + " by ", names))
                credits.sort()
                show.credits = "\n".join([i[1] + i[2] for i in credits])
                self.log(f"Updating masthead for {show}: {repr(show.credits)}")
                show.save()
                if credits[0][0] < 100 and not show.show.creator_credit:
                    creator = credits[0][2]
                    self.log(f"Updating show creator credit for {show.show}: {creator}.")
                    show.show.creator_credit = creator
                    show.show.save()

    def get_or_create_venue(self, venue_name: str):
        if venue_name == "New College Theater":
            return Space.objects.get(name="Farkas Hall")
        elif venue_name == "Loeb Mainstage":
            return Space.objects.get(nickname="Loeb Proscenium")
        elif venue_name == "Loeb Experimental Theater":
            return Space.objects.get(nickname="Loeb Ex")
        words = venue_name.split()
        if len(words) > 1 and words[1].lower() == "house":
            building_name = " ".join(words[:2])
            space_name = " ".join(words[2:])
            space_args = {"name": space_name, "nickname": words[0] + " " + space_name}
        else:
            building_name = venue_name
            space_name = venue_name
            space_args = {"name": venue_name, "include_building_name": False}
        spaces = Space.objects.filter(Q(name__icontains=venue_name) | Q(nickname__icontains=venue_name) |
                                      Q(name=space_name, building__name=building_name))
        if spaces.exists():
            self.log(f"Found matching venue: {spaces.first()}")
            return spaces.first()
        else:
            building = self.get_or_create_building(building_name)
            space_args["building"] = building
            self.okay_to_create(Space, space_args)
            return Space.objects.create(order=98, **space_args)

    def get_or_create_building(self, building_name: str):
        buildings = Building.objects.filter(name__icontains=building_name)
        if buildings.exists():
            return buildings.first()
        else:
            self.okay_to_create(Building, {"name": building_name})
            return Building.objects.create(name=building_name)

    def get_or_create_show(self, slug, name, affiliation, space, row):
        existing = Show.objects.filter(slug=slug)
        if existing.exists():
            show = existing.first()
            self.log(f"Found matching show: {show} - {season_name(show.season)} {show.year}")
            return show
        else:
            try:
                start = date.fromisoformat(row["start_date"])
                end = date.fromisoformat(row["end_date"])
            except ValueError:
                self.warn(f"Unable to parse dates for {name} ({row['production_id']}): "
                          f"{row['start_date']} - {row['end_date']} [{row['modified']}]")
                try:
                    start = date.fromisoformat(prompt("Enter start date (YYYY-MM-DD): "))
                    end = date.fromisoformat(prompt("Enter start date (YYYY-MM-DD): "))
                except Exception:
                    self.warn(f"Failed to get dates interactively for {name}.")
                    return None
            show_args = {"year": start.year, "season": season_from_month(start.month), "slug": slug,
                         "title": name, "affiliation": affiliation, "space": space,
                         "residency_starts": start, "residency_ends": end}
            if self.okay_to_create(Show, show_args, False):
                return Show.objects.create(**show_args)

    def get_or_create_publicity_info(self, show):
        try:
            pub: PublicityInfo = show.publicity_info
            self.log(f"PublicityInfo already exists for {show}")
        except Show.publicity_info.RelatedObjectDoesNotExist:
            pub_args = {"show": show}
            if not self.okay_to_create(PublicityInfo, pub_args, False):
                return None
            pub = PublicityInfo(**pub_args)
            pub.save()
        return pub

    def get_or_create_user(self, htdbid, first, last, year, email):
        if not email:
            email = f"{slugify(first)}.{slugify(last)}.htdb{htdbid}@htdb-import.hrdctheater.org"
        users = User.objects.filter(email=email)
        if not users.exists():
            users = User.objects.filter(first_name__iexact=first, last_name__iexact=last)
            if year:
                users = users.filter(Q(year=None) | Q(year=year))
        if users.exists():
            self.log(f"Found existing user for {first} {last} {year} ({email})...")
            return users.first()
        else:
            args = {"first_name": first, "last_name": last, "year": year or None, "email": email}
            if self.okay_to_create(User, args, False):
                user = User(**args, is_active=False, source="htdb", subscribed=False)
                user.save()
                return user

    def get_or_create_person(self, pub: PublicityInfo, user: User, character, role, type_, rank):
        showperson_type = int(type_)
        position = role
        if showperson_type == 2:
            showperson_type = 1
        elif showperson_type == 1 and role == "Actor":
            showperson_type = 2
            position = character
        elif showperson_type == 1 or role == "Actor":
            self.warn(f"Unexpected type ({showperson_type} and role combination: {role}!")
            if confirm("Continue (y/n)? "):
                showperson_type = 2
                position = character
            else:
                raise CommandError("Cancelled")

        if not position.strip("-"):
            position = ""
        else:
            position = position.strip()

        if position == "Director" or position == "Co-Director":
            showperson_type = 0
            rank = 100
        elif "Producer" in position:
            if not ("Assistant" in position or "Associate" in position):
                showperson_type = 0
                rank = 200

        args = {"show": pub, "person": user, "position": position, "type": showperson_type}
        existing = ShowPerson.objects.filter(**args)
        if existing.exists():
            self.log(f"Found existing position: {existing.first()}")
            return existing.first()
        else:
            if self.okay_to_create(ShowPerson, args, False):
                return ShowPerson.objects.create(**args, order=rank)
