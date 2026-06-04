class CodeOptimization:
    def constant_folding(self, tac):
        optimized = []
        for line in tac:
            if '=' in line:
                lhs, rhs = line.split('=', 1)
                lhs = lhs.strip()
                rhs = rhs.strip()
                
                try:
                    result = eval(rhs)
                    optimized.append(f'{lhs} = {result}')
                except:
                    optimized.append(line)
            else:
                optimized.append(line)
        
        return optimized
    
    def dead_code_elimination(self, tac):
        used_vars = set()
        
        for line in reversed(tac):
            if '=' in line:
                lhs, rhs = line.split('=', 1)
                lhs = lhs.strip()
                
                for token in rhs.split():
                    if token.isalnum():
                        used_vars.add(token)
        
        optimized = []
        for line in tac:
            if '=' in line:
                lhs, rhs = line.split('=', 1)
                lhs = lhs.strip()
                
                if lhs in used_vars or not lhs.startswith('t'):
                    optimized.append(line)
                    for token in rhs.split():
                        if token.isalnum():
                            used_vars.add(token)
            else:
                optimized.append(line)
        
        return optimized
    
    def copy_propagation(self, tac):
        copies = {}
        optimized = []
        
        for line in tac:
            if '=' in line:
                lhs, rhs = line.split('=', 1)
                lhs = lhs.strip()
                rhs = rhs.strip()
                
                for var, value in copies.items():
                    rhs = rhs.replace(var, value)
                
                if rhs.isalnum() and not rhs.isdigit():
                    copies[lhs] = rhs
                
                optimized.append(f'{lhs} = {rhs}')
            else:
                optimized.append(line)
        
        return optimized
    
    def optimize(self, tac):
        steps = []
        
        steps.append({
            'name': 'Original',
            'code': tac[:]
        })
        
        cf = self.constant_folding(tac)
        steps.append({
            'name': 'Constant Folding',
            'code': cf
        })
        
        cp = self.copy_propagation(cf)
        steps.append({
            'name': 'Copy Propagation',
            'code': cp
        })
        
        dce = self.dead_code_elimination(cp)
        steps.append({
            'name': 'Dead Code Elimination',
            'code': dce
        })
        
        return steps
