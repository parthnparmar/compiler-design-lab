class ThreeAddressCode:
    def __init__(self):
        self.temp_count = 0
        self.tac = []
        self.quadruples = []
        self.triples = []
        
    def new_temp(self):
        self.temp_count += 1
        return f't{self.temp_count}'
    
    def parse_expression(self, expr):
        expr = expr.replace(' ', '')
        if '=' in expr:
            lhs, rhs = expr.split('=', 1)
            result = self.generate_tac(rhs)
            self.tac.append(f'{lhs} = {result}')
            self.quadruples.append(('=', result, '', lhs))
            self.triples.append(('=', result, lhs))
            return lhs
        else:
            return self.generate_tac(expr)
    
    def generate_tac(self, expr):
        expr = expr.strip()
        
        for op in ['+', '-']:
            parts = self.split_by_operator(expr, op)
            if len(parts) > 1:
                left = self.generate_tac(parts[0])
                for i in range(1, len(parts)):
                    right = self.generate_tac(parts[i])
                    temp = self.new_temp()
                    self.tac.append(f'{temp} = {left} {op} {right}')
                    self.quadruples.append((op, left, right, temp))
                    self.triples.append((op, left, right))
                    left = temp
                return left
        
        for op in ['*', '/']:
            parts = self.split_by_operator(expr, op)
            if len(parts) > 1:
                left = self.generate_tac(parts[0])
                for i in range(1, len(parts)):
                    right = self.generate_tac(parts[i])
                    temp = self.new_temp()
                    self.tac.append(f'{temp} = {left} {op} {right}')
                    self.quadruples.append((op, left, right, temp))
                    self.triples.append((op, left, right))
                    left = temp
                return left
        
        if expr.startswith('(') and expr.endswith(')'):
            return self.generate_tac(expr[1:-1])
        
        return expr
    
    def split_by_operator(self, expr, op):
        parts = []
        current = ''
        depth = 0
        
        for char in expr:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            
            if char == op and depth == 0:
                if current:
                    parts.append(current)
                    current = ''
            else:
                current += char
        
        if current:
            parts.append(current)
        
        return parts if len(parts) > 1 else [expr]
    
    def generate(self, expression):
        self.temp_count = 0
        self.tac = []
        self.quadruples = []
        self.triples = []
        
        self.parse_expression(expression)
        
        return {
            'tac': self.tac,
            'quadruples': self.quadruples,
            'triples': self.triples
        }
