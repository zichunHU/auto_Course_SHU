from modules.schedule_extractor import ScheduleExtractor

class ScheduleService:
    def __init__(self, sess, base_url: str, timeout: int = 10):
        self.extractor = ScheduleExtractor(sess, base_url, timeout)

    def get(self, year: int, term: int, student_id: str):
        return self.extractor.get_schedule(year, term, student_id)