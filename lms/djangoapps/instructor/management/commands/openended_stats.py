"""
Command to get statistics about open ended problems.
"""
from django.core.management.base import BaseCommand
from optparse import make_option

from courseware.courses import get_course
from courseware.models import StudentModule
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.open_ended_grading_classes.openendedchild import OpenEndedChild
from student.models import anonymous_id_for_user
from ._utils import create_json_file_of_data, get_enrolled_students, get_module_for_student


class Command(BaseCommand):
    """
    Command to get statistics about open ended problems.
    """

    help = "Usage: openended_stats <course_id> <problem_location> --task-index=<task_index>\n"

    option_list = BaseCommand.option_list + (
        make_option('--task-index',
                    type='int', default=0,
                    help="Index of task state."),
    )


    def handle(self, *args, **options):
        """Handler for command."""

        task_index = options['task_index']

        if len(args) == 2:
            course_id = args[0]
            location = args[1]
        else:
            print self.help
            return

        try:
            course = get_course(course_id)
        except ValueError as err:
            print err
            return

        descriptor = modulestore().get_instance(course.id, location, depth=0)
        if descriptor is None:
            print "Location {0} not found in course".format(location)
            return

        try:
            enrolled_students = get_enrolled_students(course_id)
            print "Total students enrolled in {0}: {1}".format(course_id, enrolled_students.count())

            self.calculate_state_counts(enrolled_students, course, location, task_index)

        except KeyboardInterrupt:
            print "\nOperation Cancelled"

    def calculate_state_counts(self, students, course, location, task_index):
        """Print stats of students."""

        stats = {
            OpenEndedChild.INITIAL: 0,
            OpenEndedChild.ASSESSING: 0,
            OpenEndedChild.POST_ASSESSMENT: 0,
            OpenEndedChild.DONE: 0
        }

        students_with_saved_answers = []
        students_with_ungraded_submissions = []  # pylint: disable=invalid-name
        students_with_graded_submissions = []  # pylint: disable=invalid-name
        students_with_invalid_state = []

        student_modules = StudentModule.objects.filter(module_state_key=location, student__in=students).order_by('student')
        print "Total student modules: {0}".format(student_modules.count())

        for index, student_module in enumerate(student_modules):
            if index % 100 == 0:
                print "--- {0} students processed ---".format(index)

            student = student_module.student
            print "{0}:{1}".format(student.id, student.username)
            module = get_module_for_student(student, course, location)
            if module is None:
                print "  WARNING: No state found"
                students_with_invalid_state.append(student)
                continue

            latest_task = module.child_module.get_task_at_index(task_index)
            if latest_task is None:
                print "  WARNING: No task state found"
                students_with_invalid_state.append(student)
                continue

            task_state = latest_task.child_state
            stats[task_state] += 1
            print "  State: {0}".format(task_state)

            if task_state == OpenEndedChild.INITIAL:
                if latest_task.stored_answer is not None:
                    students_with_saved_answers.append(student)
            elif task_state == OpenEndedChild.ASSESSING:
                students_with_ungraded_submissions.append(student)
            elif task_state == OpenEndedChild.POST_ASSESSMENT or task_state == OpenEndedChild.DONE:
                students_with_graded_submissions.append(student)

        data = dict()
        data["assessing"] = [{"anonymous_id": anonymous_id_for_user(student, ''),
                              "user_id": student.id,
                              "username": student.username,
                              } for student in students_with_ungraded_submissions]

        data["post_assessment"] = [{"anonymous_id": anonymous_id_for_user(student, ''),
                                    "user_id": student.id,
                                    "username": student.username,
                                    } for student in students_with_graded_submissions]

        location = Location(location)
        filename = "stats.{0}.{1}".format(location.course, location.name)
        create_json_file_of_data(data, filename)

        print "----------------------------------"
        print "Course: {0}".format(course.location)
        print "Location: {0}".format(location)
        print "Viewed problem: {0}".format(stats[OpenEndedChild.INITIAL] - len(students_with_saved_answers))
        print "Saved answers: {0}".format(len(students_with_saved_answers))
        print "Submitted answers: {0}".format(stats[OpenEndedChild.ASSESSING])
        print "Received grades: {0}".format(stats[OpenEndedChild.POST_ASSESSMENT] + stats[OpenEndedChild.DONE])
        print "Invalid state: {0}".format(len(students_with_invalid_state))
        print "----------------------------------"
