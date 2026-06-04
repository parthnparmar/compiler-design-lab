from ll1_parser import LL1Parser
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test Case 1: Expression Grammar
print("="*60)
print("TEST 1: Expression Grammar")
print("="*60)
grammar1 = """E -> T E'
E' -> + T E' | ε
T -> F T'
T' -> * F T' | ε
F -> ( E ) | id"""

parser1 = LL1Parser()
parser1.parse_grammar(grammar1)
parser1.compute_first()
parser1.compute_follow()
is_ll1, msg = parser1.build_parsing_table()
parser1.display_results()
print(f"\n{msg}")
if is_ll1:
    parser1.parse_string("id + id * id")

# Test Case 2: Simple Grammar
print("\n\n" + "="*60)
print("TEST 2: Simple Grammar")
print("="*60)
grammar2 = """S -> A B
A -> a | ε
B -> b"""

parser2 = LL1Parser()
parser2.parse_grammar(grammar2)
parser2.compute_first()
parser2.compute_follow()
is_ll1, msg = parser2.build_parsing_table()
parser2.display_results()
print(f"\n{msg}")
if is_ll1:
    parser2.parse_string("a b")
    parser2.parse_string("b")

# Test Case 3: If-Then-Else Grammar
print("\n\n" + "="*60)
print("TEST 3: If-Then-Else Grammar")
print("="*60)
grammar3 = """S -> i E t S S' | a
S' -> e S | ε
E -> b"""

parser3 = LL1Parser()
parser3.parse_grammar(grammar3)
parser3.compute_first()
parser3.compute_follow()
is_ll1, msg = parser3.build_parsing_table()
parser3.display_results()
print(f"\n{msg}")
if is_ll1:
    parser3.parse_string("i b t a e a")
