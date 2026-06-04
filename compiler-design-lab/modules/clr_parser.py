from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any

from .first_follow import _parse_grammar, compute_first_follow_with_steps

# LR(1) item: (head, body_tuple, dot, lookahead)
Item1 = Tuple[str, Tuple[str, ...], int, str]


def _first_of_sequence(seq: List[str], lookahead: str, first: Dict[str, set], non_terminals: set) -> Set[str]:
    """Compute FIRST(seq + lookahead) for use in LR(1) closure."""
    result = set()
    for sym in seq:
        if sym not in non_terminals:
            result.add(sym)
            return result
        result |= first.get(sym, set()) - {'ε'}
        if 'ε' not in first.get(sym, set()):
            return result
    result.add(lookahead)
    return result


def clr_closure(items: Set[Item1], productions: Dict, first: Dict, non_terminals: set) -> frozenset:
    closure_set = set(items)
    changed = True
    while changed:
        changed = False
        for head, body, dot, lookahead in list(closure_set):
            if dot < len(body):
                B = body[dot]
                if B in non_terminals:
                    beta = list(body[dot + 1:])
                    for la in _first_of_sequence(beta, lookahead, first, non_terminals):
                        for prod_body in productions[B]:
                            new_item = (B, tuple(prod_body), 0, la)
                            if new_item not in closure_set:
                                closure_set.add(new_item)
                                changed = True
    return frozenset(closure_set)


def clr_goto(items: frozenset, symbol: str, productions: Dict, first: Dict, non_terminals: set) -> frozenset:
    moved = set()
    for head, body, dot, la in items:
        if dot < len(body) and body[dot] == symbol:
            moved.add((head, body, dot + 1, la))
    return clr_closure(moved, productions, first, non_terminals) if moved else frozenset()


def build_clr_canonical_collection(
    start_symbol: str, productions: Dict, first: Dict, non_terminals: set
) -> Tuple[List[frozenset], Dict[Tuple[int, str], int], str]:
    aug_start = start_symbol + "'"
    while aug_start in productions:
        aug_start += "'"
    productions[aug_start] = [[start_symbol]]

    start_item = (aug_start, tuple(productions[aug_start][0]), 0, '$')
    I0 = clr_closure({start_item}, productions, first, non_terminals)
    C: List[frozenset] = [I0]
    transitions: Dict[Tuple[int, str], int] = {}

    i = 0
    while i < len(C):
        I = C[i]
        symbols = {body[dot] for head, body, dot, la in I if dot < len(body)}
        for X in symbols:
            g = clr_goto(I, X, productions, first, non_terminals)
            if g:
                if g not in C:
                    C.append(g)
                j = C.index(g)
                transitions[(i, X)] = j
        i += 1
    return C, transitions, aug_start


def build_clr_table(
    C: List[frozenset],
    transitions: Dict[Tuple[int, str], int],
    productions: Dict,
    aug_start: str,
    non_terminals: set,
) -> Tuple[Dict, Dict, List]:
    # Build ordered production list (excluding augmented)
    prod_list: List[Tuple[str, Tuple[str, ...]]] = []
    for head, bodies in productions.items():
        if head == aug_start:
            continue
        for body in bodies:
            prod_list.append((head, tuple(body)))

    terminals_set = set()
    for head, bodies in productions.items():
        for body in bodies:
            for sym in body:
                if sym not in non_terminals and sym != 'ε':
                    terminals_set.add(sym)

    action: Dict[Tuple[int, str], str] = {}
    goto_table: Dict[Tuple[int, str], int] = {}
    conflicts: List[str] = []

    for (i, X), j in transitions.items():
        if X in non_terminals:
            goto_table[(i, X)] = j
        else:
            key = (i, X)
            new_val = f's{j}'
            if key in action and action[key] != new_val:
                conflicts.append(f'Conflict at state {i}, symbol {X}: {action[key]} vs {new_val}')
            action[key] = new_val

    for i, I in enumerate(C):
        for head, body, dot, la in I:
            if dot == len(body):
                if head == aug_start:
                    key = (i, '$')
                    if key in action and action[key] != 'acc':
                        conflicts.append(f'Conflict at state {i}, $: {action[key]} vs acc')
                    action[key] = 'acc'
                else:
                    prod_index = prod_list.index((head, tuple(body)))
                    key = (i, la)
                    new_val = f'r{prod_index}'
                    if key in action and action[key] != new_val:
                        conflicts.append(f'Conflict at state {i}, symbol {la}: {action[key]} vs {new_val}')
                    action[key] = new_val

    return action, goto_table, prod_list, conflicts


def _tokenize(input_string: str, action: Dict) -> List[str]:
    """Flexible tokenizer: splits on whitespace first, then tries greedy match per chunk.
    Works for inputs like 'ccd', 'c c d', 'id+id', 'id + id * id' etc.
    """
    known = sorted({sym for (_, sym) in action if sym != '$'}, key=len, reverse=True)

    def match_chunk(chunk: str) -> List[str]:
        """Greedily match known terminals inside a whitespace-free chunk."""
        result, i = [], 0
        while i < len(chunk):
            matched = False
            for term in known:
                if chunk[i:i + len(term)] == term:
                    result.append(term)
                    i += len(term)
                    matched = True
                    break
            if not matched:
                result.append(chunk[i])  # unknown char — pass through as-is
                i += 1
        return result

    tokens = []
    # Split on any whitespace; each space-separated piece is matched greedily
    for chunk in input_string.split():
        tokens.extend(match_chunk(chunk))
    return tokens


def simulate_clr_parse(tokens: List[str], action: Dict, goto_table: Dict, prod_list: List) -> List[Dict]:
    stack = [0]
    inp = tokens + ['$']
    ip = 0
    trace = []

    while True:
        state = stack[-1]
        a = inp[ip]
        act = action.get((state, a))
        stack_str = ' '.join(str(s) for s in stack)
        input_str = ' '.join(inp[ip:])

        if act is None:
            trace.append({'Step': len(trace) + 1, 'Stack': stack_str, 'Input': input_str,
                          'Action': f'Error: no action for state {state}, symbol "{a}"'})
            break
        if act.startswith('s'):
            ns = int(act[1:])
            trace.append({'Step': len(trace) + 1, 'Stack': stack_str, 'Input': input_str,
                          'Action': f'Shift {ns}'})
            stack.extend([a, ns])
            ip += 1
        elif act.startswith('r'):
            idx = int(act[1:])
            head, body = prod_list[idx]
            body_len = 0 if body == ('ε',) else len(body)
            for _ in range(2 * body_len):
                stack.pop()
            gs = goto_table.get((stack[-1], head))
            if gs is None:
                trace.append({'Step': len(trace) + 1, 'Stack': stack_str, 'Input': input_str,
                              'Action': f'Error: no goto for ({stack[-1]}, {head})'})
                break
            trace.append({'Step': len(trace) + 1, 'Stack': stack_str, 'Input': input_str,
                          'Action': f'Reduce r{idx}: {head} → {" ".join(body)}'})
            stack.extend([head, gs])
        elif act == 'acc':
            trace.append({'Step': len(trace) + 1, 'Stack': stack_str, 'Input': input_str,
                          'Action': 'Accept ✓'})
            break
    return trace


def lalr_parse_with_steps(grammar_text: str, input_string: str) -> Dict[str, Any]:
    """LALR(1): build CLR(1) collection, merge states with identical LR(0) cores."""
    start_symbol, productions = _parse_grammar(grammar_text)
    non_terminals = set(productions.keys())

    ff = compute_first_follow_with_steps(grammar_text)
    first = {k: set(v) for k, v in ff['first_sets'].items()}

    C, transitions, aug_start = build_clr_canonical_collection(
        start_symbol, productions, first, non_terminals
    )
    non_terminals_aug = set(productions.keys())

    # --- LALR merge: group CLR states by LR(0) core (items without lookahead) ---
    def core(state: frozenset) -> frozenset:
        return frozenset((h, b, d) for h, b, d, _ in state)

    # Map each CLR state index -> merge group index
    core_to_group: Dict[frozenset, int] = {}
    group_id: List[int] = []          # group_id[i] = LALR state for CLR state i
    groups: List[List[int]] = []      # groups[g] = list of CLR state indices

    for i, I in enumerate(C):
        c = core(I)
        if c not in core_to_group:
            core_to_group[c] = len(groups)
            groups.append([])
        g = core_to_group[c]
        group_id.append(g)
        groups[g].append(i)

    num_lalr = len(groups)

    # Build merged LALR states: union lookaheads for items with same core
    lalr_states: List[frozenset] = []
    for g, clr_indices in enumerate(groups):
        merged: Dict[Tuple, set] = {}
        for ci in clr_indices:
            for h, b, d, la in C[ci]:
                key = (h, b, d)
                merged.setdefault(key, set()).add(la)
        lalr_states.append(frozenset(
            (h, b, d, la) for (h, b, d), las in merged.items() for la in las
        ))

    # Remap transitions to LALR state indices
    lalr_transitions: Dict[Tuple[int, str], int] = {}
    for (i, X), j in transitions.items():
        lalr_transitions[(group_id[i], X)] = group_id[j]

    # Build LALR table
    action, goto_table, prod_list, conflicts = build_clr_table(
        lalr_states, lalr_transitions, productions, aug_start, non_terminals_aug
    )

    # Readable item sets
    states_readable = []
    for idx, I in enumerate(lalr_states):
        items_strings = []
        orig_indices = groups[idx]
        label = 'I' + ','.join(str(x) for x in orig_indices) if len(orig_indices) > 1 else f'I{orig_indices[0]}'
        for head, body, dot, la in sorted(I):
            b = list(body)
            b.insert(dot, '•')
            items_strings.append(f'{head} → {" ".join(b)},  [{la}]')
        states_readable.append({
            'index': idx,
            'label': label,
            'item_list': sorted(items_strings)
        })

    all_terminals = sorted({sym for (_, sym) in action if sym != '$'} | {'$'})
    all_non_terms = sorted({A for (_, A) in goto_table})

    def fmt(v):
        if not v: return ''
        if v == 'acc': return 'acc'
        if v.startswith('s'): return 'S' + v[1:]
        return v

    table_rows = []
    for i in range(num_lalr):
        row = {'State': i}
        for a in all_terminals:
            row[a] = fmt(action.get((i, a), ''))
        for A in all_non_terms:
            row[A] = str(goto_table[(i, A)]) if (i, A) in goto_table else ''
        table_rows.append(row)

    aug_grammar_list = [{'Rule': 'r0', 'Production': f"{aug_start} → {productions[aug_start][0][0]}"}]
    for idx, (head, body) in enumerate(prod_list):
        aug_grammar_list.append({'Rule': f'r{idx}', 'Production': f'{head} → {" ".join(body)}'})

    parse_trace = []
    accepted = None
    if input_string.strip():
        tokens = _tokenize(input_string.strip(), action)
        parse_trace = simulate_clr_parse(tokens, action, goto_table, prod_list)
        last = parse_trace[-1]['Action'] if parse_trace else ''
        accepted = last.startswith('Accept')

    # Merge info for display
    merged_info = [
        {'LALR State': idx,
         'Merged from CLR States': ', '.join(f'I{x}' for x in groups[idx])}
        for idx in range(num_lalr) if len(groups[idx]) > 1
    ]

    return {
        'start_symbol': start_symbol,
        'aug_start': aug_start,
        'aug_grammar_list': aug_grammar_list,
        'prod_list': prod_list,
        'states': states_readable,
        'action_terminals': all_terminals,
        'goto_non_terminals': all_non_terms,
        'table_rows': table_rows,
        'conflicts': conflicts,
        'parse_trace': parse_trace,
        'accepted': accepted,
        'input_string': input_string.strip(),
        'merged_info': merged_info,
        'clr_state_count': len(C),
        'lalr_state_count': num_lalr,
    }


def clr_parse_with_steps(grammar_text: str, input_string: str) -> Dict[str, Any]:
    start_symbol, productions = _parse_grammar(grammar_text)
    non_terminals = set(productions.keys())

    # Compute FIRST sets for LR(1) closure
    ff = compute_first_follow_with_steps(grammar_text)
    first = {k: set(v) for k, v in ff['first_sets'].items()}
    follow_sets = ff['follow_sets']

    C, transitions, aug_start = build_clr_canonical_collection(
        start_symbol, productions, first, non_terminals
    )
    # Recompute non_terminals after augmentation adds aug_start
    non_terminals_aug = set(productions.keys())

    action, goto_table, prod_list, conflicts = build_clr_table(
        C, transitions, productions, aug_start, non_terminals_aug
    )

    # Readable item sets
    states_readable = []
    for idx, I in enumerate(C):
        items_strings = []
        for head, body, dot, la in sorted(I):
            b = list(body)
            b.insert(dot, '•')
            items_strings.append(f'{head} → {" ".join(b)},  [{la}]')
        states_readable.append({'index': idx, 'item_list': sorted(items_strings)})

    # Table rows
    all_terminals = sorted({sym for (_, sym) in action if sym != '$'} | {'$'})
    all_non_terms = sorted({A for (_, A) in goto_table})

    def fmt(v):
        if not v:
            return ''
        if v == 'acc':
            return 'acc'
        if v.startswith('s'):
            return 'S' + v[1:]
        return v

    table_rows = []
    for i in range(len(C)):
        row = {'State': i}
        for a in all_terminals:
            row[a] = fmt(action.get((i, a), ''))
        for A in all_non_terms:
            row[A] = str(goto_table[(i, A)]) if (i, A) in goto_table else ''
        table_rows.append(row)

    # Augmented grammar list
    aug_grammar_list = [{'Rule': 'r0', 'Production': f"{aug_start} → {productions[aug_start][0][0]}"}]
    for idx, (head, body) in enumerate(prod_list):
        aug_grammar_list.append({'Rule': f'r{idx}', 'Production': f'{head} → {" ".join(body)}'})

    parse_trace = []
    accepted = None
    if input_string.strip():
        tokens = _tokenize(input_string.strip(), action)
        parse_trace = simulate_clr_parse(tokens, action, goto_table, prod_list)
        last = parse_trace[-1]['Action'] if parse_trace else ''
        accepted = last.startswith('Accept')

    return {
        'start_symbol': start_symbol,
        'aug_start': aug_start,
        'aug_grammar_list': aug_grammar_list,
        'prod_list': prod_list,
        'states': states_readable,
        'follow_sets': follow_sets,
        'action_terminals': all_terminals,
        'goto_non_terminals': all_non_terms,
        'table_rows': table_rows,
        'conflicts': conflicts,
        'parse_trace': parse_trace,
        'accepted': accepted,
        'input_string': input_string.strip(),
    }
