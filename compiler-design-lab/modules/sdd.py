import re
from typing import List, Dict, Any, Tuple


class Node:
    def __init__(self, label: str, val=None):
        self.label = label
        self.val = val
        self.children: List['Node'] = []

    def add(self, child: 'Node'):
        self.children.append(child)
        return child


def _tree_to_html(node: Node) -> str:
    """Render parse tree as nested <ul> HTML."""
    val_str = f'<br><small class="text-success fw-bold">.val = {node.val}</small>' if node.val is not None else ''
    label_html = f'<span class="tree-node">{node.label}{val_str}</span>'
    if not node.children:
        return f'<li>{label_html}</li>'
    children_html = ''.join(_tree_to_html(c) for c in node.children)
    return f'<li>{label_html}<ul>{children_html}</ul></li>'


class SDDEvaluator:
    """
    Grammar:
        E -> E + T | E - T | T
        T -> T * F | T / F | F
        F -> ( E ) | num | id
    Synthesized attribute: .val
    """

    def tokenize(self, expr: str) -> List[str]:
        return re.findall(r'\d+\.\d+|\d+|[a-zA-Z_]\w*|[+\-*/()]', expr)

    def _parse_E(self, tokens, pos, steps) -> Tuple[any, int, Node]:
        val, pos, node = self._parse_T(tokens, pos, steps)
        e_node = Node('E', val)
        e_node.add(node)

        while pos < len(tokens) and tokens[pos] in ('+', '-'):
            op = tokens[pos]; pos += 1
            rval, pos, r_node = self._parse_T(tokens, pos, steps)
            result = val + rval if op == '+' else val - rval

            new_e = Node('E', result)
            new_e.add(Node(op))
            new_e.add(r_node)
            # move existing e_node as left child
            new_e.children.insert(0, e_node)
            e_node = new_e

            steps.append({
                'Step': len(steps) + 1,
                'Production': f'E → E {op} T',
                'Attribute Rule': f'E.val = {val} {op} {rval} = {result}',
                'Value': result
            })
            val = result

        e_node.val = val
        return val, pos, e_node

    def _parse_T(self, tokens, pos, steps) -> Tuple[any, int, Node]:
        val, pos, node = self._parse_F(tokens, pos, steps)
        t_node = Node('T', val)
        t_node.add(node)

        while pos < len(tokens) and tokens[pos] in ('*', '/'):
            op = tokens[pos]; pos += 1
            rval, pos, r_node = self._parse_F(tokens, pos, steps)
            result = val * rval if op == '*' else (val / rval if rval != 0 else 0)

            new_t = Node('T', result)
            new_t.add(t_node)
            new_t.add(Node(op))
            new_t.add(r_node)
            t_node = new_t

            steps.append({
                'Step': len(steps) + 1,
                'Production': f'T → T {op} F',
                'Attribute Rule': f'T.val = {val} {op} {rval} = {result}',
                'Value': result
            })
            val = result

        t_node.val = val
        return val, pos, t_node

    def _parse_F(self, tokens, pos, steps) -> Tuple[any, int, Node]:
        if pos < len(tokens) and tokens[pos] == '(':
            pos += 1
            val, pos, inner = self._parse_E(tokens, pos, steps)
            pos += 1  # ')'
            f_node = Node('F', val)
            f_node.add(Node('('))
            f_node.add(inner)
            f_node.add(Node(')'))
            return val, pos, f_node

        tok = tokens[pos]; pos += 1
        try:
            val = float(tok) if '.' in tok else int(tok)
            prod = 'F → num'
        except ValueError:
            val = tok
            prod = 'F → id'

        f_node = Node('F', val)
        f_node.add(Node(tok))
        steps.append({
            'Step': len(steps) + 1,
            'Production': prod,
            'Attribute Rule': f'F.val = {tok}',
            'Value': val
        })
        return val, pos, f_node

    def evaluate(self, expression: str) -> Dict[str, Any]:
        tokens = self.tokenize(expression)
        steps: List[Dict] = []
        try:
            val, _, tree = self._parse_E(tokens, 0, steps)
            final = val
            error = None
            tree_html = f'<ul class="tree">{_tree_to_html(tree)}</ul>'
        except Exception as e:
            final = None
            error = str(e)
            tree_html = None

        attr_table = [
            {'Node': f'n{i}', 'Production': s['Production'], 'Attribute': s['Attribute Rule']}
            for i, s in enumerate(steps)
        ]

        return {
            'tokens': tokens,
            'steps': steps,
            'attr_table': attr_table,
            'final_val': final,
            'error': error,
            'tree_html': tree_html,
            'expression': expression,
        }
