class SLRParser:
    def __init__(self):
        self.grammar = {}
        self.productions = []
        self.terminals = set()
        self.non_terminals = set()
        self.start_symbol = None
        self.augmented_start = None
        self.first = {}
        self.follow = {}
        self.states = []
        self.goto = {}
        self.action = {}
        
    def parse_grammar(self, grammar_str):
        lines = grammar_str.strip().split('\n')
        for line in lines:
            if '->' in line:
                lhs, rhs = line.split('->')
                lhs = lhs.strip()
                if self.start_symbol is None:
                    self.start_symbol = lhs
                productions = [p.strip() for p in rhs.split('|')]
                for prod in productions:
                    self.productions.append((lhs, prod))
                    if lhs not in self.grammar:
                        self.grammar[lhs] = []
                    self.grammar[lhs].append(prod)
                    self.non_terminals.add(lhs)
        
        # Augment grammar
        self.augmented_start = self.start_symbol + "'"
        self.productions.insert(0, (self.augmented_start, self.start_symbol))
        self.grammar[self.augmented_start] = [self.start_symbol]
        self.non_terminals.add(self.augmented_start)
        
        # Find terminals
        for lhs, rhs in self.productions:
            for symbol in rhs.split():
                if symbol not in self.non_terminals and symbol != 'ε':
                    self.terminals.add(symbol)
    
    def compute_first(self):
        for nt in self.non_terminals:
            self.first[nt] = set()
        
        changed = True
        while changed:
            changed = False
            for lhs, rhs in self.productions:
                symbols = rhs.split()
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
    
    def compute_follow(self):
        for nt in self.non_terminals:
            self.follow[nt] = set()
        self.follow[self.augmented_start].add('$')
        
        changed = True
        while changed:
            changed = False
            for lhs, rhs in self.productions:
                symbols = rhs.split()
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
    
    def closure(self, items):
        closure_set = set(items)
        changed = True
        while changed:
            changed = False
            new_items = set()
            for lhs, rhs, dot in closure_set:
                symbols = rhs.split() if rhs != 'ε' else []
                if dot < len(symbols) and symbols[dot] in self.non_terminals:
                    next_symbol = symbols[dot]
                    for prod_lhs, prod_rhs in self.productions:
                        if prod_lhs == next_symbol:
                            new_item = (prod_lhs, prod_rhs, 0)
                            if new_item not in closure_set:
                                new_items.add(new_item)
                                changed = True
            closure_set |= new_items
        return frozenset(closure_set)
    
    def goto_state(self, items, symbol):
        goto_set = set()
        for lhs, rhs, dot in items:
            symbols = rhs.split() if rhs != 'ε' else []
            if dot < len(symbols) and symbols[dot] == symbol:
                goto_set.add((lhs, rhs, dot + 1))
        if goto_set:
            return self.closure(goto_set)
        return frozenset()
    
    def build_canonical_collection(self):
        start_item = (self.augmented_start, self.start_symbol, 0)
        start_state = self.closure([start_item])
        self.states = [start_state]
        
        i = 0
        while i < len(self.states):
            state = self.states[i]
            symbols = set()
            for lhs, rhs, dot in state:
                symbols_list = rhs.split() if rhs != 'ε' else []
                if dot < len(symbols_list):
                    symbols.add(symbols_list[dot])
            
            for symbol in symbols:
                new_state = self.goto_state(state, symbol)
                if new_state and new_state not in self.states:
                    self.states.append(new_state)
                if new_state:
                    state_idx = self.states.index(new_state)
                    self.goto[(i, symbol)] = state_idx
            i += 1
    
    def build_parsing_table(self):
        conflicts = []
        
        for i, state in enumerate(self.states):
            self.action[i] = {}
            for lhs, rhs, dot in state:
                symbols = rhs.split() if rhs != 'ε' else []
                
                # Shift
                if dot < len(symbols) and symbols[dot] in self.terminals:
                    terminal = symbols[dot]
                    if (i, terminal) in self.goto:
                        next_state = self.goto[(i, terminal)]
                        if terminal in self.action[i]:
                            conflicts.append(f"Shift-Reduce conflict at state {i}, terminal {terminal}")
                        self.action[i][terminal] = ('shift', next_state)
                
                # Reduce
                elif dot == len(symbols):
                    if lhs == self.augmented_start:
                        self.action[i]['$'] = ('accept', 0)
                    else:
                        prod_num = self.productions.index((lhs, rhs))
                        for terminal in self.follow[lhs]:
                            if terminal in self.action[i]:
                                conflicts.append(f"Reduce-Reduce conflict at state {i}, terminal {terminal}")
                            self.action[i][terminal] = ('reduce', prod_num)
        
        return len(conflicts) == 0, conflicts
    
    def display_results(self):
        print("\n" + "="*80)
        print("STEP 1: AUGMENTED GRAMMAR")
        print("="*80)
        print("Original Start Symbol:", self.start_symbol)
        print("Augmented Start Symbol:", self.augmented_start)
        print("\nProductions:")
        for i, (lhs, rhs) in enumerate(self.productions):
            marker = " (Augmented)" if i == 0 else ""
            print(f"  {i}. {lhs} -> {rhs}{marker}")
        
        print("\n" + "="*80)
        print("STEP 2: CANONICAL COLLECTION OF LR(0) ITEMS")
        print("="*80)
        for i, state in enumerate(self.states):
            print(f"\nState I{i}:")
            for lhs, rhs, dot in sorted(state):
                symbols = rhs.split() if rhs != 'ε' else ['ε']
                prod = ' '.join(symbols[:dot]) + ' • ' + ' '.join(symbols[dot:])
                print(f"  {lhs} -> {prod}")
            
            # Show transitions
            transitions = []
            for (state_idx, symbol), next_state in self.goto.items():
                if state_idx == i:
                    transitions.append(f"{symbol} -> I{next_state}")
            if transitions:
                print(f"  Transitions: {', '.join(transitions)}")
        
        print("\n" + "="*80)
        print("STEP 3: FOLLOW SETS")
        print("="*80)
        for nt in sorted(self.follow.keys()):
            if nt != self.augmented_start:
                print(f"  FOLLOW({nt}) = {{ {', '.join(sorted(self.follow[nt]))} }}")
        
        print("\n" + "="*80)
        print("STEP 4: SLR PARSING TABLE")
        print("="*80)
        
        all_terminals = sorted(self.terminals | {'$'})
        all_non_terminals = sorted(self.non_terminals - {self.augmented_start})
        
        header = f"{'State':<8} | ACTION" + " " * 30 + "| GOTO"
        print(header)
        sub_header = f"{'':8} | " + " | ".join(f"{t:<8}" for t in all_terminals) + " | " + " | ".join(f"{nt:<8}" for nt in all_non_terminals)
        print(sub_header)
        print("-" * len(sub_header))
        
        for i in range(len(self.states)):
            row = f"{i:<8} | "
            for t in all_terminals:
                if i in self.action and t in self.action[i]:
                    action_type, value = self.action[i][t]
                    if action_type == 'shift':
                        row += f"s{value:<7} | "
                    elif action_type == 'reduce':
                        row += f"r{value:<7} | "
                    elif action_type == 'accept':
                        row += f"{'acc':<8} | "
                else:
                    row += f"{'—':<8} | "
            
            for nt in all_non_terminals:
                if (i, nt) in self.goto:
                    row += f"{self.goto[(i, nt)]:<8} | "
                else:
                    row += f"{'—':<8} | "
            print(row)
    
    def parse_string(self, input_string):
        print(f"\n{'='*80}")
        print(f"STEP 5: PARSE INPUT STRING")
        print("="*80)
        print(f"Input: {input_string}")
        print()
        
        stack = [0]
        tokens = input_string.split() + ['$']
        index = 0
        
        print(f"{'Step':<6} {'Stack':<30} {'Input':<25} {'Action':<35}")
        print("-" * 96)
        step = 1
        
        while True:
            state = stack[-1]
            token = tokens[index]
            
            stack_str = ' '.join(map(str, stack))
            input_str = ' '.join(tokens[index:])
            
            if state not in self.action or token not in self.action[state]:
                print(f"{step:<6} {stack_str:<30} {input_str:<25} {'ERROR: No action':<35}")
                print("\nParsing FAILED!")
                return False
            
            action_type, value = self.action[state][token]
            
            if action_type == 'shift':
                action = f"Shift to state {value}"
                print(f"{step:<6} {stack_str:<30} {input_str:<25} {action:<35}")
                stack.append(value)
                index += 1
            elif action_type == 'reduce':
                lhs, rhs = self.productions[value]
                symbols = rhs.split() if rhs != 'ε' else []
                action = f"Reduce by {lhs} -> {rhs}"
                print(f"{step:<6} {stack_str:<30} {input_str:<25} {action:<35}")
                
                if rhs != 'ε':
                    for _ in range(len(symbols)):
                        stack.pop()
                
                state = stack[-1]
                if (state, lhs) in self.goto:
                    stack.append(self.goto[(state, lhs)])
                else:
                    print(f"ERROR: No GOTO for state {state}, symbol {lhs}")
                    print("\nParsing FAILED!")
                    return False
            elif action_type == 'accept':
                print(f"{step:<6} {stack_str:<30} {input_str:<25} {'ACCEPT':<35}")
                print("\n" + "="*80)
                print("Parsing SUCCESSFUL!")
                print("="*80)
                return True
            
            step += 1


# Example usage
if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("="*80)
    print("SLR (SIMPLE LR) PARSER")
    print("="*80)
    print("Enter your grammar:")
    print("Format: E -> E + T | T")
    print("        T -> T * F | F")
    print("(Type 'done' when finished)\n")
    
    grammar_input = ""
    while True:
        line = input()
        if line.lower() == 'done':
            break
        grammar_input += line + "\n"
    
    parser = SLRParser()
    parser.parse_grammar(grammar_input)
    
    # STEP 1: Show Augmented Grammar
    print("\n" + "="*80)
    print("█ STEP 1: AUGMENTED GRAMMAR")
    print("="*80)
    print(f"Original Start Symbol: {parser.start_symbol}")
    print(f"Augmented Start Symbol: {parser.augmented_start}")
    print(f"\nAugmented Grammar Productions:")
    for i, (lhs, rhs) in enumerate(parser.productions):
        marker = " ← (Augmented Production)" if i == 0 else ""
        print(f"  ({i}) {lhs} → {rhs}{marker}")
    print("="*80)
    
    # STEP 2: Build Canonical Collection
    print("\n" + "="*80)
    print("█ STEP 2: CANONICAL COLLECTION OF LR(0) ITEMS")
    print("="*80)
    parser.compute_first()
    parser.build_canonical_collection()
    print(f"\n✓ Total States Generated: {len(parser.states)}\n")
    
    for i, state in enumerate(parser.states):
        print(f"╔═══ State I{i} ═══╗")
        for lhs, rhs, dot in sorted(state):
            symbols = rhs.split() if rhs != 'ε' else ['ε']
            prod = ' '.join(symbols[:dot]) + ' • ' + ' '.join(symbols[dot:])
            print(f"║  {lhs} → {prod}")
        
        # Show transitions
        transitions = []
        for (state_idx, symbol), next_state in parser.goto.items():
            if state_idx == i:
                transitions.append(f"{symbol} → I{next_state}")
        if transitions:
            print(f"║  GOTO: {', '.join(transitions)}")
        print(f"╚{'═'*20}╝")
    
    # STEP 3: Compute FOLLOW Sets
    print("\n" + "="*80)
    print("█ STEP 3: FOLLOW SETS")
    print("="*80)
    parser.compute_follow()
    print()
    for nt in sorted(parser.follow.keys()):
        if nt != parser.augmented_start:
            follow_items = ', '.join(sorted(parser.follow[nt]))
            print(f"  FOLLOW({nt}) = {{ {follow_items} }}")
    print("\n" + "="*80)
    
    # STEP 4: Build SLR Parsing Table
    print("\n" + "="*80)
    print("█ STEP 4: SLR PARSING TABLE")
    print("="*80)
    is_slr, conflicts = parser.build_parsing_table()
    
    all_terminals = sorted(parser.terminals | {'$'})
    all_non_terminals = sorted(parser.non_terminals - {parser.augmented_start})
    
    header = f"{'State':<8} | ACTION" + " " * 30 + "| GOTO"
    print(header)
    sub_header = f"{'':8} | " + " | ".join(f"{t:<8}" for t in all_terminals) + " | " + " | ".join(f"{nt:<8}" for nt in all_non_terminals)
    print(sub_header)
    print("-" * len(sub_header))
    
    for i in range(len(parser.states)):
        row = f"{i:<8} | "
        for t in all_terminals:
            if i in parser.action and t in parser.action[i]:
                action_type, value = parser.action[i][t]
                if action_type == 'shift':
                    row += f"s{value:<7} | "
                elif action_type == 'reduce':
                    row += f"r{value:<7} | "
                elif action_type == 'accept':
                    row += f"{'acc':<8} | "
            else:
                row += f"{'—':<8} | "
        
        for nt in all_non_terminals:
            if (i, nt) in parser.goto:
                row += f"{parser.goto[(i, nt)]:<8} | "
            else:
                row += f"{'—':<8} | "
        print(row)
    
    print(f"\n{'='*80}")
    if is_slr:
        print("✓ Grammar is SLR(1) - No conflicts detected")
    else:
        print("✗ Grammar is NOT SLR(1)")
        print("\nConflicts detected:")
        for conflict in conflicts:
            print(f"  - {conflict}")
    print("="*80)
    
    # STEP 5: Parse Input String
    if is_slr:
        test_input = input("\nEnter string to parse (space-separated, e.g., 'id + id * id'): ")
        if test_input:
            print(f"\n{'='*80}")
            print(f"█ STEP 5: PARSING INPUT STRING")
            print("="*80)
            print(f"Input: {test_input}")
            print()
            
            stack = [0]
            tokens = test_input.split() + ['$']
            index = 0
            
            print(f"{'Step':<6} {'Stack':<30} {'Input':<25} {'Action':<35}")
            print("-" * 96)
            step = 1
            
            while True:
                state = stack[-1]
                token = tokens[index]
                
                stack_str = ' '.join(map(str, stack))
                input_str = ' '.join(tokens[index:])
                
                if state not in parser.action or token not in parser.action[state]:
                    print(f"{step:<6} {stack_str:<30} {input_str:<25} {'ERROR: No action':<35}")
                    print("\nParsing FAILED!")
                    break
                
                action_type, value = parser.action[state][token]
                
                if action_type == 'shift':
                    action = f"Shift to state {value}"
                    print(f"{step:<6} {stack_str:<30} {input_str:<25} {action:<35}")
                    stack.append(value)
                    index += 1
                elif action_type == 'reduce':
                    lhs, rhs = parser.productions[value]
                    symbols = rhs.split() if rhs != 'ε' else []
                    action = f"Reduce by {lhs} -> {rhs}"
                    print(f"{step:<6} {stack_str:<30} {input_str:<25} {action:<35}")
                    
                    if rhs != 'ε':
                        for _ in range(len(symbols)):
                            stack.pop()
                    
                    state = stack[-1]
                    if (state, lhs) in parser.goto:
                        stack.append(parser.goto[(state, lhs)])
                    else:
                        print(f"ERROR: No GOTO for state {state}, symbol {lhs}")
                        print("\nParsing FAILED!")
                        break
                elif action_type == 'accept':
                    print(f"{step:<6} {stack_str:<30} {input_str:<25} {'ACCEPT':<35}")
                    print("\n" + "="*80)
                    print("Parsing SUCCESSFUL!")
                    print("="*80)
                    break
                
                step += 1
