import graphviz

class RegexToNFA:
    def __init__(self):
        self.state_count = 0
        
    def new_state(self):
        self.state_count += 1
        return self.state_count
    
    def to_postfix(self, regex):
        precedence = {'*': 3, '.': 2, '|': 1}
        output = []
        stack = []
        
        regex = self.add_concat(regex)
        
        for char in regex:
            if char.isalnum():
                output.append(char)
            elif char == '(':
                stack.append(char)
            elif char == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                stack.pop()
            else:
                while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence.get(char, 0):
                    output.append(stack.pop())
                stack.append(char)
        
        while stack:
            output.append(stack.pop())
        
        return ''.join(output)
    
    def add_concat(self, regex):
        result = []
        for i in range(len(regex)):
            result.append(regex[i])
            if i < len(regex) - 1:
                c1, c2 = regex[i], regex[i + 1]
                if (c1.isalnum() or c1 in ')*') and (c2.isalnum() or c2 == '('):
                    result.append('.')
        return ''.join(result)
    
    def construct_nfa(self, regex):
        self.state_count = 0
        postfix = self.to_postfix(regex)
        stack = []
        
        for char in postfix:
            if char.isalnum():
                start = self.new_state()
                end = self.new_state()
                nfa = {
                    'start': start,
                    'end': end,
                    'transitions': {start: {char: [end]}}
                }
                stack.append(nfa)
            elif char == '|':
                nfa2 = stack.pop()
                nfa1 = stack.pop()
                start = self.new_state()
                end = self.new_state()
                transitions = {**nfa1['transitions'], **nfa2['transitions']}
                transitions[start] = {'ε': [nfa1['start'], nfa2['start']]}
                transitions[nfa1['end']] = {'ε': [end]}
                transitions[nfa2['end']] = {'ε': [end]}
                stack.append({'start': start, 'end': end, 'transitions': transitions})
            elif char == '.':
                nfa2 = stack.pop()
                nfa1 = stack.pop()
                transitions = {**nfa1['transitions'], **nfa2['transitions']}
                if nfa1['end'] not in transitions:
                    transitions[nfa1['end']] = {}
                transitions[nfa1['end']]['ε'] = [nfa2['start']]
                stack.append({'start': nfa1['start'], 'end': nfa2['end'], 'transitions': transitions})
            elif char == '*':
                nfa = stack.pop()
                start = self.new_state()
                end = self.new_state()
                transitions = {**nfa['transitions']}
                transitions[start] = {'ε': [nfa['start'], end]}
                transitions[nfa['end']] = {'ε': [nfa['start'], end]}
                stack.append({'start': start, 'end': end, 'transitions': transitions})
        
        return stack[0], postfix
    
    def create_transition_table(self, nfa):
        states = set()
        symbols = set()
        
        for state, trans in nfa['transitions'].items():
            states.add(state)
            for symbol, next_states in trans.items():
                symbols.add(symbol)
                states.update(next_states)
        
        states.add(nfa['start'])
        states.add(nfa['end'])
        states = sorted(states)
        symbols = sorted(symbols, key=lambda x: (x != 'ε', x))
        
        table = []
        for state in states:
            row = {'State': f'q{state}'}
            for symbol in symbols:
                next_states = nfa['transitions'].get(state, {}).get(symbol, [])
                row[symbol] = ', '.join([f'q{s}' for s in next_states]) if next_states else '-'
            table.append(row)
        
        return table
    
    def visualize_nfa(self, nfa):
        dot = graphviz.Digraph(comment='NFA')
        dot.attr(rankdir='LR')
        
        dot.node('start', shape='point')
        dot.edge('start', f'q{nfa["start"]}')
        
        for state in nfa['transitions']:
            if state == nfa['end']:
                dot.node(f'q{state}', shape='doublecircle')
            else:
                dot.node(f'q{state}', shape='circle')
        
        dot.node(f'q{nfa["end"]}', shape='doublecircle')
        
        for state, trans in nfa['transitions'].items():
            for symbol, next_states in trans.items():
                for next_state in next_states:
                    dot.edge(f'q{state}', f'q{next_state}', label=symbol)
        
        return dot
