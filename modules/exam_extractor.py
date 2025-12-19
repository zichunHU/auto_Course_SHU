import time
import requests
from urllib.parse import urljoin
from loguru import logger

class ExamExtractor:
    EXAM_PATH = "jwglxt/kwgl/kscx_cxXsksxxIndex.html"

    def __init__(self, session: requests.Session, base_url: str, timeout: int = 10):
        self.sess = session
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        logger.debug("初始化 ExamExtractor：base_url={} timeout={}", self.base_url, self.timeout)

    def get_exam_schedule(self, year: int, term: int, student_id: str) -> dict:
        exam_url = urljoin(self.base_url, self.EXAM_PATH)
        exam_url_with_params = f"{exam_url}?doType=query&gnmkdm=N358105"
        term_param = 3 if term == 1 else 16
        xqm = "" if term_param == 0 else str(term_param)

        payload = {
            "xnm": str(year),
            "xqm": xqm,
            "ksmcdmb_id": "",
            "kch": "",
            "kc": "",
            "ksrq": "",
            "kkbm_id": "",
            "_search": "false",
            "nd": int(time.time() * 1000),
            "queryModel.showCount": "15",
            "queryModel.currentPage": "1",
            "queryModel.sortName": "+",
            "queryModel.sortOrder": "asc",
            "time": "0",
        }
        headers = {
            "Referer": f"{self.base_url}/jwglxt/kwgl/kscx_cxXsksxxIndex.html?gnmkdm=N358105&layout=default",
            "Origin": self.base_url,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }

        try:
            resp = self.sess.post(exam_url_with_params, data=payload, headers=headers, timeout=self.timeout)
            logger.debug("考试请求状态: {}", resp.status_code)

            if resp.status_code != 200:
                return {"code": 2333, "msg": "考试接口请求失败"}

            if "用户登录" in resp.text or "统一认证" in resp.text:
                return {"code": 1006, "msg": "未登录或会话过期"}

            try:
                data = resp.json()
            except Exception as e:
                logger.error("考试响应解析失败: {}", e)
                return {"code": 2334, "msg": "响应数据格式错误", "data": {}}

            if not isinstance(data, dict):
                logger.warning("考试信息响应格式不正确，预期为 dict，实际为 {}: {}", type(data), data)
                return {"code": 2335, "msg": f"响应格式不正确: {data}", "data": {}}

            items = data.get("items") or []
            if not items:
                return {"code": 1005, "msg": "无考试数据", "data": {"courses": []}}

            def to_float(v):
                try:
                    return float(v) if v is not None and v != '' else None
                except Exception:
                    return None

            result = {
                "sid": items[0].get("xh"),
                "name": items[0].get("xm"),
                "year": year,
                "term": term,
                "count": len(items),
                "courses": [
                    {
                        "course_id": i.get("kch"),
                        "title": i.get("kcmc"),
                        "time": i.get("kssj"),
                        "location": i.get("cdmc"),
                        "campus": i.get("cdxqmc"),
                        "seat": i.get("zwh"),
                        "retake": i.get("cxbj", ""),
                        "exam_name": i.get("ksmc"),
                        "teacher": i.get("jsxx"),
                        "class_name": i.get("jxbmc"),
                        "college": i.get("kkxy"),
                        "credit": to_float(i.get("xf")),
                        "method": i.get("ksfs"),
                        "paper_id": i.get("sjbh"),
                        "note": i.get("bz1", ""),
                    }
                    for i in items
                ],
            }
            return {"code": 1000, "msg": "获取考试信息成功", "data": result}
        except requests.Timeout:
            return {"code": 1003, "msg": "请求超时"}
        except Exception as e:
            logger.exception("获取考试信息异常")
            return {"code": 999, "msg": f"未知异常：{e}"}
