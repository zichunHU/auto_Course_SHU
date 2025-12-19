import requests
from urllib.parse import urljoin
from loguru import logger
from modules.tools.debug_utils import DEBUG
from modules.tools.display import display_course_info

class CourseSearcher:
    SEARCH_PATH = f"jwglxt/xsxk/zzxkyzb_cxZzxkYzbPartDisplay.html"

    def __init__(self, session: requests.Session, base_url: str, timeout: int = 10):
        """
        :param session: 已登录的会话对象
        :param base_url: 教务系统基础URL
        :param student_id: 学号
        :param timeout: 请求超时时间(秒)
        """
        self.sess = session
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        logger.debug("初始化 CourseSearcher：base_url={} ", self.base_url)

    def search_course(self, student_id: str, params: dict = None, year: int = None, term: int = None,
                      kklxdm: str = "",kspage: int = 1, jspage: int = 10, keyW : str = None) -> dict:
        """
        搜索课程接口
        :param rwlx: 任务类型，1为主修课
        :param xkly: 选课来源，1为主修课
        :param zyh_id: 专业代号
        :param njdm_id: 年级代码
        :param bh_id: 个人编号
        :param year: 当前学期年份
        :param term: 学期
        :param kklxdm: 课程类别，01为主修课，10为选修课
        :param kspage: 页号
        :param jspage: 每页显示的数量
        :param filter_list: 筛选参数列表
        :return: dict，包含搜索结果
        """
        # 计算学期参数
        term_param = term ** 2 * 3  # 1 -> 3, 2 -> 12

        # 构造搜索接口URL
        search_url = urljoin(self.base_url, self.SEARCH_PATH)
        search_url_with_params = f"{search_url}?gnmkdm=N253512&su={student_id}"

        # 构造请求数据
        payload = {
            "xkxnm": year,
            "xkxqm": term_param,
            'kklxdm': kklxdm,
            "kspage": kspage,
            "jspage": jspage,
        }

        # 如果提供了参数字典，则使用它
        if params and isinstance(params, dict):
            for k, v in params.items():
                if v:  # 只添加非空值
                    payload[k] = v

        # 添加筛选参数
        if keyW != "":
             payload['filter_list[0]'] = keyW

        headers = {
                "Referer": search_url_with_params,
                "Origin": self.base_url,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Accept": "application/json, text/javascript, */*; q=0.01"
            }

        logger.debug("准备搜索课程请求 → {}", search_url_with_params)
        logger.debug("→ Payload: {}", payload)
        logger.debug("→ Headers: {}", headers)

        try:
            # 发送搜索请求
            response = self.sess.post(
                search_url_with_params,
                data=payload,
                headers=headers,
                timeout=self.timeout
            )

            # 状态码检查
            if response.status_code != 200:
                logger.error("搜索课程失败，状态码: {}", response.status_code)
                return {"code": 2333, "msg": f"搜索失败，状态码：{response.status_code}", "data": {}}

            # 记录响应文本用于调试
            logger.debug("响应文本: {}", response.text[:200])  # 记录前200个字符

            # 检查响应是否为字符串 "0"
            if response.text.strip() == '"0"' or response.text.strip() == "0":
                logger.info("搜索结果为空")
                return {
                    "code": 1000,
                    "msg": "搜索成功，但没有找到匹配的课程",
                    "data": []
                }

            try:
                # 检查响应是否为JSON格式
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type and 'text/javascript' not in content_type:
                    logger.warning("响应不是JSON格式: {}", content_type)

                # 尝试将响应解析为JSON
                result = response.json()

                # 验证result是否为字典
                if not isinstance(result, dict):
                    logger.error("响应JSON不是字典: {}", type(result))
                    return {"code": 1007, "msg": f"返回数据格式错误: {type(result)}", "data": []}

                # 提取课程列表
                courses = result.get("tmpList", [])
                if not isinstance(courses, list):
                    logger.error("课程列表不是列表类型: {}", type(courses))
                    return {"code": 1007, "msg": f"课程列表格式错误: {type(courses)}", "data": []}

                logger.info(f"搜索到 {len(courses)} 门课程")

                return {
                    "code": 1000,
                    "msg": "搜索成功",
                    "data": courses
                }

            except ValueError as e:
                # JSON解析失败
                logger.error("JSON解析失败: {}", e)
                logger.debug("响应文本: {}", response.text)
                return {"code": 1007, "msg": f"返回数据格式错误: {e}", "data": []}

        except requests.Timeout:
            logger.error("请求超时")
            return {"code": 1003, "msg": "请求超时", "data": {}}
        except Exception as e:
            logger.exception("搜索课程时发生未知异常：")
            return {"code": 999, "msg": f"未知异常：{e}", "data": {}}
