class LL1Parser:
    def __init__(self):
        self.first = {}
        self.follow = {}
        self.parsing_table = {}
        self.original_grammar = {}
        self.after_left_recursion = {}
        self.after_left_factoring = {}
        
    def parse_grammar(self, grammar_text):
        grammar = {}
        for line in grammar_text.strip().split('\n'):
            if '->' in line:
                lhs, rhs = line.split('->')
                lhs = lhs.strip()
                productions = [p.strip() for p in rhs.split('|')]
                if lhs not in grammar:
                    grammar[lhs] = []
                grammar[lhs].extend(productions)
        self.original_grammar = {k: v[:] for k, v in grammar.items()}
        return grammar
    
    def remove_left_recursion(self, grammar):
        """Remove direct and indirect left recursion"""
        new_grammar = {}
        non_terminals = list(grammar.keys())
        
        # Copy original grammar
        for nt in non_terminals:
            new_grammar[nt] = grammar[nt][:]
        
        # Remove direct left recursion for each non-terminal
        for nt in non_terminals:
            recursive = []
            non_recursive = []
            
            for prod in new_grammar[nt]:
                if prod.split()[0] == nt if prod.split() else False:
                    recursive.append(prod)
                else:
                    non_recursive.append(prod)
            
            if recursive:
                # Create new non-terminal
                new_nt = nt + "'"
                new_grammar[new_nt] = []
                
                # Update non-recursive productions
                new_grammar[nt] = []
                for prod in non_recursive:
                    if prod == 'ε':
                        new_grammar[nt].append(new_nt)
                    else:
                        new_grammar[nt].append(prod + ' ' + new_nt)
                
                # Create productions for new non-terminal
                for prod in recursive:
                    alpha = ' '.join(prod.split()[1:])  # Remove the left-recursive part
                    if alpha:
                        new_grammar[new_nt].append(alpha + ' ' + new_nt)
                    else:
                        new_grammar[new_nt].append(new_nt)
                new_grammar[new_nt].append('ε')
        
        self.after_left_recursion = {k: v[:] for k, v in new_grammar.items()}
        return new_grammar
    
    def left_factor(self, grammar):
        """Perform left factoring on the grammar"""
        new_grammar = {k: v[:] for k, v in grammar.items()}
        changed = True
        
        while changed:
            changed = False
            for nt in list(new_grammar.keys()):
                productions = new_grammar[nt]
                
                # Find common prefixes
                for i in range(len(productions)):
                    for j in range(i + 1, len(productions)):
                        prod1 = productions[i].split()
                        prod2 = productions[j].split()
                        
                        # Find common prefix
                        common = []
                        for k in range(min(len(prod1), len(prod2))):
                            if prod1[k] == prod2[k]:
                                common.append(prod1[k])
                            else:
                                break
                        
                        if common:
                            # Create new non-terminal
                            new_nt = nt + "'"
                            counter = 1
                            while new_nt in new_grammar:
                                new_nt = nt + "'" * (counter + 1)
                                counter += 1
                            
                            # Update productions
                            alpha = ' '.join(common)
                            beta1 = ' '.join(prod1[len(common):]) if len(prod1) > len(common) else 'ε'
                            beta2 = ' '.join(prod2[len(common):]) if len(prod2) > len(common) else 'ε'
                            
                            new_grammar[nt] = [p for idx, p in enumerate(productions) if idx not in [i, j]]
                            new_grammar[nt].append(alpha + ' ' + new_nt if alpha else new_nt)
                            new_grammar[new_nt] = [beta1, beta2]
                            
                            changed = True
                            break
                    if changed:
                        break
                if changed:
                    break
        
        self.after_left_factoring = {k: v[:] for k, v in new_grammar.items()}
        return new_grammar
        
    def parse_grammar(self, grammar_text):
        grammar = {}
        for line in grammar_text.strip().split('\n'):
            if '->' in line:
                lhs, rhs = line.split('->')
                lhs = lhs.strip()
                productions = [p.strip() for p in rhs.split('|')]
                if lhs not in grammar:
                    grammar[lhs] = []
                grammar[lhs].extend(productions)
        return grammar
    
    def compute_first(self, grammar):
        self.first = {nt: set() for nt in grammar}
        
        for terminal in self.get_terminals(grammar):
            self.first[terminal] = {terminal}
        
        changed = True
        while changed:
            changed = False
            for nt in grammar:
                for prod in grammar[nt]:
                    if prod == 'ε':
                        if 'ε' not in self.first[nt]:
                            self.first[nt].add('ε')
                            changed = True
                    else:
                        for symbol in prod.split():
                            if symbol in grammar:
                                before = len(self.first[nt])
                                self.first[nt] |= self.first[symbol] - {'ε'}
                                if len(self.first[nt]) > before:
                                    changed = True
                                if 'ε' not in self.first[symbol]:
                                    break
                            else:
                                if symbol not in self.first[nt]:
                                    self.first[nt].add(symbol)
                                    changed = True
                                break
                        else:
                            if 'ε' not in self.first[nt]:
                                self.first[nt].add('ε')
                                changed = True
        
        return self.first
    
    def compute_follow(self, grammar, start_symbol):
        self.follow = {nt: set() for nt in grammar}
        
        # Ensure start symbol exists in grammar
        if start_symbol not in self.follow:
            self.follow[start_symbol] = set()
        
        self.follow[start_symbol].add('$')
        
        changed = True
        while changed:
            changed = False
            for nt in grammar:
                for prod in grammar[nt]:
                    if prod == 'ε':
                        continue
                    symbols = prod.split()
                    for i, symbol in enumerate(symbols):
                        if symbol in grammar:
                            if i < len(symbols) - 1:
                                next_symbol = symbols[i + 1]
                                if next_symbol in grammar:
                                    before = len(self.follow[symbol])
                                    self.follow[symbol] |= self.first.get(next_symbol, set()) - {'ε'}
                                    if len(self.follow[symbol]) > before:
                                        changed = True
                                    if 'ε' in self.first.get(next_symbol, set()):
                                        before = len(self.follow[symbol])
                                        self.follow[symbol] |= self.follow[nt]
                                        if len(self.follow[symbol]) > before:
                                            changed = True
                                else:
                                    if next_symbol not in self.follow[symbol]:
                                        self.follow[symbol].add(next_symbol)
                                        changed = True
                            else:
                                before = len(self.follow[symbol])
                                self.follow[symbol] |= self.follow[nt]
                                if len(self.follow[symbol]) > before:
                                    changed = True
        
        return self.follow
    
    def get_terminals(self, grammar):
        terminals = set()
        for productions in grammar.values():
            for prod in productions:
                for symbol in prod.split():
                    if symbol not in grammar and symbol != 'ε':
                        terminals.add(symbol)
        return terminals
    
    def build_parsing_table(self, grammar, start_symbol):
        self.compute_first(grammar)
        self.compute_follow(grammar, start_symbol)
        
        terminals = self.get_terminals(grammar) | {'$'}
        self.parsing_table = {nt: {t: None for t in terminals} for nt in grammar}
        
        for nt in grammar:
            for prod in grammar[nt]:
                if prod == 'ε':
                    for terminal in self.follow[nt]:
                        self.parsing_table[nt][terminal] = prod
                else:
                    symbols = prod.split()
                    first_of_prod = set()
                    for symbol in symbols:
                        if symbol in grammar:
                            first_of_prod |= self.first[symbol] - {'ε'}
                            if 'ε' not in self.first[symbol]:
                                break
                        else:
                            first_of_prod.add(symbol)
                            break
                    else:
                        first_of_prod.add('ε')
                    
                    for terminal in first_of_prod:
                        if terminal != 'ε':
                            self.parsing_table[nt][terminal] = prod
                    
                    if 'ε' in first_of_prod:
                        for terminal in self.follow[nt]:
                            self.parsing_table[nt][terminal] = prod
        
        return self.parsing_table
    
    def _tokenize_input(self, input_string):
        known_terminals = set()
        for nt in self.parsing_table:
            for sym in self.parsing_table[nt]:
                if sym != '$':
                    known_terminals.add(sym)
        known_terminals_sorted = sorted(known_terminals, key=len, reverse=True)
        tokens = []
        i = 0
        while i < len(input_string):
            if input_string[i] == ' ':
                i += 1
                continue
            matched = False
            for term in known_terminals_sorted:
                end = i + len(term)
                if input_string[i:end] == term:
                    tokens.append(term)
                    i = end
                    matched = True
                    break
            if not matched:
                tokens.append(input_string[i])
                i += 1
        return tokens

    def parse_string(self, grammar, start_symbol, input_string):
        self.build_parsing_table(grammar, start_symbol)
        
        stack = ['$', start_symbol]
        input_tokens = self._tokenize_input(input_string) + ['$']
        index = 0
        steps = []
        
        while stack:
            top = stack[-1]
            current = input_tokens[index]
            
            step = {
                'Stack': ' '.join(stack),
                'Input': ' '.join(input_tokens[index:]),
                'Action': ''
            }
            
            if top == current == '$':
                step['Action'] = 'Accept'
                steps.append(step)
                break
            elif top == current:
                step['Action'] = f'Match {top}'
                steps.append(step)
                stack.pop()
                index += 1
            elif top in grammar:
                production = self.parsing_table[top].get(current)
                if production:
                    step['Action'] = f'{top} -> {production}'
                    steps.append(step)
                    stack.pop()
                    if production != 'ε':
                        for symbol in reversed(production.split()):
                            stack.append(symbol)
                else:
                    step['Action'] = f'Error: no rule for {top} on {current}'
                    steps.append(step)
                    break
            else:
                step['Action'] = f'Error: unexpected {top}'
                steps.append(step)
                break
        
        return steps
