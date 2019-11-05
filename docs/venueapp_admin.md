# Venue Application Administration
{:.no_toc}

* TOC
{:toc}

# Introduction

The venue application manager is designed to provide a flexible system for
production teams to apply for space. It provides an interface for collecting
staff lists, residency preferences, preliminary budgets, answers to arbitrary
additional questions, and supplemental statements, resumes, and PDF attachments
from each staff member if applicable.

It also allows uploading documents or linking to other websites to display
applications for venues not using this system, allowing all applications to
at least be listed in one place.

# Creating a Venue Application

## Setting up a show

# Available Staff Roles

On the staff list page presented to executive teams applying for space, they
have the ability to select the role for each staff member from a dropdown menu.
The options available in that menu are configured via the "Staff Roles" portion
of the admin interface. This configuration also affects the supplemental
questions presented to individual staff members.

![Staff Roles Dropdown](venueapp_images/staff-roles.png)

## Configuring Available Staff Roles

Staff roles can be created and modified via the page in the site admin. They
are divided into seven categories, primarily for organizational purposes,
although "Executive" staff roles are unique in that staff members placed in
"Executive" roles will be given full access to the show in the app, including
the entire venue application, as well as common casting and other functionality,
should the show be granted space.

In order to remove a staff role from the dropdown, simply check the "Archived"
checkbox, rather than trying to delete the role. This will prevent the role
from being displayed or selected on staff lists.

### "Other" Staff Roles

"Other" staff roles are also special, in that they allow production teams to
assign custom roles to team members. Upon selecting an "Other" role in the staff
list, the user will be able to then input a custom name for the role, allowing
them to include staff members you did not think of.

However, if they manually type the name of an existing role, that staff member
will be coerced back into the role you have listed, and will be shown the
correct supplement for that role.

## Staff Supplements

Regardless of role, the system will ask for a resume and conflicts from all
staff members. The resume and conflicts they supply will also be shared across
all applications they are on for the entire season.

The system supports three kinds of supplements from individual staff members,
statements, attachments, and extra questions. If "Statement length" is non-zero,
the individual will be asked to provide a statement of "up to _" words, even
though the system will not actually enforce a word minimum or maximum. If
"Accepts attachment" is enabled, they will be asked to "Please attach a design plan, statement, or other PDF document". Finally, one or more questions may be
listed for the role. The short name is entirely for internal administrative use,
and will not be shown to the user, only the question itself. The "required"
checkbox is currently ignored, and all questions are always required.

![Staff Role Admin](venueapp_images/role-admin.png)

While the user will be able to save their supplement without providing an
attachment even if "accepts attachment" is checked for their role,
their supplement will not show as complete until they do provide one.

![Individual Supplement](venueapp_images/supplement.png)

# Old-Style Applications

For venues that do not wish to use this system, their applications can still be
linked to or uploaded to the system as downloadable documents.

To do so, navigate to "Old-Style Applications" in the site admin. From there,
you can modify existing entries or add a new one.

![Old-Style Application Admin](venueapp_images/old-style.png)

Simply select the correct year, season, venue, and due date, and then either
provide the URL of the application or upload the application document. (You must
either provide a URL or downloadable application, but never both).

Like the normal venue applications, this application will only be publicly
visible before the due date, and only while "live" is checked.

![Start a New Application](venueapp_images/new-app.png)
