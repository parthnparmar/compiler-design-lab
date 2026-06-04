import graphviz

class DFAMinimization:
    def minimize(self, dfa):
        states = dfa['states']
        transitions = dfa['transitions']
        final_states = set(frozenset(s) for s in dfa['final'])
        state_map = dfa['state_map']
        symbols = dfa['symbols']
        
        non_final = [frozenset(s) for s in states if frozenset(s) not in final_states]
        final = list(final_states)
        
        partitions = []
        if non_final:
            partitions.append(non_final)
        if final:
            partitions.append(final)
        
        partition_history = [partitions[:]]
        
        changed = True
        while changed:
            changed = False
            new_partitions = []
            
            for partition in partitions:
                if len(partition) == 1:
                    new_partitions.append(partition)
                    continue
                
                groups = {}
                for state in partition:
                    signature = []
                    for symbol in symbols:
                        next_state = transitions.get(state, {}).get(symbol)
                        if next_state:
                            for i, p in enumerate(partitions):
                                if next_state in p:
                                    signature.append(i)
                                    break
                        else:
                            signature.append(-1)
                    
                    sig_tuple = tuple(signature)
                    if sig_tuple not in groups:
                        groups[sig_tuple] = []
                    groups[sig_tuple].append(state)
                
                if len(groups) > 1:
                    changed = True
                
                new_partitions.extend(groups.values())
            
            partitions = new_partitions
            partition_history.append(partitions[:])
        
        new_state_map = {}
        for i, partition in enumerate(partitions):
            for state in partition:
                new_state_map[state] = i
        
        new_transitions = {}
        for partition in partitions:
            rep = partition[0]
            state_id = new_state_map[rep]
            new_transitions[state_id] = {}
            for symbol in symbols:
                next_state = transitions.get(rep, {}).get(symbol)
                if next_state:
                    new_transitions[state_id][symbol] = new_state_map[next_state]
        
        start_state = new_state_map[frozenset(dfa['start'])]
        final_states = list(set(new_state_map[frozenset(s)] for s in dfa['final']))
        
        return {
            'states': list(range(len(partitions))),
            'transitions': new_transitions,
            'start': start_state,
            'final': final_states,
            'symbols': symbols,
            'partitions': partitions,
            'partition_history': partition_history,
            'state_map': new_state_map
        }
    
    def visualize_minimized_dfa(self, min_dfa):
        dot = graphviz.Digraph(comment='Minimized DFA')
        dot.attr(rankdir='LR')
        
        dot.node('start', shape='point')
        dot.edge('start', f'S{min_dfa["start"]}')
        
        for state in min_dfa['states']:
            state_name = f'S{state}'
            if state in min_dfa['final']:
                dot.node(state_name, shape='doublecircle')
            else:
                dot.node(state_name, shape='circle')
        
        for state, trans in min_dfa['transitions'].items():
            for symbol, next_state in trans.items():
                dot.edge(f'S{state}', f'S{next_state}', label=symbol)
        
        return dot
