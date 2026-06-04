import re
from typing import List, Dict, Any, Tuple
from .sdd import Node, _tree_to_html


class SDTTranslator:
    """
    Grammar with embedded translation actions.
    Produces: TAC steps, annotated parse tree, postfix expression.
    """

    def __init__(self):
        self.temp_count = 0
        self.steps: List[Dict] = []
        self.code: List[str] = []
        self.postfix_tokens: List[str] = []

    def _new_temp(self) -> str:
        self.temp_count += 1
        return f't{self.temp_count}'

    def tokenize(self, expr: str) -> List[str]:
        return re.findall(r'\d+\.\d+|\d+|[a-zA-Z_]\w*|[+\-*/()]', expr)

    def _parse_E(self, tokens, pos) -> Tuple[str, int, Node]:
        place, pos, node = self._parse_T(tokens, pos)
        e_node = Node('E', place)
        e_node.add(node)

        while pos < len(tokens) and tokens[pos] in ('+', '-'):
            op = tokens[pos]; pos += 1
            rplace, pos, r_node = self._parse_T(tokens, pos)
            t = self._new_temp()
            instr = f'{t} = {place} {op} {rplace}'
            self.code.append(instr)
            self.postfix_tokens.append(op)

            new_e = Node('E', t)
            new_e.add(e_node)
            new_e.add(Node(op))
            new_e.add(r_node)
            e_node = new_e

            self.steps.append({
                'Step': len(self.steps) + 1,
                'Production': f'E → E {op} T',
                'Semantic Action': f'E.place = {t}',
                'Generated Code': instr,
            })
            place = t

        e_node.val = place
        return place, pos, e_node

    def _parse_T(self, tokens, pos) -> Tuple[str, int, Node]:
        place, pos, node = self._parse_F(tokens, pos)
        t_node = Node('T', place)
        t_node.add(node)

        while pos < len(tokens) and tokens[pos] in ('*', '/'):
            op = tokens[pos]; pos += 1
            rplace, pos, r_node = self._parse_F(tokens, pos)
            t = self._new_temp()
            instr = f'{t} = {place} {op} {rplace}'
            self.code.append(instr)
            self.postfix_tokens.append(op)

            new_t = Node('T', t)
            new_t.add(t_node)
            new_t.add(Node(op))
            new_t.add(r_node)
            t_node = new_t

            self.steps.append({
                'Step': len(self.steps) + 1,
                'Production': f'T → T {op} F',
                'Semantic Action': f'T.place = {t}',
                'Generated Code': instr,
            })
            place = t

        t_node.val = place
        return place, pos, t_node

    def _parse_F(self, tokens, pos) -> Tuple[str, int, Node]:
        if pos < len(tokens) and tokens[pos] == '(':
            pos += 1
            place, pos, inner = self._parse_E(tokens, pos)
            pos += 1  # ')'
            f_node = Node('F', place)
            f_node.add(Node('('))
            f_node.add(inner)
            f_node.add(Node(')'))
            return place, pos, f_node

        tok = tokens[pos]; pos += 1
        prod = 'F → num' if re.match(r'^\d', tok) else 'F → id'
        self.postfix_tokens.append(tok)
        f_node = Node('F', tok)
        f_node.add(Node(tok))
        self.steps.append({
            'Step': len(self.steps) + 1,
            'Production': prod,
            'Semantic Action': f'F.place = {tok}',
            'Generated Code': '',
        })
        return tok, pos, f_node

    def translate(self, expression: str) -> Dict[str, Any]:
        self.temp_count = 0
        self.steps = []
        self.code = []
        self.postfix_tokens = []
        tokens = self.tokenize(expression)
        try:
            result_place, _, tree = self._parse_E(tokens, 0)
            error = None
            tree_html = f'<ul class="tree">{_tree_to_html(tree)}</ul>'
        except Exception as e:
            result_place = None
            error = str(e)
            tree_html = None

        return {
            'expression': expression,
            'steps': self.steps,
            'code': self.code,
            'result_place': result_place,
            'postfix': ' '.join(self.postfix_tokens),
            'tree_html': tree_html,
            'error': error,
        }
