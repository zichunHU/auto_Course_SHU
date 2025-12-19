from modules.exam_extractor import ExamExtractor

class ExamService:
    def __init__(self, sess, base_url: str, timeout: int = 10):
        self.extractor = ExamExtractor(sess, base_url, timeout)
    def get(self, year: int, term: int, student_id: str):
        return self.extractor.get_exam_schedule(year, term, student_id)