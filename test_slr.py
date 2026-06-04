from slr_parser import SLRParser
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test Case 1: Expression Grammar
print("="*80)
print("TEST 1: Expression Grammar")
print("="*80)
grammar1 = """E -> E + T | T
T -> T * F | F
F -> ( E ) | id"""

parser1 = SLRParser()
parser1.parse_grammar(grammar1)
parser1.compute_first()
parser1.compute_follow()
parser1.build_canonical_collection()
is_slr, conflicts = parser1.build_parsing_table()
parser1.display_results()
print(f"\nGrammar is {'SLR(1)' if is_slr else 'NOT SLR(1)'}")
if is_slr:
    parser1.parse_string("id + id * id")

# Test Case 2: Simple Grammar
print("\n\n" + "="*80)
print("TEST 2: Simple Grammar (S -> A A)")
print("="*80)
grammar2 = """S -> A A
A -> a A | b"""

parser2 = SLRParser()
parser2.parse_grammar(grammar2)
parser2.compute_first()
parser2.compute_follow()
parser2.build_canonical_collection()
is_slr, conflicts = parser2.build_parsing_table()
parser2.display_results()
print(f"\nGrammar is {'SLR(1)' if is_slr else 'NOT SLR(1)'}")
if is_slr:
    parser2.parse_string("a a b b")

# Test Case 3: List Grammar
print("\n\n" + "="*80)
print("TEST 3: List Grammar")
print("="*80)
grammar3 = """S -> ( L ) | a
L -> L , S | S"""

parser3 = SLRParser()
parser3.parse_grammar(grammar3)
parser3.compute_first()
parser3.compute_follow()
parser3.build_canonical_collection()
is_slr, conflicts = parser3.build_parsing_table()
parser3.display_results()
print(f"\nGrammar is {'SLR(1)' if is_slr else 'NOT SLR(1)'}")
if is_slr:
    parser3.parse_string("( a , a )")

# Test Case 4: Assignment Grammar
print("\n\n" + "="*80)
print("TEST 4: Assignment Grammar")
print("="*80)
grammar4 = """S -> L = R | R
L -> * R | id
R -> L"""

parser4 = SLRParser()
parser4.parse_grammar(grammar4)
parser4.compute_first()
parser4.compute_follow()
parser4.build_canonical_collection()
is_slr, conflicts = parser4.build_parsing_table()
parser4.display_results()
print(f"\nGrammar is {'SLR(1)' if is_slr else 'NOT SLR(1)'}")
if is_slr:
    parser4.parse_string("id = * id")
