import sys
import time
from modules.tools.display import display_course_info, select_course_interactive, display_schedule_text, export_schedule_json, display_exam_text, export_exam_json
from modules.tools.debug_utils import init_logger
from modules.services.login_service import LoginService
from modules.services.param_service import ParamService
from modules.services.search_service import SearchService
from modules.services.select_service import SelectService
from functions.course_sniper import CourseSniper
from functions.course_storage import CourseStorage

class AppOrchestrator:
    def __init__(self, base_url: str, sid: str, pwd: str, year: int, term: int, debug_flag: bool = True):
        self.base_url = base_url
        self.sid = sid
        self.pwd = pwd
        self.year = year
        self.term = term
        self.debug_flag = debug_flag
        self.log_path = init_logger(self.debug_flag)
        self.login = LoginService(self.base_url)
        self.selector = None
        self.sniper = None
        self.course_params = None
        self.storage = CourseStorage()

    def _login_and_prepare(self) -> bool:
        res_login = self.login.login(self.sid, self.pwd)
        if res_login["code"] != 1000:
            print(f"登录失败：{res_login['msg']}")
            return False
        params_result = ParamService(self.login.sess, self.base_url).extract()
        if params_result["code"] != 1000:
            print(f"提取选课参数失败：{params_result['msg']}")
            return False
        self.course_params = params_result["data"]
        self.selector = SelectService(self.login.sess, self.base_url)
        self.sniper = CourseSniper(self.selector.selector, self.sid, self.course_params)
        return True

    def run_assistant(self):
        print(f"日志文件：{self.log_path}")
        if not self._login_and_prepare():
            sys.exit(1)
        print("\n✅ 成功提取选课参数")
        while True:
            print("\n========== 上海大学选课助手 ==========")
            print("1. 搜索课程并添加到抢课列表")
            print("2. 查看当前抢课列表")
            print("3. 开始抢课")
            print("4. 清空抢课列表")
            print("5. 查看当前课表")
            print("6. 查看考试信息")
            print("0. 退出程序")
            choice = input("\n请选择功能: ")
            if choice == '0':
                print("\n程序已退出，感谢使用！")
                break
            elif choice == '1':
                self.search_and_add_courses()
            elif choice == '2':
                self.display_target_courses()
            elif choice == '3':
                self.start_course_sniping()
            elif choice == '4':
                if self.storage.clear_all_statuses():
                    self.storage.save_target_courses([])
                    print("\n✅ 抢课列表已清空")
                else:
                    print("\n❌ 清空抢课列表失败")
            elif choice == '5':
                self.view_current_schedule()
            elif choice == '6':
                self.view_exam_schedule()
            else:
                print("\n❌ 无效的选择，请重新输入")

    def search_and_add_courses(self):
        searcher = SearchService(self.login.sess, self.base_url)
        target_courses = []
        while True:
            keyword = input("\n请输入要搜索的课程关键词 (输入'0'退出, 输入'done'完成添加): ")
            if keyword == '0':
                return
            if keyword == 'done':
                break
            if not keyword:
                print("请输入有效的关键词")
                continue
            search_result = searcher.search(
                student_id=self.sid,
                params=self.course_params,
                year=self.year,
                term=self.term,
                kklxdm="01",
                kspage=1,
                jspage=50,
                keyW=keyword
            )
            if search_result["code"] == 1000:
                if not search_result["data"]:
                    print("❌ 暂无课程数据")
                    print("\n可能原因:")
                    print("1. 当前不是选课时间")
                    print("2. 学年学期设置不正确（当前设置：{}-{} 学年，第{}学期）".format(self.year, self.year + 1, self.term))
                    print("3. 没有符合条件的课程")
                    continue
                display_course_info({"courses": search_result["data"]})
                add_option = input("\n是否要添加课程到抢课列表? (y/n): ").lower()
                if add_option == 'y':
                    selected_course = select_course_interactive(search_result["data"])
                    if selected_course:
                        target_courses.append(selected_course)
                        print(f"\n✅ 已添加 {selected_course.get('kcmc', '未知课程')} 到抢课列表")
                    else:
                        print("\n已取消添加")
            else:
                print(f"搜索课程失败：{search_result['msg']}")
        if target_courses:
            if self.sniper.add_target_courses(target_courses):
                print(f"\n✅ 成功添加 {len(target_courses)} 门课程到抢课列表")
            else:
                print("\n❌ 添加课程到抢课列表失败")
        else:
            print("\n未添加任何课程")

    def display_target_courses(self):
        courses = self.sniper.load_target_courses()
        if not courses:
            print("\n❌ 抢课列表为空，请先添加课程")
            return
        print("\n========== 当前抢课列表 ==========")
        print(f"共 {len(courses)} 门课程:")
        for i, course in enumerate(courses, 1):
            print(f"{i}. {course.get('kcmc', '未知课程')}")
            print(f"   课程号: {course.get('kch_id', '未知')}")
            print(f"   教学班: {course.get('jxbmc', '未知')}")
            if i < len(courses):
                print("-" * 40)

    def start_course_sniping(self):
        courses = self.sniper.load_target_courses()
        if not courses:
            print("\n❌ 抢课列表为空，请先添加课程")
            return
        print("\n========== 抢课配置 ==========")
        print("请设置抢课参数:")
        try:
            interval_min = int(input("最小间隔时间(秒，默认1): ") or "1")
            interval_max = int(input("最大间隔时间(秒，默认3): ") or "3")
            max_attempts = int(input("每门课最大尝试次数(默认100，0表示无限): ") or "100")
            randomize = input("是否随机选课顺序(y/n，默认y): ").lower() != 'n'
        except ValueError:
            print("\n❌ 输入无效，使用默认值")
            interval_min = 1
            interval_max = 3
            max_attempts = 100
            randomize = True
        self.sniper.configure(
            interval_min=interval_min,
            interval_max=interval_max,
            max_attempts=max_attempts,
            randomize=randomize
        )
        print("\n========== 开始抢课 ==========")
        print(f"目标课程: {len(courses)} 门")
        print(f"尝试间隔: {interval_min}-{interval_max} 秒")
        print(f"最大尝试: {'无限' if max_attempts == 0 else max_attempts} 次/每门课")
        print("抢课顺序: " + ("随机" if randomize else "顺序"))
        print("\n按 Ctrl+C 可随时中止抢课")
        countdown_seconds = 3
        for i in range(countdown_seconds, 0, -1):
            print(f"\r准备开始... {i} ", end="", flush=True)
            time.sleep(1)
        print("\r开始抢课!             ")
        try:
            max_duration = 0
            result = self.sniper.start(max_duration)
            print("\n========== 抢课结束 ==========")
            print(f"尝试次数: {result.get('attempts', 0)}")
            print(f"成功课程: {result.get('successful', 0)}/{result.get('total_courses', 0)}")
            if result.get('successful', 0) > 0 and 'successful_courses' in result:
                print("\n成功选上的课程:")
                for course_id, course_name in result['successful_courses'].items():
                    print(f"- {course_name} (课程号: {course_id})")
        except KeyboardInterrupt:
            print("\n\n抢课已手动中止")

    def view_current_schedule(self):
        from modules.services.schedule_service import ScheduleService
        svc = ScheduleService(self.login.sess, self.base_url)
        res = svc.get(self.year, self.term, self.sid)
        if res.get("code") != 1000:
            print(f"\n❌ 获取课表失败：{res.get('msg')}")
            return
        data = res.get("data", {})
        display_schedule_text(data, self.year, self.term)
        opt = input("\n是否导出为 JSON 文件? (y/n): ").lower()
        if opt == 'y':
            filename = f"schedule_{self.year}_{self.term}.json"
            export_schedule_json(data, filename)
    def view_exam_schedule(self):
        from modules.services.exam_service import ExamService
        svc = ExamService(self.login.sess, self.base_url)
        res = svc.get(self.year, self.term, self.sid)
        if res.get("code") != 1000:
            print(f"\n❌ 获取考试信息失败：{res.get('msg')}")
            return
        data = res.get("data", {})
        display_exam_text(data)
        opt = input("\n是否导出为 JSON 文件? (y/n): ").lower()
        if opt == 'y':
            filename = f"exams_{self.year}_{self.term}.json"
            export_exam_json(data, filename)