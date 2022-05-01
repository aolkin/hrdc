import re
import sys
from datetime import datetime

import nltk
from django.core.management import CommandError, BaseCommand

from dramaorg.models import Season

def season_name(season):
    return Season.SEASONS[season][1]

def prompt(question):
    if not sys.stdin.isatty():
        raise CommandError("Cannot respond to prompts non-interactively")
    try:
        return input(question)
    except (EOFError, KeyboardInterrupt):
        raise CommandError("Cancelled")

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

def season_from_month(month):
    return Season.SEASONS[1][0] if month < 6 else Season.SEASONS[3][0]

class ImportCommand(BaseCommand):
    requires_system_checks = True
    requires_migrations_checks = True

    def handle(self, filename, *args, okay=None, **options):
        self.okay = list([i.lower() for i in okay]) if okay else []

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)
        parser.add_argument('--only', type=str, required=False)
        parser.add_argument('--okay', type=str, nargs="+")

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
        result = confirm(f"Okay to create {objstr}? (y/n): ")
        if failfast and not result:
            raise CommandError("Operation cancelled")
        return result

    def warn(self, output: str):
        self.stdout.write(self.style.WARNING(output))

    def log(self, output: str):
        self.stdout.write(self.style.SUCCESS(output))
