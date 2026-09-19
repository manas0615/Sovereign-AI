import json
import random

tasks = [
    ("Easy", "add(a, b)", "Return a+b", "assert add(1, 2) == 3\nassert add(-1, 1) == 0"),
    ("Easy", "subtract(a, b)", "Return a-b", "assert subtract(5, 3) == 2\nassert subtract(0, 0) == 0"),
    ("Easy", "multiply(a, b)", "Return a*b", "assert multiply(3, 4) == 12\nassert multiply(0, 5) == 0"),
    ("Easy", "divide(a, b)", "Return a/b. Assume b != 0", "assert divide(10, 2) == 5.0\nassert divide(9, 3) == 3.0"),
    ("Easy", "is_even(n)", "Return True if n is even, else False", "assert is_even(4)\nassert not is_even(3)"),
    ("Easy", "is_odd(n)", "Return True if n is odd, else False", "assert is_odd(3)\nassert not is_odd(4)"),
    ("Easy", "square(n)", "Return n squared", "assert square(4) == 16\nassert square(0) == 0"),
    ("Easy", "cube(n)", "Return n cubed", "assert cube(3) == 27\nassert cube(-2) == -8"),
    ("Easy", "sum_list(lst)", "Return sum of numbers in lst", "assert sum_list([1, 2, 3]) == 6\nassert sum_list([]) == 0"),
    ("Easy", "max_list(lst)", "Return maximum in lst. Assume lst is not empty.", "assert max_list([1, 5, 3]) == 5\nassert max_list([-1, -5]) == -1"),
    ("Medium", "min_list(lst)", "Return minimum in lst. Assume lst is not empty.", "assert min_list([1, 5, 3]) == 1\nassert min_list([-1, -5]) == -5"),
    ("Medium", "reverse_string(s)", "Return reversed string s", "assert reverse_string('abc') == 'cba'\nassert reverse_string('') == ''"),
    ("Medium", "is_palindrome(s)", "Return True if s is palindrome", "assert is_palindrome('racecar')\nassert not is_palindrome('hello')"),
    ("Medium", "count_vowels(s)", "Count vowels (a,e,i,o,u) in s", "assert count_vowels('hello') == 2\nassert count_vowels('bcd') == 0"),
    ("Medium", "factorial(n)", "Return n factorial", "assert factorial(5) == 120\nassert factorial(0) == 1"),
    ("Medium", "fibonacci(n)", "Return nth fibonacci (0th=0, 1st=1)", "assert fibonacci(5) == 5\nassert fibonacci(0) == 0"),
    ("Medium", "list_length(lst)", "Return length of list without using len()", "assert list_length([1,2,3]) == 3\nassert list_length([]) == 0"),
    ("Medium", "remove_duplicates(lst)", "Return list with duplicates removed, preserving order", "assert remove_duplicates([1,2,2,3]) == [1,2,3]\nassert remove_duplicates([]) == []"),
    ("Medium", "merge_dicts(d1, d2)", "Merge two dicts. d2 overrides d1.", "assert merge_dicts({'a': 1}, {'b': 2}) == {'a': 1, 'b': 2}\nassert merge_dicts({'a': 1}, {'a': 2}) == {'a': 2}"),
    ("Medium", "celsius_to_fahrenheit(c)", "Convert C to F", "assert celsius_to_fahrenheit(0) == 32\nassert celsius_to_fahrenheit(100) == 212"),
    ("Easy", "fahrenheit_to_celsius(f)", "Convert F to C", "assert fahrenheit_to_celsius(32) == 0\nassert fahrenheit_to_celsius(212) == 100"),
    ("Easy", "is_positive(n)", "Return True if n > 0", "assert is_positive(5)\nassert not is_positive(0)"),
    ("Easy", "is_negative(n)", "Return True if n < 0", "assert is_negative(-5)\nassert not is_negative(0)"),
    ("Medium", "get_keys(d)", "Return list of keys in dict d", "assert set(get_keys({'a': 1, 'b': 2})) == {'a', 'b'}"),
    ("Medium", "get_values(d)", "Return list of values in dict d", "assert set(get_values({'a': 1, 'b': 2})) == {1, 2}"),
    ("Medium", "sort_list_asc(lst)", "Return list sorted ascending", "assert sort_list_asc([3, 1, 2]) == [1, 2, 3]"),
    ("Medium", "sort_list_desc(lst)", "Return list sorted descending", "assert sort_list_desc([3, 1, 2]) == [3, 2, 1]"),
    ("Hard", "gcd(a, b)", "Return greatest common divisor of a and b", "assert gcd(12, 8) == 4\nassert gcd(17, 13) == 1"),
    ("Hard", "lcm(a, b)", "Return least common multiple of a and b", "assert lcm(4, 6) == 12\nassert lcm(5, 7) == 35"),
    ("Hard", "is_prime(n)", "Return True if n is prime", "assert is_prime(7)\nassert not is_prime(4)\nassert not is_prime(1)"),
    ("Hard", "generate_primes(n)", "Return list of primes up to n inclusive", "assert generate_primes(10) == [2, 3, 5, 7]"),
    ("Hard", "binary_search(lst, target)", "Return index of target in sorted lst, or -1", "assert binary_search([1, 2, 3, 4], 3) == 2\nassert binary_search([1, 2, 3, 4], 5) == -1"),
    ("Medium", "capitalize_words(s)", "Capitalize first letter of each word", "assert capitalize_words('hello world') == 'Hello World'"),
    ("Medium", "count_words(s)", "Return number of words in s", "assert count_words('hello world') == 2\nassert count_words('') == 0"),
    ("Easy", "repeat_string(s, n)", "Return s repeated n times", "assert repeat_string('a', 3) == 'aaa'"),
    ("Medium", "find_longest_word(s)", "Return longest word in string s", "assert find_longest_word('the quick brown fox') == 'quick'"),
    ("Hard", "matrix_addition(m1, m2)", "Add two 2D matrices", "assert matrix_addition([[1, 2], [3, 4]], [[1, 1], [1, 1]]) == [[2, 3], [4, 5]]"),
    ("Hard", "flatten_list(lst)", "Flatten a list of lists", "assert flatten_list([[1, 2], [3, 4]]) == [1, 2, 3, 4]"),
    ("Medium", "is_anagram(s1, s2)", "Return True if s1 and s2 are anagrams", "assert is_anagram('listen', 'silent')\nassert not is_anagram('hello', 'world')"),
    ("Medium", "sum_of_digits(n)", "Return sum of digits of positive int n", "assert sum_of_digits(123) == 6\nassert sum_of_digits(9) == 9"),
    ("Hard", "to_binary(n)", "Return binary string representation of int n (no 0b)", "assert to_binary(10) == '1010'\nassert to_binary(0) == '0'"),
    ("Hard", "from_binary(s)", "Return int from binary string s", "assert from_binary('1010') == 10\nassert from_binary('0') == 0"),
    ("Hard", "is_perfect_square(n)", "Return True if n is a perfect square", "assert is_perfect_square(16)\nassert not is_perfect_square(15)"),
    ("Medium", "replace_char(s, old, new)", "Replace old char with new in s", "assert replace_char('hello', 'l', 'x') == 'hexxo'"),
    ("Medium", "remove_char(s, c)", "Remove all occurrences of char c in s", "assert remove_char('hello', 'l') == 'heo'"),
    ("Hard", "dict_to_list(d)", "Convert dict to list of tuples (key, val) sorted by key", "assert dict_to_list({'b': 2, 'a': 1}) == [('a', 1), ('b', 2)]"),
    ("Hard", "list_to_dict(lst)", "Convert list of tuples to dict", "assert list_to_dict([('a', 1), ('b', 2)]) == {'a': 1, 'b': 2}"),
    ("Hard", "intersect_lists(l1, l2)", "Return list of common elements", "assert sorted(intersect_lists([1, 2, 3], [2, 3, 4])) == [2, 3]"),
    ("Hard", "union_lists(l1, l2)", "Return list of all unique elements", "assert sorted(union_lists([1, 2], [2, 3])) == [1, 2, 3]"),
    ("Medium", "list_difference(l1, l2)", "Return elements in l1 not in l2", "assert sorted(list_difference([1, 2, 3], [2, 3])) == [1]")
]

out = []
for i, (diff, sig, desc, tests) in enumerate(tasks):
    out.append({
        "task_id": f"TASK-{i+1:02d}-{diff}",
        "difficulty": diff,
        "prompt": f"Write a Python function {sig} that does the following: {desc}",
        "hidden_tests": tests
    })

with open("benchmarks/tasks.json", "w") as f:
    json.dump(out, f, indent=2)
