# 🖥️ Compiler Design Virtual Lab

Ek interactive educational tool jo compiler ke sabhi phases ko simulate karta hai.
Python, Flask, Graphviz, aur Pandas se bana hua full-stack web application.

---

## 📁 Project Structure

```
compiler-design-lab/
│
├── app.py                        # Main Flask application - sabhi routes yahan hain
├── requirements.txt              # Sabhi Python dependencies
├── run.bat                       # Windows pe directly run karne ke liye
├── setup.bat                     # First-time setup script
├── README.md                     # Yeh file
│
├── modules/                      # Sabhi algorithm implementations
│   ├── __init__.py
│   ├── regex_to_nfa.py           # Regex → NFA (Thompson's Construction)
│   ├── nfa_to_dfa.py             # NFA → DFA (Subset Construction)
│   ├── direct_dfa.py             # Direct DFA (Syntax Tree method)
│   ├── dfa_minimization.py       # DFA Minimization (Partition Refinement)
│   ├── lexical_analyzer.py       # Lexical Analysis (Tokenizer)
│   ├── ll1_parser.py             # LL(1) Parser (Top-Down)
│   ├── slr_parser.py             # SLR Parser (Bottom-Up)
│   ├── three_address_code.py     # TAC, Quadruples, Triples
│   ├── code_optimization.py      # Constant Folding, Dead Code, Copy Propagation
│   └── code_generation.py        # Assembly Code Generation
│
├── templates/                    # HTML pages (Jinja2 templates)
│   ├── base.html                 # Common layout (navbar, footer)
│   ├── index.html                # Home page
│   ├── regex_to_nfa.html
│   ├── nfa_to_dfa.html
│   ├── direct_dfa.html
│   ├── dfa_minimization.html
│   ├── lexical_analyzer.html
│   ├── ll1_parser.html
│   ├── slr_parser.html
│   ├── three_address_code.html
│   ├── code_optimization.html
│   ├── code_generation.html
│   └── compiler_phases.html
│
└── static/
    └── css/
        └── style.css             # Custom styling
```

---

## 📦 Libraries Used

| Library      | Version   | Kaam kya karta hai                                      |
|--------------|-----------|----------------------------------------------------------|
| `Flask`      | 3.0.0     | Web framework - routes, templates, form handling         |
| `graphviz`   | 0.20.1    | NFA/DFA diagrams SVG format mein banata hai              |
| `pandas`     | 2.1.4     | Tables (FIRST/FOLLOW/Action/Goto) HTML mein convert karta hai |
| `re`         | built-in  | Lexical analyzer mein regex pattern matching             |

Install karne ke liye:
```bash
pip install -r requirements.txt
```

---

## 🚀 Application Kaise Chalayein

### Step 1 - Graphviz Install Karein (Windows)
- Download: https://graphviz.org/download/
- Install karein aur PATH mein add karein: `C:\Program Files\Graphviz\bin`

### Step 2 - Dependencies Install Karein
```bash
pip install -r requirements.txt
```

### Step 3 - App Run Karein
```bash
python app.py
```

Browser mein kholein: **http://127.0.0.1:5000/**

Ya directly double-click karein: `run.bat`

---

## 📋 Sabhi Modules ka Kaam

---

### 1. `modules/regex_to_nfa.py` — Regex to NFA

**Class:** `RegexToNFA`

**Kya karta hai:**
- Regular expression ko postfix mein convert karta hai (Shunting Yard Algorithm)
- Thompson's Construction se NFA banata hai
- NFA transition table generate karta hai
- Graphviz se NFA diagram (SVG) banata hai

**Route:** `/regex-to-nfa`

**Example Input:** `(a|b)*abb`

**Output:**
- Postfix expression
- NFA transition table
- Visual NFA diagram with start/final states

---

### 2. `modules/nfa_to_dfa.py` — NFA to DFA

**Class:** `NFAToDFA`

**Kya karta hai:**
- ε-closure compute karta hai
- Subset Construction Algorithm se NFA ko DFA mein convert karta hai
- DFA transition table banata hai
- Graphviz se DFA diagram banata hai

**Route:** `/nfa-to-dfa`

**Example Input:** `(a|b)*abb`

**Output:**
- ε-closure table
- DFA transition table
- Visual DFA diagram

---

### 3. `modules/direct_dfa.py` — Direct DFA

**Class:** `DirectDFA`

**Kya karta hai:**
- Regex se directly syntax tree banata hai
- firstpos, lastpos, followpos compute karta hai
- Direct DFA construct karta hai (NFA ke bina)
- Syntax tree aur DFA diagram visualize karta hai

**Route:** `/direct-dfa`

**Example Input:** `(a|b)*abb`

**Output:**
- Syntax tree diagram
- followpos table
- DFA transition table
- DFA diagram

---

### 4. `modules/dfa_minimization.py` — DFA Minimization

**Class:** `DFAMinimization`

**Kya karta hai:**
- Partition Refinement Algorithm use karta hai
- Step-by-step partition history dikhata hai
- Minimized DFA banata hai
- Minimized DFA diagram visualize karta hai

**Route:** `/dfa-minimization`

**Example Input:** `(a|b)*abb`

**Output:**
- Partition steps table
- Minimized DFA transition table
- Minimized DFA diagram

---

### 5. `modules/lexical_analyzer.py` — Lexical Analyzer

**Class:** `LexicalAnalyzer`

**Kya karta hai:**
- Source code ko tokens mein todta hai
- Token types: `KEYWORD`, `IDENTIFIER`, `LITERAL`, `OPERATOR`, `PUNCTUATION`
- Symbol table banata hai (identifiers ke liye)
- Line numbers track karta hai
- Python `re` module use karta hai pattern matching ke liye

**Route:** `/lexical-analyzer`

**Example Input:**
```c
int main() {
    int a = 10;
    return a;
}
```

**Output:**
- Token table (Line, Type, Value)
- Symbol table (ID, Name, Type)

---

### 6. `modules/ll1_parser.py` — LL(1) Parser

**Class:** `LL1Parser`

**Kya karta hai:**
- Grammar parse karta hai
- Left Recursion remove karta hai
- Left Factoring karta hai
- FIRST sets compute karta hai
- FOLLOW sets compute karta hai
- LL(1) Parsing Table banata hai
- Input string ko step-by-step parse karta hai

**Route:** `/ll1-parser`

**Example Grammar:**
```
E -> T E1
E1 -> + T E1 | ε
T -> F T1
T1 -> * F T1 | ε
F -> ( E ) | id
```

**Example Input String:** `id + id * id`

**Output:**
- Original grammar table
- Grammar after left recursion removal
- Grammar after left factoring
- FIRST sets table
- FOLLOW sets table
- LL(1) Parsing table
- Step-by-step parse trace (Stack | Input | Action)

---

### 7. `modules/slr_parser.py` — SLR Parser

**Class:** `SLRParser`

**Kya karta hai:**
- Grammar augment karta hai (S' → S add karta hai)
- LR(0) items aur canonical collection banata hai
- FOLLOW sets compute karta hai
- ACTION table banata hai (shift/reduce/accept)
- GOTO table banata hai
- Input string ko step-by-step parse karta hai

**Route:** `/slr-parser`

**Example Grammar:**
```
E -> E + T | T
T -> T * F | F
F -> ( E ) | id
```

**Example Input String:** `id + id * id`

**Output:**
- Augmented grammar table
- LR(0) canonical collection (I0, I1, I2...)
- FOLLOW sets table
- ACTION table (s=shift, r=reduce, acc=accept)
- Step-by-step parse trace (Stack | Input | Action)

---

### 8. `modules/three_address_code.py` — Three Address Code

**Class:** `ThreeAddressCode`

**Kya karta hai:**
- Arithmetic expression ko parse karta hai
- Three Address Code (TAC) generate karta hai
- Quadruples banata hai: `(op, arg1, arg2, result)`
- Triples banata hai: `(index, op, arg1, arg2)`

**Route:** `/three-address-code`

**Example Input:** `x = b - c * 2`

**Output TAC:**
```
t1 = c * 2
t2 = b - t1
x = t2
```

**Quadruples Table:**

| Op | Arg1 | Arg2 | Result |
|----|------|------|--------|
| *  | c    | 2    | t1     |
| -  | b    | t1   | t2     |
| =  | t2   |      | x      |

---

### 9. `modules/code_optimization.py` — Code Optimization

**Class:** `CodeOptimization`

**Kya karta hai:**
- **Constant Folding:** `t1 = 2 * 3` → `t1 = 6`
- **Copy Propagation:** `t1 = a`, `t2 = t1 + b` → `t2 = a + b`
- **Dead Code Elimination:** Unused temporary variables remove karta hai
- Har step ka before/after dikhata hai

**Route:** `/code-optimization`

**Example Input:** `x = 2 * 3 + a`

**Optimization Steps:**
1. Original TAC
2. After Constant Folding
3. After Copy Propagation
4. After Dead Code Elimination

---

### 10. `modules/code_generation.py` — Code Generation

**Class:** `CodeGeneration`

**Kya karta hai:**
- TAC ko assembly instructions mein convert karta hai
- Registers R1, R2 use karta hai
- Instructions: `MOV`, `ADD`, `SUB`, `MUL`, `DIV`

**Route:** `/code-generation`

**Example Input:** `x = b - c * 2`

**Output Assembly:**
```asm
MOV R1, c
MOV R2, 2
MUL R1, R2
MOV t1, R1
MOV R1, b
MOV R2, t1
SUB R1, R2
MOV t2, R1
MOV x, t2
```

---

## 🌐 Flask Routes (app.py)

| Route                  | Method     | Module Used              |
|------------------------|------------|--------------------------|
| `/`                    | GET        | index.html               |
| `/regex-to-nfa`        | GET, POST  | RegexToNFA               |
| `/nfa-to-dfa`          | GET, POST  | RegexToNFA + NFAToDFA    |
| `/direct-dfa`          | GET, POST  | DirectDFA                |
| `/dfa-minimization`    | GET, POST  | RegexToNFA + NFAToDFA + DFAMinimization |
| `/lexical-analyzer`    | GET, POST  | LexicalAnalyzer          |
| `/ll1-parser`          | GET, POST  | LL1Parser                |
| `/slr-parser`          | GET, POST  | SLRParser                |
| `/three-address-code`  | GET, POST  | ThreeAddressCode         |
| `/code-optimization`   | GET, POST  | ThreeAddressCode + CodeOptimization |
| `/code-generation`     | GET, POST  | ThreeAddressCode + CodeGeneration |
| `/compiler_phases.html`| GET        | compiler_phases.html     |

---

## 📝 Logging

App mein Flask ka built-in debug logging enabled hai:

```python
app.run(debug=True)
```

**Kya log hota hai:**
- Har HTTP request (GET/POST) terminal mein dikhti hai
- Errors aur exceptions automatically print hote hain
- Template rendering errors Flask console mein aate hain

**Example log output:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
127.0.0.1 - - [GET /ll1-parser HTTP/1.1] 200
127.0.0.1 - - [POST /ll1-parser HTTP/1.1] 200
```

Production logging ke liye `app.py` mein yeh add kar sakte hain:
```python
import logging
logging.basicConfig(level=logging.DEBUG, filename='app.log')
```

---

## 🧪 Test Cases

### LL(1) Parser Test Cases

**Grammar 1 (Expression Grammar):**
```
E -> T E1
E1 -> + T E1 | ε
T -> F T1
T1 -> * F T1 | ε
F -> ( E ) | id
```
Input: `id + id * id`

**Grammar 2 (If-Else):**
```
S -> i E t S S1 | a
S1 -> e S | ε
E -> b
```
Input: `i b t a e a`

---

### SLR Parser Test Cases

**Grammar 1:**
```
E -> E + T | T
T -> T * F | F
F -> ( E ) | id
```
Input: `id + id * id`

**Grammar 2:**
```
S -> A A
A -> a A | b
```
Input: `a a b b`

**Grammar 3:**
```
S -> C C
C -> c C | d
```
Input: `c c d d`

---

### Lexical Analyzer Test Cases

**Test 1:**
```c
int x = 10 + 20;
```

**Test 2:**
```c
float result = a * b - c / 2;
if (result > 0) return result;
```

---

### Three Address Code Test Cases

| Input Expression     | TAC Output                          |
|----------------------|-------------------------------------|
| `x = b - c * 2`      | t1=c*2, t2=b-t1, x=t2              |
| `I = p * n * r / 100`| t1=p*n, t2=t1*r, t3=t2/100, I=t3  |
| `z = a + b * c - d`  | t1=b*c, t2=a+t1, t3=t2-d, z=t3    |

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `graphviz.backend.execute.ExecutableNotFound` | Graphviz install karein aur PATH mein add karein |
| `ModuleNotFoundError: No module named 'flask'` | `pip install -r requirements.txt` chalayein |
| `Grammar is not LL(1)` | Left recursion ya common prefix check karein |
| `SLR conflict` | Grammar ambiguous hai, LALR/LR(1) try karein |
| Port 5000 already in use | `app.run(port=5001)` use karein |

---

## 👨‍🎓 Educational Purpose

Yeh virtual lab compiler design ke students ke liye banaya gaya hai. Har module mein:
- Step-by-step algorithm execution
- Interactive input forms
- Visual diagrams (NFA/DFA)
- Formatted tables (FIRST, FOLLOW, ACTION, GOTO)
- Theory explanations

**Compiler ke 6 Phases:**
1. Lexical Analysis → Tokens
2. Syntax Analysis → Parse Tree (LL1/SLR)
3. Semantic Analysis → Symbol Table
4. Intermediate Code → Three Address Code
5. Code Optimization → Constant Folding, Dead Code
6. Code Generation → Assembly Instructions

---

## 📄 License

MIT License — Free for educational use.
