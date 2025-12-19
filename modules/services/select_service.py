from modules.course_selector import CourseSelector

class SelectService:
    def __init__(self, sess, base_url: str, timeout: int = 10):
        self.selector = CourseSelector(sess, base_url, timeout)

    def select(self, student_id: str, course: dict, params: dict):
        return self.selector.select_course(student_id=student_id, course=course, params=params)