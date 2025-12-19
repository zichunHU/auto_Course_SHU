import requests
import time
from loguru import logger
from modules.tools.debug_utils import DEBUG
from modules.tools.encrypt import encrypt

class LoginClient:

    def __init__(self, base_url: str, timeout: int = 10):
        """
        :param base_url: 教务系统首页 URL，例如 "https://jwxt.shu.edu.cn"
        :param timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        # 创建 Session 并统一设置浏览器头
        self.sess = requests.Session()
        self.sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        })

        logger.debug("初始化 LoginClient: base_url={}, timeout={}", base_url, timeout)


    def login(self, sid: str, password: str, force: bool = False) -> dict:
        """
        执行登录流程：
        1. GET 教务首页，不跟随重定向，获取 SSO 登录地址；
        2. RSA 加密密码后 POST 到登录接口；
        3. 完成 SSO 后回跳，验证是否登录成功。
        :param force:
        :param sid: 学号
        :param password: 明文密码
        :return: dict，包含 code、msg、cookies（成功时）
        """
        try:
            # 使用新版SSO登录接口
            login_url = 'https://newsso.shu.edu.cn/login/eyJ0aW1lc3RhbXAiOjE3NDYyNDg4MDc3NTg2NjU5MDgsInJlc3BvbnNlVHlwZSI6ImNvZGUiLCJjbGllbnRJZCI6IkttNXQyMjVFOEtFQ0tRNlpEbTVLMlA2YVMyNDU5Q3VhIiwiY2xpZW50TmFtZSI6IuacrOenkeeUn-aVmeWKoeezu-e7nyIsInNjb3BlIjoianciLCJyZWRpcmVjdFVyaSI6Imh0dHBzOi8vand4dC5zaHUuZWR1LmNuL3Nzby9zaHVsb2dpbiIsInN0YXRlIjoiIiwiZG9tYWluIjoiIn0='

            # 使用新的参数格式
            encrypted_pwd = encrypt(password)
            data = {
                "username": sid,
                "password": encrypted_pwd,
            }

            logger.debug("POST 登录请求到新版SSO: {}", login_url)
            resp = self.sess.post(login_url, data=data, timeout=self.timeout)

            # 使用新的成功判断逻辑
            if '教学管理信息服务平台' not in resp.text:
                return {"code": 1002, "msg": "用户名或密码不正确"}

            # 第四步：访问首页，验证是否登录
            resp3 = self.sess.get(self.base_url, timeout=self.timeout)
            if resp3.status_code != 200 or "统一认证" in resp3.text:
                return {"code": 1005, "msg": "SSO 回跳失败"}
            logger.debug("回跳首页: status={}", resp3.status_code)

            # 第六步：访问菜单初始化页面激活会话 - 这是关键步骤！
            timestamp = int(time.time() * 1000)
            init_menu_url = f"{self.base_url}/jwglxt/xtgl/index_initMenu.html?jsdm=xs&_t={timestamp}"
            resp4 = self.sess.get(init_menu_url, timeout=self.timeout)
            logger.debug("菜单初始化: status={}, 新增cookies={}",
                         resp4.status_code, resp4.cookies.get_dict())

            if resp4.status_code != 200:
                return {"code": 1007, "msg": "菜单初始化失败"}
            # 登录成功，返回 cookies
            final_cookies = self.sess.cookies.get_dict()
            logger.info("登录成功，最终Cookies：{}", final_cookies)
            return {"code": 1000, "msg": "登录成功", "cookies": final_cookies}

        except requests.Timeout:
            return {"code": 1003, "msg": "网络请求超时"}
        except requests.RequestException as e:
            logger.error("网络请求异常：{}", e)
            return {"code": 2333, "msg": "网络请求异常"}
        except Exception as e:
            logger.exception("登录时发生未知异常")
            return {"code": 999, "msg": f"未知错误：{e}"}