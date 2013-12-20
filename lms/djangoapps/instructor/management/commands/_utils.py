"""
Helper methods.
"""

import csv
import json
import time

from django.contrib.auth.models import User
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module
from courseware.courses import get_course
from xmodule.modulestore.django import modulestore


def get_module_for_student(student, course, location):
    """Return module for student from location."""

    descriptor = modulestore().get_instance(course.id, location, depth=0)
    request = DummyRequest()
    request.user = student

    field_data_cache = FieldDataCache([descriptor], course.id, student)
    return get_module(student, request, location, field_data_cache, course.id)


def get_enrolled_students(course_id):
    """Return enrolled students for course."""

    enrolled_students = User.objects.filter(
        courseenrollment__course_id=course_id,
        courseenrollment__is_active=1
    ).order_by('username')
    return enrolled_students


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
