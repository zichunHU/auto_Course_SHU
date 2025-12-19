from modules.login import LoginClient
from modules.session_provider import SessionProvider
from functions.result import ok, err

class LoginService:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.client = LoginClient(base_url, timeout)
        self.provider = SessionProvider(base_url, timeout)

    def login(self, sid: str, pwd: str):
        res = self.client.login(sid, pwd)
        if res.get("code") != 1000:
            return res
        init_ok = self.provider.init_menu(self.client.sess)
        if not init_ok:
            return err(1007, "菜单初始化失败")
        return ok(res.get("cookies", {}), "登录成功")

    @property
    def sess(self):
        return self.client.sess