"""
课程抢课系统主逻辑
"""
import time
import random
import threading
from typing import Dict, List, Any, Optional, Union, Tuple
from loguru import logger

from modules.course_selector import CourseSelector
from functions.course_storage import CourseStorage
from utils import print_status, countdown, is_interrupted, setup_interrupt_handler


class CourseSniper:
    """课程抢课系统"""

    def __init__(self, selector: CourseSelector, student_id: str, course_params: Dict):
        """
        初始化抢课系统

        :param selector: 课程选择器实例
        :param student_id: 学生ID
        :param course_params: 选课所需参数
        """
        self.selector = selector
        self.student_id = student_id
        self.course_params = course_params
        self.storage = CourseStorage()
        self.running = False
        self.successful_courses = set()  # 已成功选上的课程

        # 默认配置
        self.config = {
            "interval_min": 1,  # 最小间隔时间(秒)
            "interval_max": 3,  # 最大间隔时间(秒)
            "max_attempts": 100,  # 每门课最大尝试次数
            "randomize": True,  # 是否随机顺序
            "backoff_factor": 1.5  # 退避系数(连续失败时增加等待时间)
        }

    def configure(self, **kwargs):
        """
        配置抢课参数

        :param kwargs: 配置参数
        """
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
                logger.debug(f"设置配置 {key}={value}")

        return self

    def add_target_courses(self, courses: List[Dict[str, Any]]) -> bool:
        """
        添加目标课程

        :param courses: 课程列表
        :return: 是否成功
        """
        # 确保课程数据完整
        valid_courses = []
        for course in courses:
            # 检查必要字段
            if not all(k in course for k in ['kch_id', 'jxb_id']):
                logger.warning(f"课程数据不完整，跳过: {course.get('kcmc', '未知课程')}")
                continue
            valid_courses.append(course)

        if not valid_courses:
            logger.error("没有有效的课程数据")
            return False

        # 保存到存储
        return self.storage.save_target_courses(valid_courses)

    def load_target_courses(self) -> List[Dict[str, Any]]:
        """
        加载目标课程

        :return: 课程列表
        """
        return self.storage.load_target_courses()

    def _select_single_course(self, course: Dict[str, Any]) -> Tuple[bool, str]:
        """
        选择单个课程

        :param course: 课程信息
        :return: (是否成功, 消息)
        """
        try:
            # 课程基本信息
            kch_id = course.get('kch_id')
            jxb_id = course.get('jxb_id')
            kcmc = course.get('jxbmc')

            # 如果已经成功选上，跳过
            if kch_id in self.successful_courses:
                return True, "已经成功选上"

            # 执行选课
            result = self.selector.select_course(
                student_id=self.student_id,
                course=course,
                params=self.course_params
            )

            # 处理结果
            if result["code"] == 1000:
                self.successful_courses.add(kch_id)
                return True, "选课成功"
            else:
                return False, result.get("msg", "未知错误")

        except Exception as e:
            logger.exception(f"选课异常: {e}")
            return False, f"选课异常: {str(e)}"

    def start(self, max_duration: int = 0) -> Dict[str, Any]:
        """
        开始抢课

        :param max_duration: 最大运行时间(秒)，0表示无限制
        :return: 抢课结果统计
        """
        # 设置中断处理
        setup_interrupt_handler()

        # 加载目标课程
        target_courses = self.load_target_courses()
        if not target_courses:
            print_status("没有找到目标课程，请先添加", "error")
            return {"success": 0, "failed": 0, "total": 0}

        # 显示抢课信息
        print_status(f"开始抢课任务 - 目标课程数: {len(target_courses)}", "info")
        for i, course in enumerate(target_courses, 1):
            print(f"  {i}. {course.get('jxbmc', '未知课程')} (课程号: {course.get('kch_id')})")

        # 初始化统计数据
        stats = {
            "start_time": time.time(),
            "total_courses": len(target_courses),
            "successful": 0,
            "attempts": 0,
            "course_attempts": {c.get('kch_id', f'unknown_{i}'): 0 for i, c in enumerate(target_courses)},
            "completed": False,
            "successful_courses": {}
        }

        # 设置运行状态
        self.running = True
        end_time = time.time() + max_duration if max_duration > 0 else float('inf')

        # 初始化每个课程的尝试次数和退避系数
        attempt_counts = {c.get('kch_id', f'unknown_{i}'): 0 for i, c in enumerate(target_courses)}
        backoff_factors = {c.get('kch_id', f'unknown_{i}'): 1.0 for i, c in enumerate(target_courses)}

        try:
            # 主循环 - 直到所有课程都选上或超时
            while self.running:
                # 检查是否所有课程都已选上
                if len(self.successful_courses) >= len(target_courses):
                    print_status("所有课程已选上，抢课任务完成！", "success")
                    stats["completed"] = True
                    break

                # 检查是否超时
                if time.time() > end_time:
                    print_status(f"已达到最大运行时间 ({max_duration}秒)，停止抢课", "warning")
                    break

                # 检查是否被中断
                if is_interrupted():
                    print_status("抢课任务被用户中断", "warning")
                    break

                # 创建可选课程的副本
                available_courses = [c for c in target_courses if c.get('kch_id') not in self.successful_courses]

                # 如果配置为随机顺序，打乱课程顺序
                if self.config["randomize"]:
                    random.shuffle(available_courses)

                # 循环尝试每门课
                for course in available_courses:
                    # 如果被中断，退出循环
                    if is_interrupted():
                        break

                    kch_id = course.get('kch_id', 'unknown')
                    kcmc = course.get('kcmc', '未知课程')

                    # 检查最大尝试次数
                    max_attempts = self.config["max_attempts"]
                    if max_attempts > 0 and attempt_counts[kch_id] >= max_attempts:
                        print_status(f"课程 [{kcmc}] 已达到最大尝试次数 ({max_attempts}次)，跳过", "warning")
                        continue

                    # 增加尝试次数
                    attempt_counts[kch_id] += 1
                    stats["attempts"] += 1
                    stats["course_attempts"][kch_id] += 1

                    # 尝试选课
                    print_status(f"尝试选课 [{kcmc}] (第 {attempt_counts[kch_id]} 次)", "attempt")
                    success, message = self._select_single_course(course)

                    # 更新状态
                    status = "success" if success else "failed"
                    self.storage.update_course_status(kch_id, status, message)

                    # 处理结果
                    if success:
                        print_status(f"课程 [{kcmc}] 选课成功！", "success")
                        stats["successful"] += 1
                        stats["successful_courses"][kch_id] = kcmc
                        # 重置该课程的退避系数
                        backoff_factors[kch_id] = 1.0
                    else:
                        print_status(f"课程 [{kcmc}] 选课失败: {message}", "error")
                        # 增加退避系数
                        backoff_factors[kch_id] *= self.config["backoff_factor"]

                    # 计算下一次尝试的等待时间
                    interval_min = self.config["interval_min"]
                    interval_max = self.config["interval_max"]
                    backoff = min(5.0, backoff_factors[kch_id])  # 限制最大退避系数

                    wait_time = random.uniform(
                        interval_min * backoff,
                        interval_max * backoff
                    )

                    # 等待一段时间再尝试下一门课
                    if not is_interrupted() and len(self.successful_courses) < len(target_courses):
                        time.sleep(min(wait_time, 10.0))  # 限制最大等待时间为10秒

                # 所有课程尝试一轮后，等待一段时间再开始下一轮
                if not is_interrupted() and len(self.successful_courses) < len(target_courses):
                    next_round_wait = random.uniform(self.config["interval_min"], self.config["interval_max"])
                    print_status(f"本轮抢课完成，等待 {next_round_wait:.1f} 秒后开始下一轮...", "info")
                    time.sleep(next_round_wait)

        except Exception as e:
            logger.exception(f"抢课过程发生异常: {e}")
            print_status(f"抢课过程发生异常: {e}", "error")

        finally:
            # 结束抢课，更新统计信息
            self.running = False
            stats["end_time"] = time.time()
            stats["duration"] = stats["end_time"] - stats["start_time"]
            stats["successful"] = len(self.successful_courses)

            # 显示最终结果
            print_status(
                f"抢课任务结束 - 成功: {stats['successful']}/{stats['total_courses']}, 总尝试次数: {stats['attempts']}",
                "success" if stats["successful"] > 0 else "info")

            return stats
