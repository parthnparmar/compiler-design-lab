import re

class LexicalAnalyzer:
    def __init__(self):
        self.keywords = {'if', 'else', 'while', 'for', 'int', 'float', 'return', 'void', 'main'}
        self.operators = {'+', '-', '*', '/', '=', '==', '!=', '<', '>', '<=', '>=', '&&', '||', '!'}
        self.punctuation = {';', ',', '(', ')', '{', '}', '[', ']'}
        
    def analyze(self, source_code):
        tokens = []
        symbol_table = {}
        symbol_id = 1
        
        token_patterns = [
            ('NUMBER', r'\d+(\.\d+)?'),
            ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
            ('OPERATOR', r'==|!=|<=|>=|&&|\|\||[+\-*/=<>!]'),
            ('PUNCTUATION', r'[;,(){}[\]]'),
            ('STRING', r'"[^"]*"'),
            ('WHITESPACE', r'\s+'),
        ]
        
        pattern = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_patterns)
        regex = re.compile(pattern)
        
        line_num = 1
        for match in regex.finditer(source_code):
            token_type = match.lastgroup
            token_value = match.group()
            
            if token_type == 'WHITESPACE':
                if '\n' in token_value:
                    line_num += token_value.count('\n')
                continue
            
            if token_type == 'IDENTIFIER':
                if token_value in self.keywords:
                    token_type = 'KEYWORD'
                else:
                    if token_value not in symbol_table:
                        symbol_table[token_value] = {
                            'id': symbol_id,
                            'type': 'identifier',
                            'value': token_value
                        }
                        symbol_id += 1
            elif token_type == 'NUMBER':
                token_type = 'LITERAL'
            elif token_type == 'STRING':
                token_type = 'LITERAL'
            
            tokens.append({
                'line': line_num,
                'type': token_type,
                'value': token_value
            })
        
        return tokens, symbol_table
