import graphviz

class DirectDFA:
    def __init__(self):
        self.pos_count = 0
        
    def parse_regex(self, regex):
        self.pos_count = 0
        augmented = self.add_concat(regex) + '.#'
        tree = self.build_tree(augmented)
        return tree
    
    def add_concat(self, regex):
        result = []
        for i in range(len(regex)):
            result.append(regex[i])
            if i < len(regex) - 1:
                c1, c2 = regex[i], regex[i + 1]
                if (c1.isalnum() or c1 in ')*') and (c2.isalnum() or c2 == '('):
                    result.append('.')
        return ''.join(result)
    
    def build_tree(self, regex):
        postfix = self.to_postfix(regex)
        stack = []
        
        for char in postfix:
            if char.isalnum() or char == '#':
                self.pos_count += 1
                node = {
                    'type': 'leaf',
                    'symbol': char,
                    'pos': self.pos_count,
                    'nullable': False,
                    'firstpos': {self.pos_count},
                    'lastpos': {self.pos_count}
                }
                stack.append(node)
            elif char == '|':
                if len(stack) < 2:
                    continue
                right = stack.pop()
                left = stack.pop()
                node = {
                    'type': 'or',
                    'left': left,
                    'right': right,
                    'nullable': left['nullable'] or right['nullable'],
                    'firstpos': left['firstpos'] | right['firstpos'],
                    'lastpos': left['lastpos'] | right['lastpos']
                }
                stack.append(node)
            elif char == '.':
                if len(stack) < 2:
                    continue
                right = stack.pop()
                left = stack.pop()
                firstpos = left['firstpos'] | right['firstpos'] if left['nullable'] else left['firstpos']
                lastpos = right['lastpos'] | left['lastpos'] if right['nullable'] else right['lastpos']
                node = {
                    'type': 'concat',
                    'left': left,
                    'right': right,
                    'nullable': left['nullable'] and right['nullable'],
                    'firstpos': firstpos,
                    'lastpos': lastpos
                }
                stack.append(node)
            elif char == '*':
                if len(stack) < 1:
                    continue
                child = stack.pop()
                node = {
                    'type': 'star',
                    'child': child,
                    'nullable': True,
                    'firstpos': child['firstpos'],
                    'lastpos': child['lastpos']
                }
                stack.append(node)
        
        return stack[0] if stack else None
    
    def to_postfix(self, regex):
        precedence = {'*': 3, '.': 2, '|': 1}
        output = []
        stack = []
        
        for char in regex:
            if char.isalnum():
                output.append(char)
            elif char == '(':
                stack.append(char)
            elif char == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if stack:
                    stack.pop()
            elif char in precedence:
                while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence.get(char, 0):
                    output.append(stack.pop())
                stack.append(char)
        
        while stack:
            output.append(stack.pop())
        
        return ''.join(output)
    
    def compute_followpos(self, tree):
        followpos = {i: set() for i in range(1, self.pos_count + 1)}
        self._compute_followpos_helper(tree, followpos)
        return followpos
    
    def _compute_followpos_helper(self, node, followpos):
        if node['type'] == 'concat':
            for i in node['left']['lastpos']:
                followpos[i] |= node['right']['firstpos']
            self._compute_followpos_helper(node['left'], followpos)
            self._compute_followpos_helper(node['right'], followpos)
        elif node['type'] == 'star':
            for i in node['lastpos']:
                followpos[i] |= node['firstpos']
            self._compute_followpos_helper(node['child'], followpos)
        elif node['type'] == 'or':
            self._compute_followpos_helper(node['left'], followpos)
            self._compute_followpos_helper(node['right'], followpos)
    
    def get_position_symbols(self, tree):
        symbols = {}
        self._get_symbols_helper(tree, symbols)
        return symbols
    
    def _get_symbols_helper(self, node, symbols):
        if node['type'] == 'leaf':
            symbols[node['pos']] = node['symbol']
        elif node['type'] in ['concat', 'or']:
            self._get_symbols_helper(node['left'], symbols)
            self._get_symbols_helper(node['right'], symbols)
        elif node['type'] == 'star':
            self._get_symbols_helper(node['child'], symbols)
    
    def construct_dfa(self, regex):
        tree = self.parse_regex(regex)
        if not tree:
            return {
                'tree': None,
                'followpos': {},
                'pos_symbols': {},
                'states': [],
                'transitions': {},
                'start': set(),
                'final': [],
                'state_map': {},
                'symbols': []
            }
        
        followpos = self.compute_followpos(tree)
        pos_symbols = self.get_position_symbols(tree)
        
        symbols = set(pos_symbols.values())
        symbols.discard('#')
        symbols = sorted(symbols)
        
        if not symbols:
            return {
                'tree': tree,
                'followpos': followpos,
                'pos_symbols': pos_symbols,
                'states': [],
                'transitions': {},
                'start': set(),
                'final': [],
                'state_map': {},
                'symbols': []
            }
        
        dfa_states = [tree['firstpos']]
        dfa_transitions = {}
        unmarked = [tree['firstpos']]
        state_map = {frozenset(tree['firstpos']): 0}
        state_counter = 1
        
        final_pos_list = [pos for pos, sym in pos_symbols.items() if sym == '#']
        final_pos = final_pos_list[0] if final_pos_list else None
        
        while unmarked:
            current = unmarked.pop(0)
            
            for symbol in symbols:
                next_state = set()
                for pos in current:
                    if pos in pos_symbols and pos_symbols[pos] == symbol:
                        next_state |= followpos.get(pos, set())
                
                if next_state:
                    frozen = frozenset(next_state)
                    if frozen not in state_map:
                        dfa_states.append(next_state)
                        state_map[frozen] = state_counter
                        state_counter += 1
                        unmarked.append(next_state)
                    
                    if frozenset(current) not in dfa_transitions:
                        dfa_transitions[frozenset(current)] = {}
                    dfa_transitions[frozenset(current)][symbol] = frozen
        
        final_states = [s for s in dfa_states if final_pos and final_pos in s]
        
        return {
            'tree': tree,
            'followpos': followpos,
            'pos_symbols': pos_symbols,
            'states': dfa_states,
            'transitions': dfa_transitions,
            'start': tree['firstpos'],
            'final': final_states,
            'state_map': state_map,
            'symbols': symbols
        }
    
    def visualize_dfa(self, result):
        graph = graphviz.Digraph(comment='Direct DFA')
        graph.attr(rankdir='LR')
        graph.attr('node', shape='circle')

        state_map = result['state_map']
        final_states = result['final']
        transitions = result['transitions']
        symbols = result['symbols']
        start = result['start']

        final_set = {frozenset(s) for s in final_states}

        # invisible start arrow
        graph.node('__start__', shape='none', label='')
        graph.edge('__start__', f"S{state_map[frozenset(start)]}")

        for state in result['states']:
            fs = frozenset(state)
            sid = f"S{state_map[fs]}"
            label = sid + '\n{' + ','.join(map(str, sorted(state))) + '}'
            shape = 'doublecircle' if fs in final_set else 'circle'
            graph.node(sid, label=label, shape=shape)

        for from_state, trans in transitions.items():
            for symbol, to_state in trans.items():
                src = f"S{state_map[from_state]}"
                dst = f"S{state_map[to_state]}"
                graph.edge(src, dst, label=symbol)

        return graph

    def visualize_tree(self, tree, graph=None, parent=None, edge_label=''):
        if graph is None:
            graph = graphviz.Digraph(comment='Syntax Tree')
            graph.attr(rankdir='TB')
        
        node_id = str(id(tree))
        
        if tree['type'] == 'leaf':
            label = f"{tree['symbol']}\npos: {tree['pos']}"
            graph.node(node_id, label, shape='box')
        else:
            label = tree['type']
            graph.node(node_id, label, shape='ellipse')
        
        if parent:
            graph.edge(parent, node_id, label=edge_label)
        
        if tree['type'] in ['concat', 'or']:
            self.visualize_tree(tree['left'], graph, node_id, 'L')
            self.visualize_tree(tree['right'], graph, node_id, 'R')
        elif tree['type'] == 'star':
            self.visualize_tree(tree['child'], graph, node_id)
        
        return graph
