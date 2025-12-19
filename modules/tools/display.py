import json
import os
from datetime import datetime
from tabulate import tabulate


def select_course_interactive(courses):
    """
    交互式选择课程
    :param courses: 课程列表
    :return: 选中的课程或None
    """
    if not courses:
        print("❌ 没有可选的课程")
        return None

    print(f"\n📚 共找到 {len(courses)} 门课程，请选择要选的课程:")

    # 显示课程列表
    for i, course in enumerate(courses, 1):
        print(
            f"{i}. {course.get('jxbmc', '未知')} - {course.get('kch_id', '未知')} - 教学班:{course.get('jxb_id', '未知')[:10]}...")

    print("0. 取消选课")

    # 获取用户选择
    while True:
        try:
            choice = input("\n请输入课程序号: ")
            if choice == "0":
                return None

            choice = int(choice)
            if 1 <= choice <= len(courses):
                selected_course = courses[choice - 1]

                # 确认选择
                print(f"\n您选择了: {selected_course.get('kcmc', '未知')}")
                print(f"课程号: {selected_course.get('kch_id', '未知')}")
                print(f"教学班ID: {selected_course.get('jxb_id', '未知')}")

                confirm = input("\n确认选择这门课程? (y/n): ").lower()
                if confirm == "y":
                    return selected_course
                else:
                    print("已取消选择，请重新选择")
            else:
                print("❌ 无效的选择，请输入1-{}之间的数字".format(len(courses)))
        except ValueError:
            print("❌ 请输入有效的数字")

def display_schedule_text(data, year=None, term=None):
    """
    显示课表文本
    :param data: 课表数据字典
    :param year: 学年（如果data中没有则使用此参数）
    :param term: 学期（如果data中没有则使用此参数）
    """
    courses = data.get("courses", [])

    # 获取年份和学期信息
    display_year = data.get("year", year or "未知")
    display_term = data.get("term", term or "未知")
    course_count = data.get("count", len(courses))

    print(f"\n📚 课表信息")
    print(f"学年：{display_year}，学期：{display_term}，共 {course_count} 门课程")

    if not courses:
        print("❌ 暂无课程数据")
        return

    # 显示课程列表
    for i, course in enumerate(courses, 1):
        print(f"\n{i}. {course.get('title', '未知课程')}")
        print(f"   课程号：{course.get('course_id', '未知')}")
        print(f"   教师：{course.get('teacher', '未知')}")
        print(f"   学分：{course.get('credit', '未知')}")
        print(f"   时间：{course.get('time', '未知')}")
        print(f"   地点：{course.get('place', '未知')}")

def display_course_info(data):
    """
    显示课程信息，重点提取指定字段
    :param data: 包含课程信息的字典
    """
    courses = data.get("courses", [])

    if not courses:
        print("❌ 暂无课程数据")
        return

    print(f"\n📚 共找到 {len(courses)} 门课程")

    # 准备表格数据
    table_data = []
    headers = ["序号", "教学班名称", "课程名称", "课程号", "教学班ID"]

    for i, course in enumerate(courses, 1):
        row = [
            i,
            course.get('jxbmc', '未知'),
            course.get('kcmc', '未知'),
            course.get('kch_id', '未知'),
            course.get('jxb_id', '未知'),
        ]
        table_data.append(row)

    # 使用tabulate显示表格
    try:
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    except ImportError:
        # 如果没有安装tabulate，使用简单格式显示
        print("\n" + " | ".join(headers))
        print("-" * 80)
        for row in table_data:
            print(" | ".join(str(item) for item in row))


def export_course_json(data, filename=None):
    """
    将课程信息导出为JSON文件
    :param data: 课程数据列表
    :param filename: 输出文件名，如果未提供则自动生成
    :return: 保存的文件路径
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"courses_{timestamp}.json"

    # 确保目录存在
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    # 准备导出数据
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "total": len(data),
        "courses": data
    }

    # 写入文件
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 课程数据已保存到: {os.path.abspath(filename)}")
    return os.path.abspath(filename)

def export_schedule_json(data: dict, filename: str):
    """
    将课表数据导出为 JSON 文件。
    :param data: ScheduleExtractor.get_schedule 返回的 data 部分
    :param filename: 输出文件名
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已导出到 {filename}")
def display_exam_text(data):
    courses = data.get("courses", [])
    year = data.get("year")
    term = data.get("term")
    count = data.get("count", len(courses))
    print(f"\n📚 考试信息")
    print(f"学年：{year}，学期：{term}，共 {count} 场考试")
    if not courses:
        print("❌ 暂无考试数据")
        return
    headers = ["序号","课程","考试时间","地点","校区","座号","方式","考试批次"]
    table = []
    for i, c in enumerate(courses, 1):
        table.append([
            i,
            c.get("title",""),
            c.get("time",""),
            c.get("location",""),
            c.get("campus",""),
            c.get("seat",""),
            c.get("method",""),
            c.get("exam_name",""),
        ])
    try:
        print(tabulate(table, headers=headers, tablefmt="grid"))
    except ImportError:
        print("\n"+" | ".join(headers))
        print("-"*80)
        for row in table:
            print(" | ".join(str(x) for x in row))
def export_exam_json(data, filename=None):
    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exams_{ts}.json"
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已导出到 {filename}")