class CodeGeneration:
    def generate_assembly(self, tac):
        assembly = []
        
        for line in tac:
            if '=' in line:
                lhs, rhs = line.split('=', 1)
                lhs = lhs.strip()
                rhs = rhs.strip()
                
                tokens = rhs.split()
                
                if len(tokens) == 1:
                    assembly.append(f'MOV {lhs}, {tokens[0]}')
                elif len(tokens) == 3:
                    operand1, operator, operand2 = tokens
                    
                    assembly.append(f'MOV R1, {operand1}')
                    assembly.append(f'MOV R2, {operand2}')
                    
                    if operator == '+':
                        assembly.append(f'ADD R1, R2')
                    elif operator == '-':
                        assembly.append(f'SUB R1, R2')
                    elif operator == '*':
                        assembly.append(f'MUL R1, R2')
                    elif operator == '/':
                        assembly.append(f'DIV R1, R2')
                    
                    assembly.append(f'MOV {lhs}, R1')
        
        return assembly
