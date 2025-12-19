from typing import TypedDict, Dict, Any, Optional

class Course(TypedDict, total=False):
    kch_id: str
    jxb_id: str
    kcmc: str
    jxbmc: str

class CourseParams(TypedDict, total=False):
    rwlx: str
    xkly: str
    zyh_id: Optional[str]
    zyh_id_1: Optional[str]
    zyh_id_xs: Optional[str]
    njdm_id: Optional[str]
    njdm_id_1: Optional[str]
    njdm_id_xs: Optional[str]
    bh_id: Optional[str]
    xkxnm: Optional[str]
    xkxqm: str
    kklxdm: str

class ScheduleItem(TypedDict, total=False):
    course_id: str
    title: str
    teacher: str
    class_id: str
    credit: Any
    time: str
    place: str
    raw_data: Dict[str, Any]