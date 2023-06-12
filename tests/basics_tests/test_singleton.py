import unittest

from basics import Arena
from basics.singleton import SingletonMixIn


class TestSingletonMixIn(unittest.TestCase):

    def test_single_instance(self):
        # 测试多次实例化返回的对象是否相同
        instance1 = SingletonMixIn()
        instance2 = SingletonMixIn()
        self.assertEqual(instance1, instance2)

    def test_attributes(self):
        # 测试单例实例的属性是否相同
        instance1 = SingletonMixIn()
        instance1.attr1 = "value1"
        instance2 = SingletonMixIn()
        self.assertEqual(instance2.attr1, "value1")

    def test_methods(self):
        # 测试单例实例的方法是否相同
        instance1 = SingletonMixIn()
        instance1.method1 = lambda: "result1"
        instance2 = SingletonMixIn()
        self.assertEqual(instance2.method1(), "result1")

    def test_arena(self):
        a = Arena()
        b = Arena()
        self.assertEqual(a, b)

    def test_arena2(self):
        b = Arena([None, None, None, None], [None, None, None, None])
        a = Arena()
        self.assertEqual(None, a.left[0])
