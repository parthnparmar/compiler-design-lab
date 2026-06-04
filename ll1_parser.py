class LL1Parser:
    def __init__(self):
        self.grammar = {}
        self.terminals = set()
        self.non_terminals = set()
        self.first = {}
        self.follow = {}
        self.parsing_table = {}
        self.original_grammar = {}
        
    def add_production(self, lhs, rhs):
        if lhs not in self.grammar:
            self.grammar[lhs] = []
        self.grammar[lhs].append(rhs)
        self.non_terminals.add(lhs)
        
    def parse_grammar(self, grammar_str):
        lines = grammar_str.strip().split('\n')
        for line in lines:
            if '->' in line:
                lhs, rhs = line.split('->')
                lhs = lhs.strip()
                productions = [p.strip() for p in rhs.split('|')]
                for prod in productions:
                    self.add_production(lhs, prod)
        
        self.original_grammar = {k: v[:] for k, v in self.grammar.items()}
        
        for lhs in self.grammar:
            for prod in self.grammar[lhs]:
                for symbol in prod.split():
                    if symbol not in self.non_terminals and symbol != 'ε':
                        self.terminals.add(symbol)
    
    def remove_left_recursion(self):
        print("\n" + "="*60)
        print("STEP 1: REMOVE LEFT RECURSION")
        print("="*60)
        
        nt_list = list(self.grammar.keys())
        changed = False
        
        for i, A in enumerate(nt_list):
            # Eliminate indirect left recursion
            for j in range(i):
                B = nt_list[j]
                new_prods = []
                for prod in self.grammar[A]:
                    symbols = prod.split()
                    if symbols and symbols[0] == B:
                        for b_prod in self.grammar[B]:
                            new_prods.append(b_prod + ' ' + ' '.join(symbols[1:]) if len(symbols) > 1 else b_prod)
                        changed = True
                    else:
                        new_prods.append(prod)
                self.grammar[A] = new_prods
            
            # Eliminate direct left recursion
            alpha = []  # A -> A α
            beta = []   # A -> β
            
            for prod in self.grammar[A]:
                symbols = prod.split()
                if symbols and symbols[0] == A:
                    alpha.append(' '.join(symbols[1:]) if len(symbols) > 1 else 'ε')
                else:
                    beta.append(prod)
            
            if alpha:
                changed = True
                A_prime = A + "'"
                self.non_terminals.add(A_prime)
                
                self.grammar[A] = [b + ' ' + A_prime for b in beta]
                self.grammar[A_prime] = [a + ' ' + A_prime for a in alpha] + ['ε']
                
                print(f"\nDirect left recursion found in {A}")
                print(f"  α productions: {alpha}")
                print(f"  β productions: {beta}")
                print(f"  New {A} -> {' | '.join(self.grammar[A])}")
                print(f"  New {A_prime} -> {' | '.join(self.grammar[A_prime])}")
        
        if not changed:
            print("\nNo left recursion found.")
        
        # Update terminals
        self.terminals = set()
        for lhs in self.grammar:
            for prod in self.grammar[lhs]:
                for symbol in prod.split():
                    if symbol not in self.non_terminals and symbol != 'ε':
                        self.terminals.add(symbol)
    
    def left_factor(self):
        print("\n" + "="*60)
        print("STEP 2: LEFT FACTORING")
        print("="*60)
        
        changed = True
        iteration = 0
        
        while changed:
            changed = False
            iteration += 1
            
            for A in list(self.grammar.keys()):
                prods = self.grammar[A]
                prefixes = {}
                
                for prod in prods:
                    symbols = prod.split()
                    if symbols:
                        first_sym = symbols[0]
                        if first_sym not in prefixes:
                            prefixes[first_sym] = []
                        prefixes[first_sym].append(prod)
                
                for prefix, matching_prods in prefixes.items():
                    if len(matching_prods) > 1:
                        # Find longest common prefix
                        common = []
                        min_len = min(len(p.split()) for p in matching_prods)
                        
                        for i in range(min_len):
                            symbols_at_i = [p.split()[i] for p in matching_prods]
                            if len(set(symbols_at_i)) == 1:
                                common.append(symbols_at_i[0])
                            else:
                                break
                        
                        if common:
                            changed = True
                            A_prime = A + "'" * iteration
                            while A_prime in self.non_terminals:
                                A_prime += "'"
                            self.non_terminals.add(A_prime)
                            
                            new_A_prods = []
                            new_A_prime_prods = []
                            
                            for prod in prods:
                                symbols = prod.split()
                                if symbols[:len(common)] == common:
                                    rest = symbols[len(common):]
                                    new_A_prime_prods.append(' '.join(rest) if rest else 'ε')
                                else:
                                    new_A_prods.append(prod)
                            
                            new_A_prods.append(' '.join(common) + ' ' + A_prime)
                            self.grammar[A] = new_A_prods
                            self.grammar[A_prime] = new_A_prime_prods
                            
                            print(f"\nCommon prefix found in {A}: {' '.join(common)}")
                            print(f"  New {A} -> {' | '.join(self.grammar[A])}")
                            print(f"  New {A_prime} -> {' | '.join(self.grammar[A_prime])}")
                            break
                
                if changed:
                    break
        
        if iteration == 1:
            print("\nNo common prefixes found.")
        
        # Update terminals
        self.terminals = set()
        for lhs in self.grammar:
            for prod in self.grammar[lhs]:
                for symbol in prod.split():
                    if symbol not in self.non_terminals and symbol != 'ε':
                        self.terminals.add(symbol)
        
    def compute_first(self):
        print("\n" + "="*60)
        print("STEP 3: COMPUTE FIRST SETS")
        print("="*60)
        
        for nt in self.non_terminals:
            self.first[nt] = set()
        
        changed = True
        while changed:
            changed = False
            for lhs in self.grammar:
                for prod in self.grammar[lhs]:
                    symbols = prod.split()
                    if not symbols or symbols[0] == 'ε':
                        if 'ε' not in self.first[lhs]:
                            self.first[lhs].add('ε')
                            changed = True
                    else:
                        for i, symbol in enumerate(symbols):
                            if symbol in self.terminals:
                                if symbol not in self.first[lhs]:
                                    self.first[lhs].add(symbol)
                                    changed = True
                                break
                            else:
                                before = len(self.first[lhs])
                                self.first[lhs] |= (self.first[symbol] - {'ε'})
                                if len(self.first[lhs]) > before:
                                    changed = True
                                if 'ε' not in self.first[symbol]:
                                    break
                                if i == len(symbols) - 1:
                                    if 'ε' not in self.first[lhs]:
                                        self.first[lhs].add('ε')
                                        changed = True
        
        print("\nFIRST sets computed:")
        for nt in sorted(self.first.keys()):
            print(f"  FIRST({nt}) = {{ {', '.join(sorted(self.first[nt]))} }}")
    
    def compute_follow(self):
        print("\n" + "="*60)
        print("STEP 4: COMPUTE FOLLOW SETS")
        print("="*60)
        
        start_symbol = list(self.grammar.keys())[0]
        for nt in self.non_terminals:
            self.follow[nt] = set()
        self.follow[start_symbol].add('$')
        
        changed = True
        while changed:
            changed = False
            for lhs in self.grammar:
                for prod in self.grammar[lhs]:
                    symbols = prod.split()
                    for i, symbol in enumerate(symbols):
                        if symbol in self.non_terminals:
                            if i == len(symbols) - 1:
                                before = len(self.follow[symbol])
                                self.follow[symbol] |= self.follow[lhs]
                                if len(self.follow[symbol]) > before:
                                    changed = True
                            else:
                                rest = symbols[i+1:]
                                for next_sym in rest:
                                    if next_sym in self.terminals:
                                        if next_sym not in self.follow[symbol]:
                                            self.follow[symbol].add(next_sym)
                                            changed = True
                                        break
                                    else:
                                        before = len(self.follow[symbol])
                                        self.follow[symbol] |= (self.first[next_sym] - {'ε'})
                                        if len(self.follow[symbol]) > before:
                                            changed = True
                                        if 'ε' not in self.first[next_sym]:
                                            break
                                else:
                                    before = len(self.follow[symbol])
                                    self.follow[symbol] |= self.follow[lhs]
                                    if len(self.follow[symbol]) > before:
                                        changed = True
        
        print("\nFOLLOW sets computed:")
        for nt in sorted(self.follow.keys()):
            print(f"  FOLLOW({nt}) = {{ {', '.join(sorted(self.follow[nt]))} }}")
    
    def build_parsing_table(self):
        print("\n" + "="*60)
        print("STEP 5: CONSTRUCT PREDICTIVE PARSING TABLE")
        print("="*60)
        
        for nt in self.non_terminals:
            self.parsing_table[nt] = {}
        
        for lhs in self.grammar:
            for prod in self.grammar[lhs]:
                symbols = prod.split()
                first_of_prod = set()
                
                if not symbols or symbols[0] == 'ε':
                    first_of_prod.add('ε')
                else:
                    for symbol in symbols:
                        if symbol in self.terminals:
                            first_of_prod.add(symbol)
                            break
                        else:
                            first_of_prod |= (self.first[symbol] - {'ε'})
                            if 'ε' not in self.first[symbol]:
                                break
                    else:
                        first_of_prod.add('ε')
                
                for terminal in first_of_prod - {'ε'}:
                    if terminal in self.parsing_table[lhs]:
                        return False, f"Conflict at [{lhs}, {terminal}]"
                    self.parsing_table[lhs][terminal] = prod
                
                if 'ε' in first_of_prod:
                    for terminal in self.follow[lhs]:
                        if terminal in self.parsing_table[lhs]:
                            return False, f"Conflict at [{lhs}, {terminal}]"
                        self.parsing_table[lhs][terminal] = prod
        
        print("\nParsing table constructed successfully.")
        return True, "Grammar is LL(1)"
    
    def display_results(self):
        print("\n" + "="*60)
        print("ORIGINAL GRAMMAR:")
        print("="*60)
        for lhs in self.original_grammar:
            print(f"{lhs} -> {' | '.join(self.original_grammar[lhs])}")
        
        print("\n" + "="*60)
        print("TRANSFORMED GRAMMAR (After Step 1 & 2):")
        print("="*60)
        for lhs in self.grammar:
            print(f"{lhs} -> {' | '.join(self.grammar[lhs])}")
        
        print("\n" + "="*60)
        print("LL(1) PARSING TABLE:")
        print("="*60)
        
        all_terminals = sorted(self.terminals | {'$'})
        header = f"{'Non-Terminal':<15} | " + " | ".join(f"{t:<15}" for t in all_terminals)
        print(header)
        print("-" * len(header))
        
        for nt in sorted(self.non_terminals):
            row = f"{nt:<15} | "
            for t in all_terminals:
                if t in self.parsing_table[nt]:
                    prod = f"{nt} -> {self.parsing_table[nt][t]}"
                    row += f"{prod:<15} | "
                else:
                    row += f"{'—':<15} | "
            print(row)
    
    def parse_string(self, input_string):
        print("\n" + "="*60)
        print("STEP 6: PARSE INPUT STRING")
        print("="*60)
        print(f"Input: {input_string}")
        
        tokens = input_string.split() + ['$']
        stack = ['$', list(self.grammar.keys())[0]]
        index = 0
        
        print(f"\n{'Step':<6} {'Stack':<30} {'Input':<25} {'Action':<30}")
        print("-" * 91)
        step = 1
        
        while len(stack) > 1:
            top = stack[-1]
            current = tokens[index]
            
            stack_str = ' '.join(stack)
            input_str = ' '.join(tokens[index:])
            
            if top == current:
                action = f"Match {top}"
                print(f"{step:<6} {stack_str:<30} {input_str:<25} {action:<30}")
                stack.pop()
                index += 1
            elif top in self.non_terminals:
                if current in self.parsing_table[top]:
                    prod = self.parsing_table[top][current]
                    action = f"Apply {top} -> {prod}"
                    print(f"{step:<6} {stack_str:<30} {input_str:<25} {action:<30}")
                    stack.pop()
                    if prod != 'ε':
                        for symbol in reversed(prod.split()):
                            stack.append(symbol)
                else:
                    print(f"{step:<6} {stack_str:<30} {input_str:<25} {'ERROR: No rule':<30}")
                    return False
            else:
                print(f"{step:<6} {stack_str:<30} {input_str:<25} {'ERROR: Mismatch':<30}")
                return False
            
            step += 1
        
        print(f"{step:<6} {'$':<30} {'$':<25} {'ACCEPT':<30}")
        return True


# Example usage
if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("LL(1) PARSER - Enter your grammar")
    print("Format: E -> T E'")
    print("        E' -> + T E' | ε")
    print("(Type 'done' when finished)\n")
    
    grammar_input = ""
    while True:
        line = input()
        if line.lower() == 'done':
            break
        grammar_input += line + "\n"
    
    parser = LL1Parser()
    parser.parse_grammar(grammar_input)
    parser.remove_left_recursion()
    parser.left_factor()
    parser.compute_first()
    parser.compute_follow()
    is_ll1, message = parser.build_parsing_table()
    
    parser.display_results()
    
    print(f"\n{'='*60}")
    print(f"Result: {message}")
    print("="*60)
    
    if is_ll1:
        test_input = input("\nEnter string to parse (or press Enter to skip): ")
        if test_input:
            parser.parse_string(test_input)
