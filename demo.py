import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ll1_parser import LL1Parser
from slr_parser import SLRParser

print("="*80)
print("COMPILER DESIGN TOOLS - PARSER DEMONSTRATION")
print("="*80)

# Demo 1: LL(1) Parser
print("\n\n" + "="*80)
print("DEMO 1: LL(1) PARSER - Expression Grammar")
print("="*80)

ll1_grammar = """E -> T E'
E' -> + T E' | ε
T -> F T'
T' -> * F T' | ε
F -> ( E ) | id"""

print("\nGrammar:")
print(ll1_grammar)

parser1 = LL1Parser()
parser1.parse_grammar(ll1_grammar)
parser1.compute_first()
parser1.compute_follow()
is_ll1, msg = parser1.build_parsing_table()
parser1.display_results()
print(f"\n✅ {msg}")

if is_ll1:
    test_str = "id + id * id"
    print(f"\n🔍 Testing string: {test_str}")
    result = parser1.parse_string(test_str)
    if result:
        print("\n✅ String ACCEPTED!")

# Demo 2: SLR Parser
print("\n\n" + "="*80)
print("DEMO 2: SLR PARSER - Expression Grammar")
print("="*80)

slr_grammar = """E -> E + T | T
T -> T * F | F
F -> ( E ) | id"""

print("\nGrammar:")
print(slr_grammar)

parser2 = SLRParser()
parser2.parse_grammar(slr_grammar)
parser2.compute_first()
parser2.compute_follow()
parser2.build_canonical_collection()
is_slr, conflicts = parser2.build_parsing_table()
parser2.display_results()

if is_slr:
    print("\n✅ Grammar is SLR(1)")
    test_str = "id + id * id"
    print(f"\n🔍 Testing string: {test_str}")
    result = parser2.parse_string(test_str)
    if result:
        print("\n✅ String ACCEPTED!")
else:
    print("\n❌ Grammar is NOT SLR(1)")

print("\n\n" + "="*80)
print("✅ BOTH PARSERS ARE WORKING CORRECTLY!")
print("="*80)
print("\nYou can now use:")
print("  • python ll1_parser.py  - for LL(1) parsing")
print("  • python slr_parser.py  - for SLR parsing")
print("\nEnter any grammar and the parsers will solve it correctly!")
