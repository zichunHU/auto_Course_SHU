import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from loguru import logger
from bs4 import BeautifulSoup

class CourseParamsExtractor:
    """选课参数提取器"""

    COURSE_SELECTION_PATH = "jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html"

    def __init__(self, session: requests.Session, base_url: str, timeout: int = 10):
        """
        初始化选课参数提取器
        :param session: 已登录的会话对象
        :param base_url: 教务系统基础URL
        :param timeout: 请求超时时间(秒)
        """
        self.sess = session
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        logger.debug("初始化 CourseParamsExtractor：base_url={}", self.base_url)

    def get_selection_time(self) -> dict:
        """
        获取当前选课时间
        :return: 选课时间信息
        """
        selection_time_url = urljoin(self.base_url, "jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html")
        response = self.sess.get(selection_time_url)

        if response.status_code != 200:
            (logger.debug("获取选课时间失败，状态码: {}", response.status_code))

        # 解析页面内容，假设选课时间在某个特定的HTML元素中
        # 这里需要根据实际页面结构进行调整
        # 例如，使用BeautifulSoup解析HTML

        soup = BeautifulSoup(response.text, 'html.parser')
        # 假设选课时间在某个特定的标签中
        selection_time = soup.find("div", class_="selection-time").text.strip()

        logger.info("当前选课时间: {}", selection_time)
        return {"code": 1000, "msg": "获取选课时间成功", "data": selection_time}

    def extract_params(self):
        """
        从选课页面提取必要的选课参数
        :return: dict，包含选课所需的参数
        """
        # 构造选课页面URL
        course_selection_url = urljoin(
            self.base_url,
            f"{self.COURSE_SELECTION_PATH}?gnmkdm=N253512&layout=default"
        )

        logger.debug("访问选课页面：{}", course_selection_url)

        try:
            # 请求选课页面
            response = self.sess.get(
                course_selection_url,
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.error("访问选课页面失败，状态码: {}", response.status_code)
                return {"code": 2333, "msg": f"访问选课页面失败，状态码：{response.status_code}", "data": {}}

            # 解析HTML内容
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取参数
            params = {
                "rwlx": self._extract_param(response.text, "rwlx", "1"),
                "xkly": self._extract_param(response.text, "xkly", "1"),
                "zyh_id": self._extract_param(response.text, "zyh_id"),
                "zyh_id_1": self._extract_param(response.text, "zyh_id_1"),
                "zyh_id_xs": self._extract_param(response.text, "zyh_id_1"),
                "njdm_id": self._extract_param(response.text, "njdm_id"),
                "njdm_id_1": self._extract_param(response.text, "njdm_id_1"),
                "njdm_id_xs": self._extract_param(response.text, "njdm_id_1"),
                "bh_id": self._extract_param(response.text, "bh_id"),
                "xkxnm": self._extract_param(response.text, "xkxnm"),
                "xkxqm": self._extract_param(response.text, "xkxqm", "12"),
                "kklxdm": self._extract_param(response.text, "kklxdm", "01")
            }

            # 检查是否成功提取所有必要参数
            missing_params = [k for k, v in params.items() if not v]
            if missing_params:
                logger.warning("未能提取到部分参数: {}", missing_params)

            logger.info("成功提取选课参数: {}", {k: v for k, v in params.items() if k != "bh_id"})

            return {
                "code": 1000,
                "msg": "参数提取成功",
                "data": params
            }

        except requests.Timeout:
            logger.error("请求超时")
            return {"code": 1003, "msg": "请求超时", "data": {}}
        except Exception as e:
            logger.exception("提取选课参数时发生未知异常：")
            return {"code": 999, "msg": f"未知异常：{e}", "data": {}}

    def _extract_param(self, html_content, param_name, default=None):
        """
        从HTML内容中提取指定参数的值
        :param html_content: HTML内容
        :param param_name: 参数名
        :param default: 默认值
        :return: 参数值或默认值
        """
        # 尝试从JavaScript变量中提取
        pattern1 = rf'var\s+{param_name}\s*=\s*[\'"]([^\'"]+)[\'"]'
        pattern2 = rf'{param_name}\s*:\s*[\'"]([^\'"]+)[\'"]'
        pattern3 = rf'name=[\'"]?{param_name}[\'"]?\s+value=[\'"]([^\'"]+)[\'"]'
        pattern4 = rf'id=[\'"]?{param_name}[\'"]?\s+value=[\'"]([^\'"]+)[\'"]'

        for pattern in [pattern1, pattern2, pattern3, pattern4]:
            match = re.search(pattern, html_content)
            if match:
                return match.group(1)

        # 尝试从隐藏输入字段中提取
        soup = BeautifulSoup(html_content, 'html.parser')
        input_field = soup.find('input', {'name': param_name}) or soup.find('input', {'id': param_name})
        if input_field and 'value' in input_field.attrs:
            return input_field['value']

        return default
