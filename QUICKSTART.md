# Quick Start Guide

## ✅ Both parsers are now working correctly!

### LL(1) Parser - Quick Test

```bash
python ll1_parser.py
```

**Input:**
```
E -> T E'
E' -> + T E' | ε
T -> F T'
T' -> * F T' | ε
F -> ( E ) | id
done
id + id * id
```

### SLR Parser - Quick Test

```bash
python slr_parser.py
```

**Input:**
```
E -> E + T | T
T -> T * F | F
F -> ( E ) | id
done
id + id * id
```

## ✨ Key Features

### LL(1) Parser
- ✅ Computes FIRST and FOLLOW sets correctly
- ✅ Builds LL(1) parsing table
- ✅ Detects conflicts (not LL(1))
- ✅ Parses any valid LL(1) grammar
- ✅ Step-by-step parsing with stack visualization

### SLR Parser
- ✅ Augments grammar automatically
- ✅ Builds LR(0) canonical collection
- ✅ Computes FOLLOW sets
- ✅ Builds SLR parsing table (ACTION/GOTO)
- ✅ Detects shift-reduce and reduce-reduce conflicts
- ✅ Parses any valid SLR(1) grammar
- ✅ Step-by-step parsing with stack visualization

## 📝 Grammar Rules

1. Use `->` to separate LHS from RHS
2. Use `|` for multiple productions
3. Use `ε` for epsilon (empty production)
4. Terminals: lowercase or symbols (id, +, *, (, ), a, b, etc.)
5. Non-terminals: uppercase (E, T, F, S, A, B, etc.)

## 🧪 More Test Cases

### LL(1) Examples

**Simple Grammar:**
```
S -> A B
A -> a | ε
B -> b
done
a b
```

**If-Then-Else:**
```
S -> i E t S S' | a
S' -> e S | ε
E -> b
done
i b t a e a
```

### SLR Examples

**Simple Grammar:**
```
S -> A A
A -> a A | b
done
a a b b
```

**List Grammar:**
```
S -> ( L ) | a
L -> L , S | S
done
( a , a )
```

**Assignment Grammar:**
```
S -> L = R | R
L -> * R | id
R -> L
done
id = * id
```

## 🎯 Tips

- **For LL(1)**: Avoid left recursion and common prefixes
- **For SLR**: Left recursion is OK, but watch for conflicts
- **Token Separation**: Use spaces between tokens (e.g., `id + id` not `id+id`)
- **Epsilon**: Use `ε` character for empty productions
- **Start Symbol**: First production's LHS is the start symbol

## 🔧 Run Automated Tests

```bash
python test_ll1.py
python test_slr.py
```

These will test multiple grammars automatically!
