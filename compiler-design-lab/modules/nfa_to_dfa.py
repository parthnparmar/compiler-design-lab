import graphviz

class NFAToDFA:
    def epsilon_closure(self, states, transitions):
        closure = set(states)
        stack = list(states)
        
        while stack:
            state = stack.pop()
            if state in transitions and 'ε' in transitions[state]:
                for next_state in transitions[state]['ε']:
                    if next_state not in closure:
                        closure.add(next_state)
                        stack.append(next_state)
        
        return frozenset(closure)
    
    def convert(self, nfa):
        transitions = nfa['transitions']
        start_state = nfa['start']
        final_state = nfa['end']
        
        symbols = set()
        for trans in transitions.values():
            symbols.update(trans.keys())
        symbols.discard('ε')
        symbols = sorted(symbols)
        
        start_closure = self.epsilon_closure([start_state], transitions)
        dfa_states = [start_closure]
        dfa_transitions = {}
        unmarked = [start_closure]
        state_map = {start_closure: 0}
        state_counter = 1
        
        epsilon_closures = {start_closure: start_closure}
        
        while unmarked:
            current = unmarked.pop(0)
            
            for symbol in symbols:
                next_states = set()
                for state in current:
                    if state in transitions and symbol in transitions[state]:
                        next_states.update(transitions[state][symbol])
                
                if next_states:
                    closure = self.epsilon_closure(next_states, transitions)
                    epsilon_closures[frozenset(next_states)] = closure
                    
                    if closure not in dfa_states:
                        dfa_states.append(closure)
                        state_map[closure] = state_counter
                        state_counter += 1
                        unmarked.append(closure)
                    
                    if current not in dfa_transitions:
                        dfa_transitions[current] = {}
                    dfa_transitions[current][symbol] = closure
        
        dfa_final_states = [s for s in dfa_states if final_state in s]
        
        return {
            'states': dfa_states,
            'transitions': dfa_transitions,
            'start': start_closure,
            'final': dfa_final_states,
            'state_map': state_map,
            'symbols': symbols,
            'epsilon_closures': epsilon_closures
        }
    
    def create_transition_table(self, dfa):
        table = []
        for state in dfa['states']:
            row = {
                'State': 'D' + str(dfa['state_map'][state]),
                'States': '{' + ', '.join([f'q{s}' for s in sorted(state)]) + '}'
            }
            for symbol in dfa['symbols']:
                next_state = dfa['transitions'].get(state, {}).get(symbol)
                row[symbol] = 'D' + str(dfa['state_map'][next_state]) if next_state else '-'
            table.append(row)
        return table
    
    def visualize_dfa(self, dfa):
        dot = graphviz.Digraph(comment='DFA')
        dot.attr(rankdir='LR')
        
        dot.node('start', shape='point')
        dot.edge('start', 'D' + str(dfa['state_map'][dfa['start']]))
        
        for state in dfa['states']:
            state_name = 'D' + str(dfa['state_map'][state])
            if state in dfa['final']:
                dot.node(state_name, shape='doublecircle')
            else:
                dot.node(state_name, shape='circle')
        
        for state, trans in dfa['transitions'].items():
            for symbol, next_state in trans.items():
                dot.edge('D' + str(dfa['state_map'][state]), 
                        'D' + str(dfa['state_map'][next_state]), 
                        label=symbol)
        
        return dot
