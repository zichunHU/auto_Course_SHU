import requests
from urllib.parse import urljoin
from loguru import logger
from modules.tools.debug_utils import DEBUG


class ScheduleExtractor:
    SCHEDULE_PATH = "jwglxt/xsxk/zzxkyzb_cxZzxkYzbChoosedDisplay.html"

    def __init__(self, session: requests.Session, base_url: str, timeout: int = 10):
        """
        :param session: requests.Session 实例
        :param base_url: 基础URL
        :param timeout: 超时时间
        """
        self.sess = session
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        logger.debug("初始化 ScheduleExtractor：base_url={} timeout={}", self.base_url, self.timeout)

    def get_schedule(self, year: int, term: int, student_id: str) -> dict:
        """获取课表数据"""
        # 构造URL
        schedule_url = urljoin(self.base_url, self.SCHEDULE_PATH)
        schedule_url_with_params = f"{schedule_url}?gnmkdm=N253512&su={student_id}"

        try:
            # POST 获取课表数据
            term_param = 3 if term == 1 else 16
            payload = {
                "xkxnm": str(year),
                "xkxqm": str(term_param),
            }

            headers = {
                "Referer": schedule_url_with_params,
                "Origin": self.base_url,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            }

            logger.debug("POST 课表请求: {} payload: {}", schedule_url_with_params, payload)

            response = self.sess.post(
                schedule_url_with_params,
                data=payload,
                headers=headers,
                timeout=self.timeout
            )

            logger.debug("课表响应状态: {}", response.status_code)

            if response.status_code != 200:
                return {"code": 2333, "msg": f"课表请求失败，状态码: {response.status_code}", "data": {}}

            # 检查登录状态
            if "用户登录" in response.text or "统一认证" in response.text:
                return {"code": 1006, "msg": "未登录或会话过期", "data": {}}

            # 解析JSON响应
            try:
                courses_data = response.json()
                logger.debug("获取到课表数据，数量: {}", len(courses_data) if isinstance(courses_data, list) else "未知")

                if not courses_data:
                    return {"code": 1001, "msg": "无课表数据", "data": {"courses": []}}

                # 解析课程数据
                courses = [self._parse_course(course) for course in courses_data]
                return {"code": 1000, "msg": "获取课表成功", "data": {"courses": courses}}

            except ValueError as e:
                logger.error("JSON解析失败: {}", e)
                logger.debug("响应内容: {}", response.text[:500])
                return {"code": 2334, "msg": "响应数据格式错误", "data": {}}

        except Exception as e:
            logger.exception("获取课表时发生未知异常：")
            return {"code": 999, "msg": f"未知异常：{e}", "data": {}}

    def _parse_course(self, item: dict) -> dict:
        """解析单个课程信息"""
        return {
            "course_id": item.get("kch") or item.get("kch_id"),
            "title": item.get("jxbmc") or item.get("kcmc"),
            "teacher": self._extract_teacher_name(item.get("jsxx", "")),
            "class_id": item.get("jxb_id"),
            "credit": self._to_float(item.get("xf")),
            "time": item.get("sksj", "").replace('<br/>', '\n'),
            "place": item.get("jxdd", "").replace('<br/>', '\n'),
            "raw_data": item
        }

    def _extract_teacher_name(self, teacher_info: str) -> str:
        """从教师信息中提取教师姓名"""
        if not teacher_info:
            return ""

        # 根据格式 "xxx/教师姓名/xxx" 提取教师姓名
        parts = teacher_info.split('/')
        if len(parts) >= 2:
            return parts[1]  # 取中间部分作为教师姓名
        else:
            return teacher_info  # 如果格式不匹配，使用原始字符串

    @staticmethod
    def _to_float(v):
        """安全转换为浮点数"""
        try:
            return float(v) if v is not None and v != '' else None
        except (ValueError, TypeError):
            return None
