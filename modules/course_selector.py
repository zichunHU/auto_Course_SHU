import requests
from urllib.parse import urljoin
from loguru import logger

class CourseSelector:
    """课程选择器类"""

    SELECT_COURSE_PATH = "jwglxt/xsxk/zzxkyzbjk_xkBcZyZzxkYzb.html"

    def __init__(self, session: requests.Session, base_url: str, timeout: int = 10):
        """
        初始化课程选择器
        :param session: 已登录的会话对象
        :param base_url: 教务系统基础URL
        :param timeout: 请求超时时间(秒)
        """
        self.sess = session
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        logger.debug("初始化 CourseSelector：base_url={}", self.base_url)

    def refresh_session(self, student_id: str):
        """
        刷新会话状态，相当于清除浏览器缓存
        :param student_id: 学号
        :return: 是否成功
        """
        try:
            # 访问选课主页面，刷新会话状态
            refresh_url = urljoin(self.base_url, "jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html")
            refresh_url_with_params = f"{refresh_url}?gnmkdm=N253512&layout=default"

            logger.info("正在刷新会话状态...")
            response = self.sess.get(
                refresh_url_with_params,
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.error("刷新会话失败，状态码: {}", response.status_code)
                return False

            # 可以额外请求一些其他页面来确保会话完全刷新
            logger.info("会话状态已刷新")
            return True

        except Exception as e:
            logger.error("刷新会话时出错: {}", e)
            return False

    def select_course(self, student_id: str, course: dict, params: dict = None) -> dict:
        """
        选课操作
        :param student_id: 学号
        :param course: 课程信息字典，包含必要的选课信息
        :param params: 附加参数
        :return: 选课结果
        """
        # 首先刷新会话
        if not self.refresh_session(student_id):
            return {"code": 1002, "msg": "刷新会话失败，无法继续选课", "data": {}}

        # 构造选课URL
        select_url = urljoin(self.base_url, self.SELECT_COURSE_PATH)
        select_url_with_params = f"{select_url}?gnmkdm=N253512&su={student_id}"

        # 获取必要的参数
        jxb_ids = course.get("jxb_id", "")
        kch_id = course.get("kch_id", "")
        kcmc = course.get("kcmc", "")
        qz = course.get("qz", "0")

        # 其他必要参数
        year = params.get("xkxnm", "")
        term = params.get("xkxqm", "")
        njdm_id = params.get("njdm_id", "")
        njdm_id_xs = params.get("njdm_id_xs", "")
        zyh_id = params.get("zyh_id", "")
        zyh_id_xs = params.get("zyh_id_xs", "")

        # 构造请求数据
        payload = {
            "jxb_ids": jxb_ids,
            "kch_id": kch_id,
            "qz": qz,
            "xkkz_id": "371D2220895ED5DDE063F1000A0ABC43",
            "njdm_id": njdm_id,
            "njdm_id_xs": njdm_id_xs,
            "zyh_id": zyh_id,
            "zyh_id_xs": zyh_id_xs,
            "xkxnm": year,
            "xkxqm": term,
        }

        headers = {
            "Referer": f"{self.base_url}/jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html?gnmkdm=N253512&layout=default",
            "Origin": self.base_url,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }

        logger.debug("准备选课请求 → {}", select_url_with_params)
        logger.debug("→ Payload: {}", payload)
        logger.debug("→ Headers: {}", headers)

        try:
            # 发送选课请求
            response = self.sess.post(
                select_url_with_params,
                data=payload,
                headers=headers,
                timeout=self.timeout
            )

            # 状态码检查
            if response.status_code != 200:
                error_content = response.text[:500] if response.text else "无响应内容"
                error_detail = {
                    "status_code": response.status_code,
                    "url": select_url_with_params,
                    "response_preview": error_content,
                    "headers": dict(response.headers)
                }

            # 记录响应文本用于调试
            logger.debug("响应文本: {}", response.text)

            try:
                # 解析响应JSON
                result = response.json()

                # 检查选课结果
                if result.get("flag") == "1":
                    logger.info("选课成功: {}", kcmc)
                    return {
                        "code": 1000,
                        "msg": "选课成功",
                        "data": result
                    }
                else:
                    error_msg = result.get("msg", "未知错误")
                    logger.error("选课失败: {}", error_msg)
                    return {
                        "code": 1001,
                        "msg": f"选课失败: {error_msg}",
                        "data": result
                    }

            except ValueError as e:
                logger.error("解析选课响应失败: {}", e)
                return {"code": 1007, "msg": f"解析选课响应失败: {e}", "data": {}}

        except requests.Timeout:
            logger.error("选课请求超时")
            return {"code": 1003, "msg": "选课请求超时", "data": {}}
        except Exception as e:
            logger.exception("选课时发生未知异常：")
            return {"code": 999, "msg": f"未知异常：{e}", "data": {}}
