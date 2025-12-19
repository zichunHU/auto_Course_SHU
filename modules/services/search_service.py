from modules.course_searcher import CourseSearcher

class SearchService:
    def __init__(self, sess, base_url: str, timeout: int = 10):
        self.searcher = CourseSearcher(sess, base_url, timeout)

    def search(self, student_id: str, params: dict, year: int, term: int, kklxdm: str, kspage: int, jspage: int, keyW: str):
        return self.searcher.search_course(
            student_id=student_id,
            params=params,
            year=year,
            term=term,
            kklxdm=kklxdm,
            kspage=kspage,
            jspage=jspage,
            keyW=keyW
        )