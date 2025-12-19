"""
课程信息存储和读取
"""
import os
import json
import time
from typing import Dict, List, Any, Optional
from loguru import logger


class CourseStorage:
    """课程信息存储类"""

    def __init__(self, storage_dir: str = "data"):
        """
        初始化课程存储

        :param storage_dir: 存储目录
        """
        self.storage_dir = storage_dir
        self.target_file = os.path.join(storage_dir, "target_courses.json")
        self.status_file = os.path.join(storage_dir, "course_status.json")

        # 确保目录存在
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)

    def save_target_courses(self, courses: List[Dict[str, Any]]) -> bool:
        """
        保存目标课程列表

        :param courses: 课程列表
        :return: 是否成功
        """
        try:
            # 添加时间戳和基本状态
            data = {
                "timestamp": time.time(),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "courses": courses
            }

            with open(self.target_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"已保存{len(courses)}门目标课程到 {self.target_file}")
            return True
        except Exception as e:
            logger.error(f"保存目标课程失败: {e}")
            return False

    def load_target_courses(self) -> List[Dict[str, Any]]:
        """
        加载目标课程列表

        :return: 课程列表
        """
        try:
            if not os.path.exists(self.target_file):
                logger.warning(f"目标课程文件不存在: {self.target_file}")
                return []

            with open(self.target_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            courses = data.get("courses", [])
            logger.debug(f"已加载{len(courses)}门目标课程")
            return courses
        except Exception as e:
            logger.error(f"加载目标课程失败: {e}")
            return []

    def update_course_status(self, course_id: str, status: str, message: str = "") -> bool:
        """
        更新课程状态

        :param course_id: 课程ID
        :param status: 状态 (waiting, success, failed)
        :param message: 附加消息
        :return: 是否成功
        """
        try:
            # 加载现有状态
            statuses = {}
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    statuses = json.load(f)

            # 更新状态
            statuses[course_id] = {
                "status": status,
                "message": message,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            # 保存状态
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(statuses, f, ensure_ascii=False, indent=2)

            logger.debug(f"更新课程 {course_id} 状态为 {status}")
            return True
        except Exception as e:
            logger.error(f"更新课程状态失败: {e}")
            return False

    def get_course_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有课程状态

        :return: 课程状态字典
        """
        try:
            if not os.path.exists(self.status_file):
                return {}

            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"获取课程状态失败: {e}")
            return {}

    def clear_all_statuses(self) -> bool:
        """
        清除所有状态记录

        :return: 是否成功
        """
        try:
            if os.path.exists(self.status_file):
                os.remove(self.status_file)
            return True
        except Exception as e:
            logger.error(f"清除状态记录失败: {e}")
            return False
