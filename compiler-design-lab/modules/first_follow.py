from typing import Dict, List, Tuple


def _parse_grammar(grammar_text: str) -> Tuple[str, Dict[str, List[List[str]]]]:
    productions: Dict[str, List[List[str]]] = {}
    start_symbol = None
    for line in grammar_text.strip().splitlines():
        line = line.strip()
        if not line or '->' not in line:
            continue
        lhs, rhs = line.split('->', 1)
        lhs = lhs.strip()
        if start_symbol is None:
            start_symbol = lhs
        if lhs not in productions:
            productions[lhs] = []
        for alt in rhs.split('|'):
            productions[lhs].append(alt.strip().split())
    return start_symbol, productions


def compute_first_follow_with_steps(grammar_text: str) -> Dict:
    start_symbol, productions = _parse_grammar(grammar_text)
    non_terminals = set(productions.keys())

    # FIRST sets
    first: Dict[str, set] = {nt: set() for nt in non_terminals}
    changed = True
    while changed:
        changed = False
        for nt, bodies in productions.items():
            for body in bodies:
                for sym in body:
                    if sym == 'ε':
                        if 'ε' not in first[nt]:
                            first[nt].add('ε')
                            changed = True
                        break
                    elif sym not in non_terminals:
                        if sym not in first[nt]:
                            first[nt].add(sym)
                            changed = True
                        break
                    else:
                        before = len(first[nt])
                        first[nt] |= first[sym] - {'ε'}
                        if len(first[nt]) > before:
                            changed = True
                        if 'ε' not in first[sym]:
                            break
                else:
                    if 'ε' not in first[nt]:
                        first[nt].add('ε')
                        changed = True

    # FOLLOW sets
    follow: Dict[str, set] = {nt: set() for nt in non_terminals}
    follow[start_symbol].add('$')
    changed = True
    while changed:
        changed = False
        for nt, bodies in productions.items():
            for body in bodies:
                for i, sym in enumerate(body):
                    if sym not in non_terminals:
                        continue
                    trailer = set()
                    all_derive_eps = True
                    for next_sym in body[i + 1:]:
                        if next_sym not in non_terminals:
                            trailer.add(next_sym)
                            all_derive_eps = False
                            break
                        trailer |= first[next_sym] - {'ε'}
                        if 'ε' not in first[next_sym]:
                            all_derive_eps = False
                            break
                    if all_derive_eps:
                        trailer |= follow[nt]
                    before = len(follow[sym])
                    follow[sym] |= trailer
                    if len(follow[sym]) > before:
                        changed = True

    return {
        "start_symbol": start_symbol,
        "productions": productions,
        "first_sets": {k: sorted(v) for k, v in first.items()},
        "follow_sets": {k: sorted(v) for k, v in follow.items()},
    }
