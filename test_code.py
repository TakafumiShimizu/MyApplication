"""Pythonのテスト用サンプルコード。"""


def add(a: int, b: int) -> int:
    """2つの整数を足して返す。"""
    return a + b


if __name__ == "__main__":
    x, y = 2, 3
    print(f"{x} + {y} = {add(x, y)}")
