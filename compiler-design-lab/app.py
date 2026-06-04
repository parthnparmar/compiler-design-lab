import os, re, random, string
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from models import db, User
from modules.regex_to_nfa import RegexToNFA
from modules.nfa_to_dfa import NFAToDFA
from modules.direct_dfa import DirectDFA
from modules.dfa_minimization import DFAMinimization
from modules.lexical_analyzer import LexicalAnalyzer
from modules.ll1_parser import LL1Parser
from modules.slr_parser import slr_parse_with_steps
from modules.clr_parser import clr_parse_with_steps, lalr_parse_with_steps
from modules.sdd import SDDEvaluator
from modules.sdt import SDTTranslator
from modules.expr_translation import ExpressionTranslator
from modules.three_address_code import ThreeAddressCode
from modules.code_optimization import CodeOptimization
from modules.code_generation import CodeGeneration

# ── Graphviz path (Windows) ──────────────────────────────────────────────────
if os.name == 'nt':
    gv = r'C:\Program Files\Graphviz\bin'
    if os.path.exists(gv):
        os.environ['PATH'] += os.pathsep + gv

# ── App config ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cdlab-secret-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Email config (Gmail SMTP) ───────────────────────────────────────────────
app.config['MAIL_SERVER']        = 'smtp.gmail.com'
app.config['MAIL_PORT']          = 587
app.config['MAIL_USE_TLS']       = True
app.config['MAIL_USE_SSL']       = False
app.config['MAIL_USERNAME']      = os.environ.get('MAIL_USERNAME', 'pp0273888@gmail.com')
app.config['MAIL_PASSWORD']      = os.environ.get('MAIL_PASSWORD', 'ifol srrv ahaj ytfa')
app.config['MAIL_DEFAULT_SENDER'] = ('Compiler Design Lab', os.environ.get('MAIL_USERNAME', 'pp0273888@gmail.com'))
app.config['MAIL_MAX_EMAILS']    = None
app.config['MAIL_ASCII_ATTACHMENTS'] = False

db.init_app(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'

CORS(app, resources={r'/api/*': {'origins': '*', 'allow_headers': ['Content-Type'],
                                  'methods': ['GET', 'POST', 'OPTIONS']}})

@app.after_request
def cors_headers(r):
    r.headers['Access-Control-Allow-Origin']  = '*'
    r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    r.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return r

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

# ── Create DB tables ─────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    error = success = None
    if request.method == 'POST':
        firstname = request.form.get('firstname', '').strip()
        lastname  = request.form.get('lastname',  '').strip()
        username  = request.form.get('username',  '').strip()
        email     = request.form.get('email',     '').strip().lower()
        password  = request.form.get('password',  '')
        confirm   = request.form.get('confirm',   '')
        if not all([firstname, lastname, username, email, password]):
            error = 'All fields are required.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif User.query.filter_by(username=username).first():
            error = f'Username "{username}" is already taken.'
        elif User.query.filter_by(email=email).first():
            error = 'An account with this email already exists.'
        else:
            user = User(firstname=firstname, lastname=lastname,
                        username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            success = f'Account created for {firstname}! You can now login.'
    return render_template('register.html', error=error, success=success)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        error = 'Invalid username or password.'
    return render_template('login.html', error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            otp = ''.join(random.choices(string.digits, k=6))
            user.otp_code   = otp
            user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
            db.session.commit()
            try:
                msg = Message('Password Reset OTP — Compiler Design Lab', recipients=[email])
                msg.body = (f'Hello {user.firstname},\n\nYour OTP is: {otp}\n\nValid for 10 minutes.')
                mail.send(msg)
            except Exception:
                pass
            return redirect(url_for('reset_password', email=email))
        else:
            error = 'No account found with that email.'
    return render_template('forgot_password.html', error=error)


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    error = success = None
    email = request.args.get('email', '')
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        otp      = request.form.get('otp', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')
        user = User.query.filter_by(email=email).first()
        if not user or user.otp_code != otp:
            error = 'Invalid OTP.'
        elif user.otp_expiry < datetime.utcnow():
            error = 'OTP has expired. Please request a new one.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        else:
            user.set_password(password)
            user.otp_code = None
            user.otp_expiry = None
            db.session.commit()
            success = 'Password reset successful! You can now login.'
            return redirect(url_for('login'))
    return render_template('reset_password.html', email=email, error=error, success=success)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


# ═══════════════════════════════════════════════════════════════════════════════
# WEBSITE ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/compiler_phases.html')
def compiler_phases():
    return render_template('compiler_phases.html')

@app.route('/regex-to-nfa', methods=['GET', 'POST'])
def regex_to_nfa():
    if request.method == 'POST':
        regex = request.form.get('regex')
        converter = RegexToNFA()
        nfa, postfix = converter.construct_nfa(regex)
        table   = converter.create_transition_table(nfa)
        diagram = converter.visualize_nfa(nfa)
        return render_template('regex_to_nfa.html', regex=regex, postfix=postfix,
            table=pd.DataFrame(table).to_html(classes='table table-bordered', index=False),
            diagram=diagram.pipe(format='svg').decode('utf-8'),
            start=f'q{nfa["start"]}', end=f'q{nfa["end"]}')
    return render_template('regex_to_nfa.html')

@app.route('/nfa-to-dfa', methods=['GET', 'POST'])
def nfa_to_dfa():
    if request.method == 'POST':
        regex = request.form.get('regex')
        converter = RegexToNFA()
        nfa, _ = converter.construct_nfa(regex)
        dfa_converter = NFAToDFA()
        dfa     = dfa_converter.convert(nfa)
        table   = dfa_converter.create_transition_table(dfa)
        diagram = dfa_converter.visualize_dfa(dfa)
        epsilon_closures = []
        for states, closure in dfa['epsilon_closures'].items():
            if states != closure:
                epsilon_closures.append({
                    'States':    '{' + ', '.join([f'q{s}' for s in sorted(states)]) + '}',
                    'ε-closure': '{' + ', '.join([f'q{s}' for s in sorted(closure)]) + '}'})
        return render_template('nfa_to_dfa.html', regex=regex,
            table=pd.DataFrame(table).to_html(classes='table table-bordered', index=False),
            diagram=diagram.pipe(format='svg').decode('utf-8'),
            epsilon_closures=pd.DataFrame(epsilon_closures).to_html(classes='table table-bordered', index=False) if epsilon_closures else None)
    return render_template('nfa_to_dfa.html')

@app.route('/direct-dfa', methods=['GET', 'POST'])
def direct_dfa():
    if request.method == 'POST':
        regex = request.form.get('regex')
        converter = DirectDFA()
        result = converter.construct_dfa(regex)
        if not result['tree']:
            return render_template('direct_dfa.html', regex=regex, error='Invalid regular expression')
        tree_diagram = converter.visualize_tree(result['tree'])
        followpos_table = []
        for pos in sorted(result['followpos'].keys()):
            if pos in result['pos_symbols']:
                followpos_table.append({'Position': pos, 'Symbol': result['pos_symbols'][pos],
                    'followpos': '{' + ', '.join(map(str, sorted(result['followpos'][pos]))) + '}'})
        dfa_table = []
        for state in result['states']:
            row = {'State': 'S' + str(result['state_map'][frozenset(state)]),
                   'Positions': '{' + ', '.join(map(str, sorted(state))) + '}'}
            for symbol in result['symbols']:
                ns = result['transitions'].get(frozenset(state), {}).get(symbol)
                row[symbol] = 'S' + str(result['state_map'][ns]) if ns else '-'
            dfa_table.append(row)
        return render_template('direct_dfa.html', regex=regex,
            tree_diagram=tree_diagram.pipe(format='svg').decode('utf-8') if tree_diagram else None,
            dfa_diagram=converter.visualize_dfa(result).pipe(format='svg').decode('utf-8') if result['states'] else None,
            followpos_table=pd.DataFrame(followpos_table).to_html(classes='table table-bordered', index=False) if followpos_table else None,
            dfa_table=pd.DataFrame(dfa_table).to_html(classes='table table-bordered', index=False) if dfa_table else None)
    return render_template('direct_dfa.html')

@app.route('/dfa-minimization', methods=['GET', 'POST'])
def dfa_minimization():
    if request.method == 'POST':
        regex = request.form.get('regex')
        converter = RegexToNFA(); nfa, _ = converter.construct_nfa(regex)
        dfa_converter = NFAToDFA(); dfa = dfa_converter.convert(nfa)
        minimizer = DFAMinimization(); min_dfa = minimizer.minimize(dfa)
        diagram = minimizer.visualize_minimized_dfa(min_dfa)
        partition_steps = []
        for i, partition in enumerate(min_dfa['partition_history']):
            step = {'Step': i}
            for j, group in enumerate(partition):
                states = ', '.join([f'D{dfa["state_map"][s]}' for s in group])
                step[f'P{j}'] = '{' + states + '}'
            partition_steps.append(step)
        min_table = []
        for state in min_dfa['states']:
            row = {'State': f'S{state}'}
            for symbol in min_dfa['symbols']:
                ns = min_dfa['transitions'].get(state, {}).get(symbol)
                row[symbol] = f'S{ns}' if ns is not None else '-'
            min_table.append(row)
        return render_template('dfa_minimization.html', regex=regex,
            partition_steps=pd.DataFrame(partition_steps).to_html(classes='table table-bordered', index=False),
            min_table=pd.DataFrame(min_table).to_html(classes='table table-bordered', index=False),
            diagram=diagram.pipe(format='svg').decode('utf-8'))
    return render_template('dfa_minimization.html')

@app.route('/lexical-analyzer', methods=['GET', 'POST'])
def lexical_analyzer():
    if request.method == 'POST':
        source_code = request.form.get('source_code')
        analyzer = LexicalAnalyzer()
        tokens, symbol_table = analyzer.analyze(source_code)
        symbol_list = [{'ID': v['id'], 'Name': k, 'Type': v['type']} for k, v in symbol_table.items()]
        return render_template('lexical_analyzer.html', source_code=source_code,
            tokens=pd.DataFrame(tokens).to_html(classes='table table-bordered', index=False),
            symbols=pd.DataFrame(symbol_list).to_html(classes='table table-bordered', index=False) if symbol_list else None)
    return render_template('lexical_analyzer.html')

@app.route('/ll1-parser', methods=['GET', 'POST'])
def ll1_parser():
    if request.method == 'POST':
        grammar_text = request.form.get('grammar')
        start_symbol = request.form.get('start_symbol')
        input_string = request.form.get('input_string')
        parser = LL1Parser()
        grammar = parser.parse_grammar(grammar_text)
        original_grammar_list = [{'LHS': lhs, 'Production': f'{lhs} → {prod}'}
            for lhs in parser.original_grammar for prod in parser.original_grammar[lhs]]
        grammar_after_lr = parser.remove_left_recursion(grammar)
        left_recursion_list = [{'LHS': lhs, 'Production': f'{lhs} → {prod}'}
            for lhs in parser.after_left_recursion for prod in parser.after_left_recursion[lhs]]
        has_left_recursion = any(lhs not in parser.original_grammar or prod not in parser.original_grammar.get(lhs, [])
            for lhs in parser.after_left_recursion for prod in parser.after_left_recursion[lhs])
        grammar_after_lf = parser.left_factor(grammar_after_lr)
        left_factoring_list = [{'LHS': lhs, 'Production': f'{lhs} → {prod}'}
            for lhs in parser.after_left_factoring for prod in parser.after_left_factoring[lhs]]
        has_left_factoring = any(lhs not in parser.after_left_recursion or prod not in parser.after_left_recursion.get(lhs, [])
            for lhs in parser.after_left_factoring for prod in parser.after_left_factoring[lhs])
        final_grammar = grammar_after_lf
        first_sets    = parser.compute_first(final_grammar)
        follow_sets   = parser.compute_follow(final_grammar, start_symbol)
        parsing_table = parser.build_parsing_table(final_grammar, start_symbol)
        first_table   = [{'Non-terminal': nt, 'FIRST':  '{ ' + ', '.join(sorted(first_sets[nt]))  + ' }'} for nt in final_grammar]
        follow_table  = [{'Non-terminal': nt, 'FOLLOW': '{ ' + ', '.join(sorted(follow_sets[nt])) + ' }'} for nt in final_grammar]
        table_data = []
        for nt in final_grammar:
            row = {'Non-terminal': nt}
            for terminal in sorted(set(t for trans in parsing_table.values() for t in trans.keys())):
                prod = parsing_table[nt].get(terminal)
                row[terminal] = f'{nt} → {prod}' if prod else ''
            table_data.append(row)
        steps = parser.parse_string(final_grammar, start_symbol, input_string) if input_string else []
        return render_template('ll1_parser.html', grammar=grammar_text, start_symbol=start_symbol, input_string=input_string,
            original_grammar=pd.DataFrame(original_grammar_list).to_html(classes='table table-bordered', index=False),
            left_recursion_grammar=pd.DataFrame(left_recursion_list).to_html(classes='table table-bordered', index=False),
            has_left_recursion=has_left_recursion,
            left_factoring_grammar=pd.DataFrame(left_factoring_list).to_html(classes='table table-bordered', index=False),
            has_left_factoring=has_left_factoring,
            first_table=pd.DataFrame(first_table).to_html(classes='table table-bordered', index=False),
            follow_table=pd.DataFrame(follow_table).to_html(classes='table table-bordered', index=False),
            parsing_table=pd.DataFrame(table_data).to_html(classes='table table-bordered', index=False),
            steps=pd.DataFrame(steps).to_html(classes='table table-bordered', index=False) if steps else None)
    return render_template('ll1_parser.html')

@app.route('/slr-parser', methods=['GET', 'POST'])
def slr_parser():
    if request.method == 'POST':
        grammar_text = request.form.get('grammar')
        input_string = request.form.get('input_string', '')
        result = slr_parse_with_steps(grammar_text, input_string)
        aug_grammar_rows = [{'Rule': r['rule'], 'Production': f"{r['head']} → {' '.join(r['body'])}"} for r in result['augmented_grammar_list']]
        items_list   = [{'State': f"I{s['index']}", 'Items': '<br>'.join(s['items'])} for s in result['states']]
        follow_list  = [{'Non-terminal': nt, 'FOLLOW': '{ ' + ', '.join(result['follow_sets'][nt]) + ' }'} for nt in sorted(result['follow_sets'])]
        cols         = ['state'] + result['action_terminals'] + result['goto_non_terminals']
        table_rows   = [{c: row.get(c, '') for c in cols} for row in result['table_rows']]
        renamed_rows = [{'State' if k == 'state' else k: v for k, v in row.items()} for row in table_rows]
        return render_template('slr_parser.html', grammar=grammar_text, input_string=input_string,
            aug_grammar=pd.DataFrame(aug_grammar_rows).to_html(classes='table table-bordered', index=False),
            items=pd.DataFrame(items_list).to_html(classes='table table-bordered', index=False, escape=False),
            follow_sets=pd.DataFrame(follow_list).to_html(classes='table table-bordered', index=False),
            action_table=pd.DataFrame(renamed_rows).to_html(classes='table table-bordered', index=False),
            steps=pd.DataFrame(result['parse_trace']).to_html(classes='table table-bordered', index=False) if result['parse_trace'] else None)
    return render_template('slr_parser.html')

@app.route('/three-address-code', methods=['GET', 'POST'])
def three_address_code():
    if request.method == 'POST':
        expression = request.form.get('expression')
        generator  = ThreeAddressCode()
        result     = generator.generate(expression)
        quad_table   = [{'Op': q[0], 'Arg1': q[1], 'Arg2': q[2], 'Result': q[3]} for q in result['quadruples']]
        triple_table = [{'Index': i, 'Op': t[0], 'Arg1': t[1], 'Arg2': t[2]} for i, t in enumerate(result['triples'])]
        return render_template('three_address_code.html', expression=expression,
            tac='<br>'.join(result['tac']),
            quadruples=pd.DataFrame(quad_table).to_html(classes='table table-bordered', index=False),
            triples=pd.DataFrame(triple_table).to_html(classes='table table-bordered', index=False))
    return render_template('three_address_code.html')

@app.route('/code-optimization', methods=['GET', 'POST'])
def code_optimization():
    if request.method == 'POST':
        expression = request.form.get('expression')
        result     = ThreeAddressCode().generate(expression)
        steps      = CodeOptimization().optimize(result['tac'])
        opt_steps  = [{'Optimization': s['name'], 'Code': '<br>'.join(s['code'])} for s in steps]
        return render_template('code_optimization.html', expression=expression,
            steps=pd.DataFrame(opt_steps).to_html(classes='table table-bordered', index=False, escape=False))
    return render_template('code_optimization.html')

@app.route('/code-generation', methods=['GET', 'POST'])
def code_generation():
    if request.method == 'POST':
        expression = request.form.get('expression')
        result     = ThreeAddressCode().generate(expression)
        assembly   = CodeGeneration().generate_assembly(result['tac'])
        return render_template('code_generation.html', expression=expression,
            tac='<br>'.join(result['tac']), assembly='<br>'.join(assembly))
    return render_template('code_generation.html')

@app.route('/clr-parser', methods=['GET', 'POST'])
def clr_parser():
    if request.method == 'POST':
        grammar_text = request.form.get('grammar')
        input_string = request.form.get('input_string', '')
        result       = clr_parse_with_steps(grammar_text, input_string)
        aug_grammar_rows = [{'Rule': r['Rule'], 'Production': r['Production']} for r in result['aug_grammar_list']]
        items_list   = [{'State': f"I{s['index']}", 'Items': '<br>'.join(s['item_list'])} for s in result['states']]
        cols         = ['State'] + result['action_terminals'] + result['goto_non_terminals']
        table_rows   = [{c: row.get(c, '') for c in cols} for row in result['table_rows']]
        return render_template('clr_parser.html', grammar=grammar_text, input_string=input_string,
            aug_grammar=pd.DataFrame(aug_grammar_rows).to_html(classes='table table-bordered', index=False),
            items=pd.DataFrame(items_list).to_html(classes='table table-bordered', index=False, escape=False),
            action_table=pd.DataFrame(table_rows).to_html(classes='table table-bordered', index=False),
            conflicts=result['conflicts'],
            steps=pd.DataFrame(result['parse_trace']).to_html(classes='table table-bordered', index=False) if result['parse_trace'] else None,
            accepted=result['accepted'])
    return render_template('clr_parser.html')

@app.route('/lalr-parser', methods=['GET', 'POST'])
def lalr_parser():
    if request.method == 'POST':
        grammar_text = request.form.get('grammar')
        input_string = request.form.get('input_string', '')
        result       = lalr_parse_with_steps(grammar_text, input_string)
        aug_grammar_rows = [{'Rule': r['Rule'], 'Production': r['Production']} for r in result['aug_grammar_list']]
        items_list   = [{'State': s['label'], 'Items': '<br>'.join(s['item_list'])} for s in result['states']]
        cols         = ['State'] + result['action_terminals'] + result['goto_non_terminals']
        table_rows   = [{c: row.get(c, '') for c in cols} for row in result['table_rows']]
        merged_info  = pd.DataFrame(result['merged_info']).to_html(classes='table table-bordered', index=False) if result['merged_info'] else None
        return render_template('lalr_parser.html', grammar=grammar_text, input_string=input_string,
            aug_grammar=pd.DataFrame(aug_grammar_rows).to_html(classes='table table-bordered', index=False),
            items=pd.DataFrame(items_list).to_html(classes='table table-bordered', index=False, escape=False),
            action_table=pd.DataFrame(table_rows).to_html(classes='table table-bordered', index=False),
            conflicts=result['conflicts'],
            steps=pd.DataFrame(result['parse_trace']).to_html(classes='table table-bordered', index=False) if result['parse_trace'] else None,
            accepted=result['accepted'], merged_info=merged_info,
            clr_count=result['clr_state_count'], lalr_count=result['lalr_state_count'])
    return render_template('lalr_parser.html')

@app.route('/sdd', methods=['GET', 'POST'])
def sdd():
    if request.method == 'POST':
        expression = request.form.get('expression', '').strip()
        result     = SDDEvaluator().evaluate(expression)
        return render_template('sdd.html', expression=expression,
            steps_table=pd.DataFrame(result['steps']).to_html(classes='table table-bordered', index=False) if result['steps'] else None,
            attr_table=pd.DataFrame(result['attr_table']).to_html(classes='table table-bordered', index=False) if result['attr_table'] else None,
            tree_html=result['tree_html'], final_val=result['final_val'], error=result['error'])
    return render_template('sdd.html')

@app.route('/sdt', methods=['GET', 'POST'])
def sdt():
    if request.method == 'POST':
        expression = request.form.get('expression', '').strip()
        result     = SDTTranslator().translate(expression)
        return render_template('sdt.html', expression=expression,
            steps_table=pd.DataFrame(result['steps']).to_html(classes='table table-bordered', index=False) if result['steps'] else None,
            code_lines=list(enumerate(result['code'], 1)),
            result_place=result['result_place'], tree_html=result['tree_html'],
            postfix=result['postfix'], error=result['error'])
    return render_template('sdt.html')

@app.route('/expr-translation', methods=['GET', 'POST'])
def expr_translation():
    if request.method == 'POST':
        expression = request.form.get('expression', '').strip()
        if not expression:
            return render_template('expr_translation.html')
        result = ExpressionTranslator().translate(expression)
        return render_template('expr_translation.html', expression=expression,
            steps_table=pd.DataFrame(result['steps']).to_html(classes='table table-bordered', index=False) if result['steps'] else None,
            quad_table=pd.DataFrame(result['quad_rows']).to_html(classes='table table-bordered', index=False) if result['quad_rows'] else None,
            triple_table=pd.DataFrame(result['triple_rows']).to_html(classes='table table-bordered', index=False) if result['triple_rows'] else None,
            pointer_table=pd.DataFrame(result['pointer_rows']).to_html(classes='table table-bordered', index=False) if result['pointer_rows'] else None,
            indirect_triple_table=pd.DataFrame(result['indirect_triple_rows']).to_html(classes='table table-bordered', index=False) if result['indirect_triple_rows'] else None,
            result=result['result'], error=result['error'])
    return render_template('expr_translation.html')


# ═══════════════════════════════════════════════════════════════════════════════
# REST API ROUTES (Flutter)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/register', methods=['POST'])
def api_register():
    d = request.get_json()
    if not all([d.get('firstname'), d.get('username'), d.get('email'), d.get('password')]):
        return jsonify({'success': False, 'message': 'All fields required'}), 400
    if User.query.filter_by(username=d['username']).first():
        return jsonify({'success': False, 'message': 'Username already taken'}), 409
    if User.query.filter_by(email=d['email'].lower()).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 409
    if len(d['password']) < 6:
        return jsonify({'success': False, 'message': 'Password min 6 characters'}), 400
    user = User(firstname=d['firstname'], lastname=d.get('lastname', ''),
                username=d['username'], email=d['email'].lower())
    user.set_password(d['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'message': f"Account created for {d['username']}"})

@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.get_json()
    user = User.query.filter_by(username=d.get('username', '')).first()
    if user and user.check_password(d.get('password', '')):
        return jsonify({'success': True, 'message': 'Login successful',
                        'user': {'id': user.id, 'username': user.username,
                                 'firstname': user.firstname, 'lastname': user.lastname,
                                 'email': user.email}})
    return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    d    = request.get_json()
    email = d.get('email', '').strip().lower()
    user  = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'No account found with that email'}), 404
    otp = ''.join(random.choices(string.digits, k=6))
    user.otp_code   = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    try:
        msg = Message('Password Reset OTP — Compiler Design Lab', recipients=[email])
        msg.body = (f'Hello {user.firstname},\n\n'
                    f'Your OTP is: {otp}\n\nValid for 10 minutes.')
        mail.send(msg)
        return jsonify({'success': True, 'message': f'OTP sent to {email}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Email error: {str(e)}'}), 500

@app.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    d       = request.get_json()
    email   = d.get('email', '').strip().lower()
    otp     = d.get('otp', '').strip()
    password= d.get('password', '')
    user    = User.query.filter_by(email=email).first()
    if not user or user.otp_code != otp:
        return jsonify({'success': False, 'message': 'Invalid OTP'}), 400
    if user.otp_expiry < datetime.utcnow():
        return jsonify({'success': False, 'message': 'OTP expired'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password min 6 characters'}), 400
    user.set_password(password)
    user.otp_code = None
    user.otp_expiry = None
    db.session.commit()
    return jsonify({'success': True, 'message': 'Password reset successful'})

@app.route('/api/lexical-analyzer', methods=['POST'])
def api_lexical_analyzer():
    d = request.get_json()
    analyzer = LexicalAnalyzer()
    tokens, symbol_table = analyzer.analyze(d.get('source_code', ''))
    return jsonify({'tokens': tokens,
                    'symbol_table': [{'id': v['id'], 'name': k, 'type': v['type']} for k, v in symbol_table.items()]})

@app.route('/api/ll1-parser', methods=['POST'])
def api_ll1_parser():
    d = request.get_json()
    parser = LL1Parser()
    grammar = parser.parse_grammar(d.get('grammar', ''))
    grammar = parser.left_factor(parser.remove_left_recursion(grammar))
    first_sets    = parser.compute_first(grammar)
    follow_sets   = parser.compute_follow(grammar, d.get('start_symbol', ''))
    parsing_table = parser.build_parsing_table(grammar, d.get('start_symbol', ''))
    steps = parser.parse_string(grammar, d.get('start_symbol', ''), d.get('input_string', '')) if d.get('input_string') else []
    return jsonify({'first_sets': {k: list(v) for k, v in first_sets.items()},
                    'follow_sets': {k: list(v) for k, v in follow_sets.items()},
                    'parsing_table': {k: dict(v) for k, v in parsing_table.items()}, 'steps': steps})

@app.route('/api/slr-parser', methods=['POST'])
def api_slr_parser():
    d = request.get_json()
    r = slr_parse_with_steps(d.get('grammar', ''), d.get('input_string', ''))
    return jsonify({'augmented_grammar': r['augmented_grammar_list'], 'states': r['states'],
                    'follow_sets': r['follow_sets'], 'action_terminals': r['action_terminals'],
                    'goto_non_terminals': r['goto_non_terminals'], 'table_rows': r['table_rows'],
                    'parse_trace': r['parse_trace']})

@app.route('/api/clr-parser', methods=['POST'])
def api_clr_parser():
    d = request.get_json()
    r = clr_parse_with_steps(d.get('grammar', ''), d.get('input_string', ''))
    return jsonify({'augmented_grammar': r['aug_grammar_list'], 'states': r['states'],
                    'action_terminals': r['action_terminals'], 'goto_non_terminals': r['goto_non_terminals'],
                    'table_rows': r['table_rows'], 'conflicts': r['conflicts'],
                    'parse_trace': r['parse_trace'], 'accepted': r['accepted']})

@app.route('/api/lalr-parser', methods=['POST'])
def api_lalr_parser():
    d = request.get_json()
    r = lalr_parse_with_steps(d.get('grammar', ''), d.get('input_string', ''))
    return jsonify({'augmented_grammar': r['aug_grammar_list'], 'states': r['states'],
                    'action_terminals': r['action_terminals'], 'goto_non_terminals': r['goto_non_terminals'],
                    'table_rows': r['table_rows'], 'conflicts': r['conflicts'],
                    'parse_trace': r['parse_trace'], 'accepted': r['accepted'],
                    'merged_info': r['merged_info'], 'clr_state_count': r['clr_state_count'],
                    'lalr_state_count': r['lalr_state_count']})

@app.route('/api/three-address-code', methods=['POST'])
def api_three_address_code():
    d = request.get_json()
    r = ThreeAddressCode().generate(d.get('expression', ''))
    return jsonify({'tac': r['tac'],
                    'quadruples': [{'op': q[0], 'arg1': q[1], 'arg2': q[2], 'result': q[3]} for q in r['quadruples']],
                    'triples':    [{'index': i, 'op': t[0], 'arg1': t[1], 'arg2': t[2]} for i, t in enumerate(r['triples'])]})

@app.route('/api/code-optimization', methods=['POST'])
def api_code_optimization():
    d = request.get_json()
    r = ThreeAddressCode().generate(d.get('expression', ''))
    s = CodeOptimization().optimize(r['tac'])
    return jsonify({'steps': [{'name': x['name'], 'code': x['code']} for x in s]})

@app.route('/api/code-generation', methods=['POST'])
def api_code_generation():
    d = request.get_json()
    r = ThreeAddressCode().generate(d.get('expression', ''))
    return jsonify({'tac': r['tac'], 'assembly': CodeGeneration().generate_assembly(r['tac'])})

@app.route('/api/regex-to-nfa', methods=['POST'])
def api_regex_to_nfa():
    d = request.get_json()
    c = RegexToNFA(); nfa, postfix = c.construct_nfa(d.get('regex', ''))
    svg = None
    try: svg = c.visualize_nfa(nfa).pipe(format='svg').decode('utf-8')
    except: pass
    return jsonify({'postfix': postfix, 'table': c.create_transition_table(nfa),
                    'start': f'q{nfa["start"]}', 'end': f'q{nfa["end"]}', 'diagram': svg})

@app.route('/api/nfa-to-dfa', methods=['POST'])
def api_nfa_to_dfa():
    d = request.get_json()
    c = RegexToNFA(); nfa, postfix = c.construct_nfa(d.get('regex', ''))
    dc = NFAToDFA(); dfa = dc.convert(nfa)
    closures = [{'States': '{' + ', '.join([f'q{s}' for s in sorted(st)]) + '}',
                 'e-closure': '{' + ', '.join([f'q{s}' for s in sorted(cl)]) + '}'}
                for st, cl in dfa['epsilon_closures'].items() if st != cl]
    svg = None
    try: svg = dc.visualize_dfa(dfa).pipe(format='svg').decode('utf-8')
    except: pass
    return jsonify({'postfix': postfix, 'table': dc.create_transition_table(dfa),
                    'epsilon_closures': closures, 'diagram': svg})

@app.route('/api/direct-dfa', methods=['POST'])
def api_direct_dfa():
    d = request.get_json()
    c = DirectDFA(); result = c.construct_dfa(d.get('regex', ''))
    if not result['tree']:
        return jsonify({'error': 'Invalid regular expression'}), 400
    fp_table = [{'Position': pos, 'Symbol': result['pos_symbols'][pos],
                 'followpos': '{' + ', '.join(map(str, sorted(result['followpos'][pos]))) + '}'}
                for pos in sorted(result['followpos']) if pos in result['pos_symbols']]
    dfa_table = []
    for state in result['states']:
        row = {'State': 'S' + str(result['state_map'][frozenset(state)]),
               'Positions': '{' + ', '.join(map(str, sorted(state))) + '}'}
        for sym in result['symbols']:
            ns = result['transitions'].get(frozenset(state), {}).get(sym)
            row[sym] = 'S' + str(result['state_map'][ns]) if ns else '-'
        dfa_table.append(row)
    tree_svg = dfa_svg = None
    try: tree_svg = c.visualize_tree(result['tree']).pipe(format='svg').decode('utf-8')
    except: pass
    try: dfa_svg = c.visualize_dfa(result).pipe(format='svg').decode('utf-8') if result['states'] else None
    except: pass
    return jsonify({'followpos_table': fp_table, 'dfa_table': dfa_table,
                    'symbols': result['symbols'], 'tree_diagram': tree_svg, 'dfa_diagram': dfa_svg})

@app.route('/api/dfa-minimization', methods=['POST'])
def api_dfa_minimization():
    try:
        d = request.get_json()
        c = RegexToNFA(); nfa, _ = c.construct_nfa(d.get('regex', ''))
        dc = NFAToDFA(); dfa = dc.convert(nfa)
        m = DFAMinimization(); min_dfa = m.minimize(dfa)
        partition_steps = [{'Step': i, 'Partitions': ' | '.join(
            ['{' + ', '.join([f'D{dfa["state_map"][s]}' for s in sorted(g, key=lambda x: dfa["state_map"][x])]) + '}'
             for g in partition])}
            for i, partition in enumerate(min_dfa['partition_history'])]
        min_table = [dict({'State': f'S{st}', 'Is Final': 'Yes' if st in min_dfa['final'] else 'No'},
                          **{sym: (f'S{min_dfa["transitions"].get(st, {}).get(sym)}' if min_dfa['transitions'].get(st, {}).get(sym) is not None else '-')
                             for sym in min_dfa['symbols']})
                     for st in min_dfa['states']]
        svg = None
        try: svg = m.visualize_minimized_dfa(min_dfa).pipe(format='svg').decode('utf-8')
        except: pass
        return jsonify({'partition_steps': partition_steps, 'min_table': min_table, 'diagram': svg,
                        'start': f'S{min_dfa["start"]}', 'final_states': [f'S{s}' for s in min_dfa['final']]})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/sdd', methods=['POST'])
def api_sdd():
    d = request.get_json()
    r = SDDEvaluator().evaluate(d.get('expression', ''))
    return jsonify({'steps': r['steps'], 'attr_table': r['attr_table'], 'final_val': r['final_val'], 'error': r['error']})

@app.route('/api/sdt', methods=['POST'])
def api_sdt():
    d = request.get_json()
    r = SDTTranslator().translate(d.get('expression', ''))
    return jsonify({'steps': r['steps'], 'code': r['code'], 'postfix': r['postfix'], 'error': r['error']})

@app.route('/api/expr-translation', methods=['POST'])
def api_expr_translation():
    d = request.get_json()
    r = ExpressionTranslator().translate(d.get('expression', ''))
    return jsonify({'steps': r['steps'], 'quad_rows': r['quad_rows'], 'triple_rows': r['triple_rows'],
                    'pointer_rows': r['pointer_rows'], 'indirect_triple_rows': r['indirect_triple_rows'],
                    'result': r['result'], 'error': r['error']})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
