import sys
from math_utils import multiply, is_even


def main():
    print("--- Running inside Docker ---")

    val1, val2 = 6, 7
    prod = multiply(val1, val2)
    print(f"The product of {val1} and {val2} is {prod}")

    check_num = 10
    print(f"Is {check_num} even? {is_even(check_num)}")


if __name__ == "__main__":
    main()
