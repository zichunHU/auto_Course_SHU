import time
import requests

class SessionProvider:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def create(self) -> requests.Session:
        sess = requests.Session()
        sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        })
        return sess

    def init_menu(self, sess: requests.Session) -> bool:
        ts = int(time.time() * 1000)
        url = f"{self.base_url}/jwglxt/xtgl/index_initMenu.html?jsdm=xs&_t={ts}"
        try:
            resp = sess.get(url, timeout=self.timeout)
            return resp.status_code == 200
        except Exception:
            return False