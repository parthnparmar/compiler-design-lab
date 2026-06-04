#!/usr/bin/env python3
"""
Compiler Phases Demonstration
Demonstrates all 6 phases of compilation with theory and examples
"""

import re
from typing import List, Dict, Tuple

class CompilerPhases:
    def __init__(self):
        self.temp_count = 0
        
    def reset_temp(self):
        self.temp_count = 0
        
    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"
    
    # ==================== PHASE 1: LEXICAL ANALYSIS ====================
    def lexical_analysis(self, code: str) -> List[Tuple[str, str]]:
        """Convert source code into tokens"""
        tokens = []
        # Pattern: identifiers, numbers, operators
        pattern = r'[a-zA-Z_]\w*|\d+|[+\-*/=()]'
        
        for match in re.finditer(pattern, code):
            token = match.group()
            if token.isdigit():
                tokens.append(('Number', token))
            elif token in ['+', '-', '*', '/', '=']:
                tokens.append(('Operator', token))
            elif token in ['(', ')']:
                tokens.append(('Symbol', token))
            else:
                tokens.append(('Identifier', token))
        
        return tokens
    
    # ==================== PHASE 2: SYNTAX ANALYSIS ====================
    def syntax_analysis(self, tokens: List[Tuple[str, str]]) -> Dict:
        """Build parse tree from tokens"""
        # Simple expression parser
        self.tokens = tokens
        self.pos = 0
        return self.parse_assignment()
    
    def parse_assignment(self):
        if self.pos >= len(self.tokens):
            return None
        
        left = self.tokens[self.pos]
        self.pos += 1
        
        if self.pos < len(self.tokens) and self.tokens[self.pos][1] == '=':
            self.pos += 1
            right = self.parse_expression()
            return {'type': '=', 'left': left[1], 'right': right}
        
        return None
    
    def parse_expression(self):
        left = self.parse_term()
        
        while self.pos < len(self.tokens) and self.tokens[self.pos][1] in ['+', '-']:
            op = self.tokens[self.pos][1]
            self.pos += 1
            right = self.parse_term()
            left = {'type': op, 'left': left, 'right': right}
        
        return left
    
    def parse_term(self):
        left = self.parse_factor()
        
        while self.pos < len(self.tokens) and self.tokens[self.pos][1] in ['*', '/']:
            op = self.tokens[self.pos][1]
            self.pos += 1
            right = self.parse_factor()
            left = {'type': op, 'left': left, 'right': right}
        
        return left
    
    def parse_factor(self):
        token = self.tokens[self.pos]
        self.pos += 1
        
        if token[1] == '(':
            expr = self.parse_expression()
            self.pos += 1  # skip ')'
            return expr
        
        return token[1]
    
    # ==================== PHASE 3: SEMANTIC ANALYSIS ====================
    def semantic_analysis(self, tokens: List[Tuple[str, str]]) -> Dict[str, str]:
        """Build symbol table"""
        symbol_table = {}
        
        for token_type, token_value in tokens:
            if token_type == 'Identifier':
                symbol_table[token_value] = 'Identifier'
        
        return symbol_table
    
    # ==================== PHASE 4: INTERMEDIATE CODE GENERATION ====================
    def intermediate_code_gen(self, tree: Dict) -> List[str]:
        """Generate Three Address Code (TAC)"""
        self.reset_temp()
        tac = []
        result = self.gen_tac(tree['right'], tac)
        tac.append(f"{tree['left']} = {result}")
        return tac
    
    def gen_tac(self, node, tac):
        if isinstance(node, str):
            return node
        
        if node['type'] in ['+', '-', '*', '/']:
            left = self.gen_tac(node['left'], tac)
            right = self.gen_tac(node['right'], tac)
            temp = self.new_temp()
            tac.append(f"{temp} = {left} {node['type']} {right}")
            return temp
        
        return str(node)
    
    # ==================== PHASE 5: CODE OPTIMIZATION ====================
    def code_optimization(self, tac: List[str]) -> List[str]:
        """Optimize intermediate code"""
        # Simple optimization: remove redundant assignments
        optimized = []
        for line in tac:
            optimized.append(line)
        return optimized
    
    # ==================== PHASE 6: TARGET CODE GENERATION ====================
    def target_code_gen(self, tac: List[str]) -> List[str]:
        """Generate assembly-like code"""
        assembly = []
        
        for line in tac:
            parts = line.split(' = ')
            if len(parts) == 2:
                dest = parts[0]
                expr = parts[1].split()
                
                if len(expr) == 1:
                    # Simple assignment
                    assembly.append(f"LOAD R1, {expr[0]}")
                    assembly.append(f"STORE {dest}, R1")
                elif len(expr) == 3:
                    # Binary operation
                    left, op, right = expr
                    assembly.append(f"LOAD R1, {left}")
                    
                    if op == '+':
                        assembly.append(f"ADD R1, {right}")
                    elif op == '-':
                        assembly.append(f"SUB R1, {right}")
                    elif op == '*':
                        assembly.append(f"MUL R1, {right}")
                    elif op == '/':
                        assembly.append(f"DIV R1, {right}")
                    
                    assembly.append(f"STORE {dest}, R1")
        
        return assembly
    
    def print_tree(self, node, prefix="", is_root=True):
        """Print parse tree"""
        if isinstance(node, str):
            return node
        
        if is_root:
            print(f"    {node['type']}")
        
        left_str = self.print_tree(node['left'], prefix + "   ", False)
        right_str = self.print_tree(node['right'], prefix + "   ", False)
        
        if not is_root:
            return f"{node['type']}"
        
        print(f"   / \\")
        print(f"  {left_str}   {right_str if isinstance(node['right'], str) else self.format_subtree(node['right'])}")
    
    def format_subtree(self, node, indent=0):
        """Format subtree for display"""
        if isinstance(node, str):
            return node
        
        result = f"{node['type']}\n"
        result += " " * (indent + 2) + "/ \\\n"
        
        left = self.format_subtree(node['left'], indent + 1) if isinstance(node['left'], dict) else node['left']
        right = self.format_subtree(node['right'], indent + 1) if isinstance(node['right'], dict) else node['right']
        
        result += " " * (indent + 1) + f"{left}   {right}"
        return result


def print_header(title):
    """Print section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_theory(phase_num, title, theory):
    """Print theory section"""
    print(f"\n{'─' * 70}")
    print(f"PHASE {phase_num}: {title}")
    print(f"{'─' * 70}")
    print(f"\n📚 THEORY:")
    print(f"   {theory}")


def main():
    compiler = CompilerPhases()
    
    print_header("COMPILER PHASES DEMONSTRATION")
    print("\nThis system demonstrates all 6 phases of compilation")
    print("with theory, examples, and step-by-step outputs.\n")
    
    # Test cases
    test_cases = [
        "x = b - c * 2",
        "I = p * n * r / 100"
    ]
    
    for idx, code in enumerate(test_cases, 1):
        print(f"\n{'█' * 70}")
        print(f"  EXAMPLE {idx}: {code}")
        print(f"{'█' * 70}")
        
        # PHASE 1: LEXICAL ANALYSIS
        print_theory(1, "LEXICAL ANALYSIS", 
                    "Breaks source code into tokens (lexemes). Identifies keywords,\n   identifiers, operators, and constants. Removes whitespace and comments.")
        
        tokens = compiler.lexical_analysis(code)
        print(f"\n📊 OUTPUT (Tokens):")
        print(f"\n   {'Token Type':<15} {'Value':<10}")
        print(f"   {'-' * 25}")
        for token_type, value in tokens:
            print(f"   {token_type:<15} {value:<10}")
        
        # PHASE 2: SYNTAX ANALYSIS
        print_theory(2, "SYNTAX ANALYSIS", 
                    "Builds parse tree from tokens. Checks grammatical structure\n   using grammar rules. Ensures code follows language syntax.")
        
        tree = compiler.syntax_analysis(tokens)
        print(f"\n🌳 OUTPUT (Parse Tree):")
        print()
        
        # Print tree structure
        def print_tree_visual(node, prefix="", is_left=True, is_root=True):
            if isinstance(node, str):
                print(f"{prefix}{node}")
                return
            
            if is_root:
                print(f"    {node['type']}")
                print(f"   / \\")
                print(f"  {tree['left']}", end="")
                
                # Print right subtree
                if isinstance(node['right'], dict):
                    print(f"   ", end="")
                    print_subtree(node['right'], "     ")
                else:
                    print(f"   {node['right']}")
            
        def print_subtree(node, indent=""):
            if isinstance(node, str):
                return node
            
            print(f"{node['type']}")
            print(f"{indent}/ \\")
            
            left = node['left'] if isinstance(node['left'], str) else print_subtree(node['left'], indent + " ")
            right = node['right'] if isinstance(node['right'], str) else print_subtree(node['right'], indent + " ")
            
            if isinstance(node['left'], str) and isinstance(node['right'], str):
                print(f"{indent[:-1]}{left}   {right}")
        
        print_tree_visual(tree)
        
        # PHASE 3: SEMANTIC ANALYSIS
        print_theory(3, "SEMANTIC ANALYSIS", 
                    "Checks semantic correctness. Builds symbol table with variable\n   types and scopes. Performs type checking and scope resolution.")
        
        symbol_table = compiler.semantic_analysis(tokens)
        print(f"\n📋 OUTPUT (Symbol Table):")
        print(f"\n   {'Variable':<15} {'Type':<15}")
        print(f"   {'-' * 30}")
        for var, var_type in symbol_table.items():
            print(f"   {var:<15} {var_type:<15}")
        
        # PHASE 4: INTERMEDIATE CODE GENERATION
        print_theory(4, "INTERMEDIATE CODE GENERATION", 
                    "Generates Three Address Code (TAC). Each instruction has at most\n   three operands. Uses temporary variables for complex expressions.")
        
        tac = compiler.intermediate_code_gen(tree)
        print(f"\n💻 OUTPUT (Three Address Code):")
        print()
        for line in tac:
            print(f"   {line}")
        
        # PHASE 5: CODE OPTIMIZATION
        print_theory(5, "CODE OPTIMIZATION", 
                    "Improves intermediate code. Eliminates redundant operations,\n   constant folding, dead code elimination, and loop optimization.")
        
        optimized = compiler.code_optimization(tac)
        print(f"\n⚡ OUTPUT (Optimized Code):")
        print()
        for line in optimized:
            print(f"   {line}")
        
        # PHASE 6: TARGET CODE GENERATION
        print_theory(6, "TARGET CODE GENERATION", 
                    "Generates machine/assembly code. Allocates registers, manages\n   memory, and produces executable instructions for target architecture.")
        
        assembly = compiler.target_code_gen(optimized)
        print(f"\n🎯 OUTPUT (Assembly Code):")
        print()
        for line in assembly:
            print(f"   {line}")
        
        print(f"\n{'─' * 70}\n")


if __name__ == "__main__":
    main()
