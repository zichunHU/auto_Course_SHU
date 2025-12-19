import json
import os
from prettytable import PrettyTable

# 文件路径配置
COURSE_FILE_PATH = "schedule_2025_2.json"


class CourseStatusChecker:
    def __init__(self, file_path):
        self.file_path = file_path
        self.courses_data = []

    def load_data(self):
        if not os.path.exists(self.file_path):
            print(f"❌ 文件不存在: {self.file_path}")
            return False
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.courses_data = data.get("courses", []) or data.get("data", {}).get("courses", [])
            elif isinstance(data, list):
                self.courses_data = data
            return True
        except Exception as e:
            print(f"❌ 读取错误: {e}")
            return False

    def analyze_course(self, course_data):
        raw = course_data.get("raw_data", {})

        # 1. 基础信息
        title = course_data.get("title", "未知")
        teacher = course_data.get("teacher", "未知")
        credit = course_data.get("credit", 0)

        # 2. 核心数据
        base_capacity = int(raw.get("jxbrs", 0))  # 基础 (70)
        expansion = int(raw.get("krrl", 0))  # 扩容 (10)
        enrolled = int(raw.get("yxzrs", 0))  # 已选 (145)

        # 总计 = 基础 + 扩容
        total_capacity = base_capacity + expansion

        # 3. 状态判定逻辑
        # 🟢 已选上：总计 >= 已选
        # 🔴 待筛选：总计 < 已选
        # (前提是 sfxkbj=1)
        is_in_list = raw.get("sfxkbj") == "1"

        if not is_in_list:
            status_str = "⚪ 未选"
        else:
            if total_capacity >= enrolled:
                status_str = "🟢 已选上"
            else:
                status_str = "🔴 待筛选"

        # 4. 容量显示格式 (70+10 格式)
        if expansion > 0:
            capacity_display = f"{enrolled}/{base_capacity}+{expansion}"
        else:
            capacity_display = f"{enrolled}/{base_capacity}"

        # 5. 选课率
        if total_capacity > 0:
            rate = (enrolled / total_capacity) * 100
        else:
            rate = 0

        return {
            "title": title,
            "teacher": teacher,
            "credit": credit,
            "base_capacity": base_capacity,
            "expansion": expansion,
            "total_capacity": total_capacity,
            "enrolled": enrolled,
            "capacity_display": capacity_display,
            "remaining": total_capacity - enrolled,
            "rate": rate,
            "status_str": status_str,
            # 详情用
            "course_id": course_data.get("course_id"),
            "time": course_data.get("time", "").replace('\n', ' '),
            "place": course_data.get("place", "").replace('\n', ' ')
        }

    def display_table(self):
        if not self.courses_data: return

        print(f"\n📚 课程选课状况表")

        # 创建表格
        table = PrettyTable()
        table.field_names = ["序号", "课程名称", "教师", "学分", "容量 (已选/总计)", "剩余", "选课率", "课程状态"]

        # --- 优化表格对齐与显示 ---
        # 居中对齐
        table.align["序号"] = "c"
        table.align["学分"] = "c"
        table.align["容量 (已选/总计)"] = "c"
        table.align["剩余"] = "c"

        # 左对齐 (文字类)
        table.align["课程名称"] = "l"
        table.align["教师"] = "l"
        table.align["课程状态"] = "l"

        # 右对齐 (数值对比类)
        table.align["选课率"] = "r"

        # 增加内边距，不那么拥挤
        table.padding_width = 1

        processed = [self.analyze_course(c) for c in self.courses_data]

        for idx, c in enumerate(processed, 1):
            # 标题截断优化 (稍微宽一点)
            title_display = c["title"][:18] + "..." if len(c["title"]) > 18 else c["title"]

            table.add_row([
                idx,
                title_display,
                c["teacher"],
                c["credit"],
                c["capacity_display"],
                c["remaining"],
                f"{c['rate']:.1f}%",
                c["status_str"]
            ])

        print(table)
        print("注: 容量显示格式为 '已选/基础+扩容'。总计≥已选为🟢，总计<已选为🔴。")

    def display_detail(self):
        print("\n📖 课程详细信息")
        print("=" * 60)
        for idx, c_data in enumerate(self.courses_data, 1):
            c = self.analyze_course(c_data)
            print(f"{idx}. {c['title']} ({c['teacher']})")
            print(f"   🆔 课程号: {c['course_id']}")
            print(f"   👥 容量: {c['capacity_display']} (基础{c['base_capacity']} + 扩容{c['expansion']})")
            print(f"   🚩 状态: {c['status_str']}")
            print(f"   📈 选课率: {c['rate']:.2f}%")
            print(f"   ⏰ 时间: {c['time']}")
            print(f"   📍 地点: {c['place']}")
            print("-" * 40)

    def run(self):
        if not self.load_data(): return

        self.display_table()

        while True:
            print("\n[1] 显示课程详细信息  [2] 退出")
            choice = input("请输入: ").strip()
            if choice == "1":
                self.display_detail()
                self.display_table()
            elif choice == "2":
                break
            else:
                print("❌ 无效输入")


if __name__ == "__main__":
    CourseStatusChecker(COURSE_FILE_PATH).run()