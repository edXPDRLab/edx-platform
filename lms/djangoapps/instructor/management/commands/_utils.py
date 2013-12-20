"""
Helper methods.
"""

import csv
import json
import time
from django.contrib.auth.models import User

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor
from courseware.courses import get_course


def get_descriptor(course, location):
    """Find descriptor for the location in the course."""

    grading_context = course.grading_context
    for descriptor in grading_context['all_descriptors']:
        if descriptor.id == location:
            return descriptor

    return None


def create_module(student, course, descriptor, request):
    """Create module for student from descriptor."""

    field_data_cache = FieldDataCache([descriptor], course.id, student)
    return get_module_for_descriptor(student, request, descriptor, field_data_cache, course.id)


def get_module_for_student(student, course, location, descriptor=None, request=None):
    """Return module for student from location."""

    if isinstance(student, str):
        try:
            student = User.objects.get(username=student)
        except User.DoesNotExist:
            return None

    if isinstance(course, str):
        course = get_course(course)
        if course is None:
            return None

    if descriptor is None:
        descriptor = get_descriptor(course, location)

    if request is None:
        request = DummyRequest()
        request.user = student

    module = create_module(student, course, descriptor, request)
    return module


def get_enrolled_students(course_id):
    """Return enrolled students for course."""

    enrolled_students = User.objects.filter(
        courseenrollment__course_id=course_id,
        courseenrollment__is_active=1
    ).order_by('username')
    return enrolled_students


def get_users_from_ids(ids):
    """Return students from a list of ids."""

    users = User.objects.filter(
        id__in=ids,
    ).order_by('username')
    return users


def get_student_ids_from_csv(path_to_csv):
    """Return student ids from a csv."""

    student_ids = []
    with open(path_to_csv) as csv_file:
        csv_reader = csv.reader(csv_file)
        student_ids = [row[0] for row in csv_reader]

    return student_ids


def create_json_file_of_data(data, filename):
    """Write a json from student data."""

    time_stamp = time.strftime("%Y%m%d-%H%M%S")
    with open('{0}.{1}.json'.format(filename, time_stamp), 'wb') as json_file:
        json_file.write(json.dumps(data, indent=4, sort_keys=True))


class DummyRequest(object):
    """Dummy request"""

    META = {}

    def __init__(self):
        self.session = {}
        self.user = None
        return

    def get_host(self):
        """Return a default host."""
        return 'edx.mit.edu'

    def is_secure(self):
        """Always insecure."""
        return False
