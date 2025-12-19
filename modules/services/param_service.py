from modules.tools.course_params_extractor import CourseParamsExtractor

class ParamService:
    def __init__(self, sess, base_url: str, timeout: int = 10):
        self.extractor = CourseParamsExtractor(sess, base_url, timeout)

    def extract(self):
        return self.extractor.extract_params()