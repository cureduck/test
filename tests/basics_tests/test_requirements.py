import unittest
from unittest.mock import Mock

from basics import *


class TestSelfPositionalRequirement(unittest.TestCase):

    # 测试需求检查方法是否能正确检查角色的位置是否符合要求
    def test_check(self):
        # 初始化
        positions = Position((True, 2, 3, 4))  # 创建位置对象，包含 2、3、4 三个目标位置
        requirement = SelfPositionalRequirement(positions)  # 创建自身位置需求对象
        receiver = Mock(spec=CombatantMixIn)  # 创建一个模拟 CombatantMixIn 的对象
        receiver.index = 2  # 设置该对象的 index 属性为 2，符合需求
        # 执行
        result = requirement.check(receiver)  # 调用需求检查方法并获得返回值
        # 断言
        self.assertTrue(result)  # 检查返回值是否为 True

    # 测试 __repr__ 方法是否能正确返回对象的字符串表示形式
    def test_repr(self):
        # 初始化
        positions = Position((False, 5, 6, 7))  # 创建位置对象，包含 5、6、7 三个目标位置
        requirement = SelfPositionalRequirement(positions)  # 创建自身位置需求对象
        # 执行
        result = str(requirement)  # 获得对象的字符串表示形式
        # 断言
        self.assertEqual(result, "Need Self Position: (False, 5, 6, 7)")  # 检查返回值是否为指定字符串


class TestValidTargetRequirement(unittest.TestCase):

    # 测试需求检查方法是否能正确检查角色是否有符合要求的目标
    def test_check(self):
        # 初始化
        target = Targeting(1, [0, 1, 2, 3])  # 创建定位目标对象，找到所有位置
        requirement = ValidTargetRequirement(target)  # 创建有效目标需求对象
        receiver = Mock(spec=CombatantMixIn)  # 创建一个模拟 CombatantMixIn 的对象
        receiver.index = 2  # 设置该对象的 index 属性为 2，需要在 1 号位置上存在目标
        receiver.find_target.return_value = [None, None, Mock(), None]  # 指定 find_target 方法的返回值
        # 执行
        result = requirement.check(receiver)  # 调用需求检查方法并获得返回值
        # 断言
        self.assertTrue(result)  # 检查返回值是否为 True

    # 测试 __repr__ 方法是否能正确返回对象的字符串表示形式
    # def test_repr(self):
