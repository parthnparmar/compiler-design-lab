import re
from typing import List, Dict, Any, Tuple


class ExpressionTranslator:
    """Translate arithmetic expression into Quadruples, Triples, Indirect Triples."""

    def __init__(self):
        self.temp_count = 0
        self.steps: List[Dict] = []
        self.quads: List[Tuple] = []   # (op, arg1, arg2, result)
        self.triple_args: List[Tuple] = []  # (op, a1_str, a2_str) with (i) refs

    def _new_temp(self) -> str:
        self.temp_count += 1
        return f't{self.temp_count}'

    def tokenize(self, expr: str) -> List[str]:
        return re.findall(r'\d+\.\d+|\d+|[a-zA-Z_]\w*|[+\-*/()]', expr)

    def _triple_ref(self, arg: str) -> str:
        """If arg is a temp that maps to a quad index, return (i), else return arg."""
        for i, q in enumerate(self.quads):
            if q[3] == arg:
                return f'({i})'
        return arg

    def _emit(self, op: str, arg1: str, arg2: str) -> str:
        t = self._new_temp()
        # triple references
        a1 = self._triple_ref(arg1)
        a2 = self._triple_ref(arg2)
        self.quads.append((op, arg1, arg2, t))
        self.triple_args.append((op, a1, a2))
        self.steps.append({
            'Step': len(self.steps) + 1,
            'Instruction': f'{t} = {arg1} {op} {arg2}',
        })
        return t

    def _parse_E(self, tokens, pos) -> Tuple[str, int]:
        place, pos = self._parse_T(tokens, pos)
        while pos < len(tokens) and tokens[pos] in ('+', '-'):
            op = tokens[pos]; pos += 1
            rplace, pos = self._parse_T(tokens, pos)
            place = self._emit(op, place, rplace)
        return place, pos

    def _parse_T(self, tokens, pos) -> Tuple[str, int]:
        place, pos = self._parse_F(tokens, pos)
        while pos < len(tokens) and tokens[pos] in ('*', '/'):
            op = tokens[pos]; pos += 1
            rplace, pos = self._parse_F(tokens, pos)
            place = self._emit(op, place, rplace)
        return place, pos

    def _parse_F(self, tokens, pos) -> Tuple[str, int]:
        if pos < len(tokens) and tokens[pos] == '(':
            pos += 1
            place, pos = self._parse_E(tokens, pos)
            pos += 1  # ')'
            return place, pos
        return tokens[pos], pos + 1

    def translate(self, expression: str) -> Dict[str, Any]:
        self.temp_count = 0
        self.steps = []
        self.quads = []
        self.triple_args = []

        tokens = self.tokenize(expression)
        try:
            result, _ = self._parse_E(tokens, 0)
            error = None
        except Exception as e:
            result = None
            error = str(e)

        quad_rows = [
            {'Index': i, 'Operator': q[0], 'Arg1': q[1], 'Arg2': q[2], 'Result': q[3]}
            for i, q in enumerate(self.quads)
        ]
        triple_rows = [
            {'Index': i, 'Operator': t[0], 'Arg1': t[1], 'Arg2': t[2]}
            for i, t in enumerate(self.triple_args)
        ]
        pointer_rows = [
            {'Pointer': f'P{i}', 'Statement': i}
            for i in range(len(self.triple_args))
        ]

        return {
            'expression': expression,
            'steps': self.steps,
            'quad_rows': quad_rows,
            'triple_rows': triple_rows,
            'pointer_rows': pointer_rows,
            'indirect_triple_rows': triple_rows,
            'result': result,
            'error': error,
        }
