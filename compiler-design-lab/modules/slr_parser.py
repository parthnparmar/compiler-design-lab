from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any

from .first_follow import _parse_grammar, compute_first_follow_with_steps


Item = Tuple[str, Tuple[str, ...], int]  # (head, body, dot_position)


def closure(items: Set[Item], productions: Dict[str, List[List[str]]], steps: List[str]) -> Set[Item]:
    changed = True
    closure_set = set(items)
    while changed:
        changed = False
        for head, body, dot in list(closure_set):
            if dot < len(body):
                B = body[dot]
                if B in productions:
                    for prod_body in productions[B]:
                        item = (B, tuple(prod_body), 0)
                        if item not in closure_set:
                            steps.append(f"Adding item {B} -> •{' '.join(prod_body)} to closure.")
                            closure_set.add(item)
                            changed = True
    return closure_set


def goto(items: Set[Item], symbol: str, productions: Dict[str, List[List[str]]], steps: List[str]) -> Set[Item]:
    moved = set()
    for head, body, dot in items:
        if dot < len(body) and body[dot] == symbol:
            moved.add((head, tuple(body), dot + 1))
    if moved:
        steps.append(f"Computing GOTO on symbol {symbol}.")
    return closure(moved, productions, steps) if moved else set()


def items_canonical_collection(
    start_symbol: str, productions: Dict[str, List[List[str]]], steps: List[str]
) -> Tuple[List[Set[Item]], Dict[Tuple[int, str], int], str]:
    augmented_start = start_symbol + "'"
    while augmented_start in productions:
        augmented_start += "'"
    productions[augmented_start] = [[start_symbol]]

    start_item = (augmented_start, tuple(productions[augmented_start][0]), 0)
    C: List[Set[Item]] = []
    transitions: Dict[Tuple[int, str], int] = {}

    I0 = closure({start_item}, productions, steps)
    C.append(I0)
    steps.append("Initial item set I0 constructed.")

    changed = True
    while changed:
        changed = False
        for i, I in list(enumerate(C)):
            symbols = set()
            for head, body, dot in I:
                if dot < len(body):
                    symbols.add(body[dot])
            for X in symbols:
                goto_I_X = goto(I, X, productions, steps)
                if not goto_I_X:
                    continue
                if goto_I_X not in C:
                    C.append(goto_I_X)
                    j = len(C) - 1
                    transitions[(i, X)] = j
                    steps.append(f"New state I{j} reached by GOTO(I{i}, {X}).")
                    changed = True
                else:
                    j = C.index(goto_I_X)
                    transitions[(i, X)] = j
    return C, transitions, augmented_start


def build_slr_parsing_table(
    C: List[Set[Item]],
    transitions: Dict[Tuple[int, str], int],
    productions: Dict[str, List[List[str]]],
    augmented_start: str,
    follow_sets: Dict[str, List[str]],
    steps: List[str],
) -> Tuple[Dict[Tuple[int, str], str], Dict[Tuple[int, str], int]]:
    action: Dict[Tuple[int, str], str] = {}
    goto_table: Dict[Tuple[int, str], int] = {}

    non_terminals = set(productions.keys())
    non_terminals.discard(augmented_start)
    terminals = set()
    for head, bodies in productions.items():
        for body in bodies:
            for sym in body:
                if sym not in non_terminals and sym != "ε":
                    terminals.add(sym)

    for (i, X), j in transitions.items():
        if X in terminals:
            action[(i, X)] = f"s{j}"
            steps.append(f"action[{i}, {X}] = shift {j}")
        else:
            goto_table[(i, X)] = j
            steps.append(f"goto[{i}, {X}] = {j}")

    prod_list: List[Tuple[str, Tuple[str, ...]]] = []
    for head, bodies in productions.items():
        if head == augmented_start:
            continue
        for body in bodies:
            prod_list.append((head, tuple(body)))

    for i, I in enumerate(C):
        for head, body, dot in I:
            if dot == len(body):
                if head == augmented_start:
                    action[(i, "$")] = "acc"
                    steps.append(f"action[{i}, $] = accept (augmented start).")
                else:
                    prod_index = prod_list.index((head, tuple(body)))
                    for a in follow_sets[head]:
                        if (i, a) not in action:
                            action[(i, a)] = f"r{prod_index}"
                            steps.append(
                                f"action[{i}, {a}] = reduce using {head} -> {' '.join(body)}"
                            )
    return action, goto_table, prod_list


def simulate_slr_parse(
    input_tokens: List[str],
    action: Dict[Tuple[int, str], str],
    goto_table: Dict[Tuple[int, str], int],
    prod_list: List[Tuple[str, Tuple[str, ...]]],
) -> List[Dict[str, Any]]:
    stack: List = [0]
    tokens = input_tokens + ["$"]
    ip = 0
    trace: List[Dict[str, Any]] = []

    while True:
        state = stack[-1]
        a = tokens[ip]
        act = action.get((state, a))
        stack_content = " ".join(str(s) for s in stack)
        input_content = " ".join(tokens[ip:])
        if act is None:
            trace.append({
                "Stack": stack_content,
                "Input": input_content,
                "Action": f"Error: no action for state {state}, symbol '{a}'",
            })
            break
        if act.startswith("s"):
            next_state = int(act[1:])
            trace.append({
                "Stack": stack_content,
                "Input": input_content,
                "Action": f"Shift {next_state}",
            })
            stack.extend([a, next_state])
            ip += 1
        elif act.startswith("r"):
            prod_index = int(act[1:])
            head, body = prod_list[prod_index]
            body_len = 0 if body == ("ε",) else len(body)
            for _ in range(2 * body_len):
                stack.pop()
            state = stack[-1]
            goto_state = goto_table.get((state, head))
            if goto_state is None:
                trace.append({
                    "Stack": " ".join(str(s) for s in stack),
                    "Input": input_content,
                    "Action": f"Error: no goto for state {state}, non-terminal {head}",
                })
                break
            trace.append({
                "Stack": " ".join(str(s) for s in stack),
                "Input": input_content,
                "Action": f"Reduce r{prod_index}: {head} → {' '.join(body)}",
            })
            stack.extend([head, goto_state])
        elif act == "acc":
            trace.append({
                "Stack": stack_content,
                "Input": input_content,
                "Action": "Accept",
            })
            break
    return trace


def _tokenize_input(input_string: str, action: Dict) -> List[str]:
    """Tokenize input by greedily matching known terminals, ignoring spaces."""
    known_terminals = set()
    for (state, sym) in action:
        if sym != "$":
            known_terminals.add(sym)

    # Longest terminals first so 'id' matches before 'i', 'num' before 'n', etc.
    known_terminals_sorted = sorted(known_terminals, key=len, reverse=True)

    tokens = []
    i = 0
    while i < len(input_string):
        if input_string[i] == " ":
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


def slr_parse_with_steps(grammar_text: str, input_string: str):
    steps: List[str] = []
    start_symbol, productions = _parse_grammar(grammar_text)

    # Compute follow on the original grammar (before augmentation mutates productions)
    ff_result = compute_first_follow_with_steps(grammar_text)
    follow_sets = ff_result["follow_sets"]  # keys = original non-terminals only

    C, transitions, augmented_start = items_canonical_collection(start_symbol, productions, steps)

    action, goto_table, prod_list = build_slr_parsing_table(
        C, transitions, productions, augmented_start, follow_sets, steps
    )

    states_readable: List[Dict[str, Any]] = []
    for idx, I in enumerate(C):
        items_strings = []
        for head, body, dot in sorted(I):
            body_syms = list(body)
            body_syms.insert(dot, "•")
            items_strings.append(f"{head} -> {' '.join(body_syms)}")
        states_readable.append({"index": idx, "items": items_strings})

    symbols = set()
    for (i, a), act in action.items():
        symbols.add(a)
    for (i, A), j in goto_table.items():
        symbols.add(A)
    terminals = sorted(s for s in symbols if not s.isupper())
    non_terminals = sorted(s for s in symbols if s.isupper())

    def fmt_action(val: str) -> str:
        if not val:
            return ""
        if val == "acc":
            return "Accept"
        if val.startswith("s"):
            return "S" + val[1:]
        return val

    table_rows = []
    for i in range(len(C)):
        row = {"state": i}
        for a in terminals:
            row[a] = fmt_action(action.get((i, a), ""))
        for A in non_terminals:
            row[A] = str(goto_table.get((i, A), "")) if (i, A) in goto_table else ""
        table_rows.append(row)

    augmented_grammar_list: List[Dict[str, Any]] = []
    for r, (head, body) in enumerate(
        [(augmented_start, tuple(productions[augmented_start][0]))] + prod_list
    ):
        augmented_grammar_list.append({"rule": f"r{r}", "head": head, "body": body})

    goto_transitions: List[Dict[str, Any]] = []
    for (i, X), j in sorted(transitions.items(), key=lambda x: (x[0][0], x[0][1])):
        items_in_j = states_readable[j]["items"]
        goto_transitions.append({"from_state": i, "symbol": X, "to_state": j, "items": items_in_j})

    parse_trace = []
    if input_string.strip():
        tokens = _tokenize_input(input_string.strip(), action)
        parse_trace = simulate_slr_parse(tokens, action, goto_table, prod_list)

    return {
        "grammar_text": grammar_text,
        "start_symbol": start_symbol,
        "augmented_start": augmented_start,
        "productions": productions,
        "augmented_grammar_list": augmented_grammar_list,
        "prod_list": prod_list,
        "states": states_readable,
        "goto_transitions": goto_transitions,
        "follow_sets": follow_sets,
        "action_terminals": terminals,
        "goto_non_terminals": non_terminals,
        "table_rows": table_rows,
        "parse_trace": parse_trace,
        "construction_steps": steps,
        "input_string": input_string.strip(),
    }
