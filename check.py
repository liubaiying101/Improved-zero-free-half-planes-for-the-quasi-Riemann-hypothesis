#!/usr/bin/env python3
"""Strict replay of eight merged OAI files and two manuscript proof files."""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, tarfile, tempfile

HERE = Path(__file__).resolve().parent
ALLOWED_AXIOMS = {'propext', 'Classical.choice', 'Quot.sound'}
FLAGS = ['--trust=0', '-DautoImplicit=false', '-DwarningAsError=true', '-DmaxHeartbeats=0']
REPLAY_ORDER = [f'OAI{i:02d}' for i in range(1, 9)]+['PartsI_III', 'PartIV']


SIGNATURE_AUDIT_SOURCE = """import PartIV

/- Independent final signatures against the explicitly named external L-functions.
   This audit is generated in the replay directory, never an uploaded proof input. -/
namespace CombineV22SignatureAudit
noncomputable section
abbrev explicitBoundary : ℝ :=
  (18*CombineV22Optimality.xiInf+7)/(18*CombineV22Optimality.xiInf+9)

theorem boundary_formula : CombineV22.limitingBoundary = explicitBoundary := rfl

theorem root_equation :
    1188*CombineV22Optimality.xiInf^3-2160*CombineV22Optimality.xiInf^2+
      171*CombineV22Optimality.xiInf+190=0 :=
  CombineV22Optimality.cubic_xiInf

theorem root_explicit : CombineV22Optimality.xiInf =
    20/33+_root_.Real.sqrt 1391/33 *
      _root_.Real.cos (_root_.Real.arccos (28470/(1391*_root_.Real.sqrt 1391))/3-
        2*_root_.Real.pi/3) := CombineV22ExplicitRoot.xiInf_explicit

theorem boundary_bracket :
    (874957019420098946/10^18 : ℝ)< explicitBoundary ∧
    explicitBoundary<(874957019420098947/10^18 : ℝ) :=
  CombineV22ExplicitRoot.boundary_decimal_bracket

theorem hecke_signature
    (chi : OAI.SevenEighths.HeckeFamily.Character) (s : ℂ)
    (hs : explicitBoundary< s.re) (hpole : s≠1 ∨ chi.residue≠1) :
    OAI.SevenEighths.HeckeFamily.LFunction chi s≠0 :=
  CombineV22.hecke_nonzero chi s hs hpole

theorem dirichlet_signature (q : ℕ) [NeZero q]
    (chi : _root_.DirichletCharacter ℂ q) (s : ℂ)
    (hs : explicitBoundary< s.re) (hpole : ¬(chi=1 ∧ s=1)) :
    _root_.DirichletCharacter.LFunction chi s≠0 :=
  CombineV22.dirichlet_nonzero q chi s hs hpole

theorem zeta_signature (s : ℂ)
    (hs : explicitBoundary< s.re) (hpole : s≠1) :
    _root_.riemannZeta s≠0 := CombineV22.zeta_nonzero s hs hpole

#print axioms boundary_formula
#print axioms root_equation
#print axioms root_explicit
#print axioms boundary_bracket
#print axioms hecke_signature
#print axioms dirichlet_signature
#print axioms zeta_signature
end
end CombineV22SignatureAudit
"""
SIGNATURE_AUDIT_THEOREMS = ['CombineV22SignatureAudit.boundary_formula', 'CombineV22SignatureAudit.root_equation', 'CombineV22SignatureAudit.root_explicit', 'CombineV22SignatureAudit.boundary_bracket', 'CombineV22SignatureAudit.hecke_signature', 'CombineV22SignatureAudit.dirichlet_signature', 'CombineV22SignatureAudit.zeta_signature']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args, cwd, log=None, env=None):
    shown = list(map(str,args))
    print('+', ' '.join(shown if len(shown)<15 else shown[:5]+['... ('+str(len(shown)-5)+' more arguments)']), flush=True)
    if log is None:
        subprocess.run(args, cwd=cwd, env=env, check=True)
    else:
        with open(log, 'w') as stream:
            subprocess.run(args, cwd=cwd, env=env, stdout=stream,
                           stderr=subprocess.STDOUT, check=True)


def output(args, cwd, env=None):
    return subprocess.check_output(args, cwd=cwd, env=env, text=True).strip()


def within(path, roots):
    path = Path(path).resolve()
    return any(path == root or root in path.parents for root in roots)


def source_imports(code):
    """Read import commands after comments and strings have been removed."""
    return [module for line in re.findall(
        r'^\s*(?:(?:public|private|meta)\s+)*import\s+([^\n]+)', code, re.M)
        for module in line.split()]


def isolated_lean(foundation, dependencies, stage):
    """Reuse external packages only; exclude all original project artifacts."""
    prefix = Path(output(['lake', 'env', 'lean', '--print-prefix'], foundation)).resolve()
    lean = prefix/'bin'/('lean.exe' if os.name == 'nt' else 'lean')
    core = (prefix/'lib'/'lean').resolve()
    packages = [(foundation/dependencies['packagesDir']/p['name'].strip('«»')).resolve()
                for p in dependencies['packages']]
    raw = output(['lake', 'env', 'printenv', 'LEAN_PATH'], foundation)
    paths = []
    for entry in raw.split(os.pathsep):
        if not entry:
            continue
        path = Path(entry)
        if not path.is_absolute():
            path = foundation/path
        path = path.resolve()
        if within(path, packages+[core]) and path not in paths:
            paths.append(path)
    if core not in paths:
        paths.append(core)
    env = os.environ.copy()
    env.pop('LEAN_SRC_PATH', None)
    env['LEAN_PATH'] = os.pathsep.join(map(str, [stage]+paths))
    return lean, env, packages+[core]


def audit_dependencies(lean, source, foundation, stage, roots, compiled, env):
    raw = output([str(lean), '-R', str(stage), '--deps', str(source)], foundation, env)
    accepted = []
    for line in raw.splitlines():
        path = Path(line.strip())
        if not path.is_absolute():
            path = foundation/path
        path = path.resolve()
        if 'OAI' in path.parts or path.suffix != '.olean' or not path.is_file():
            raise RuntimeError('Unacceptable dependency artifact: '+str(path))
        if within(path, [stage]):
            if path not in {(stage/(m+'.olean')).resolve() for m in compiled}:
                raise RuntimeError('Dependency was not freshly replayed: '+str(path))
        elif not within(path, roots):
            raise RuntimeError('Dependency outside pinned packages/toolchain: '+str(path))
        accepted.append(str(path))
    return accepted


def prepare_packages(foundation, manifest):
    """Fetch exact manifest revisions; never ask Lake to resolve new versions."""
    for p in manifest['packages']:
        if p['type'] != 'git' or p.get('subDir'):
            raise RuntimeError('Unsupported dependency layout: '+p['name'])
        checkout = foundation/manifest['packagesDir']/p['name'].strip('«»')
        if not (checkout/'.git').exists():
            if checkout.exists() and any(checkout.iterdir()):
                raise RuntimeError('Nonempty dependency path: '+str(checkout))
            checkout.mkdir(parents=True, exist_ok=True)
            run(['git', 'init', '--quiet'], checkout)
            run(['git', 'remote', 'add', 'origin', p['url']], checkout)
            run(['git', 'fetch', '--quiet', '--depth=1', 'origin', p['rev']], checkout)
            run(['git', 'checkout', '--quiet', '--detach', 'FETCH_HEAD'], checkout)
        if output(['git', 'rev-parse', 'HEAD'], checkout) != p['rev']:
            raise RuntimeError('Existing dependency has wrong revision: '+p['name'])
    for name in ['PrimeNumberTheoremAnd', 'rellich-kondrachov']:
        checkout = foundation/manifest['packagesDir']/name
        patch = foundation/'upstream'/(name+'-lean4341.patch')
        reverse = subprocess.run(['git', 'apply', '--check', '--reverse', str(patch)],
                                 cwd=checkout, capture_output=True)
        if reverse.returncode:
            run(['git', 'apply', '--check', str(patch)], checkout)
            run(['git', 'apply', str(patch)], checkout)


def validate_packages(foundation, manifest, expected_changes):
    for p in manifest['packages']:
        if p['type'] != 'git':
            raise RuntimeError('Unpinned dependency: '+p['name'])
        name = p['name'].strip('«»')
        checkout = foundation/manifest['packagesDir']/name
        actual = output(['git', 'rev-parse', 'HEAD'], checkout)
        if actual != p['rev']:
            raise RuntimeError('Wrong dependency revision: '+name)
        changed = output(['git', 'diff', '--name-only', 'HEAD'], checkout).splitlines()
        allowed = expected_changes.get(name, {})
        if set(changed) != set(allowed):
            raise RuntimeError('Unexpected tracked dependency changes: '+name)
        for file, sha in allowed.items():
            if digest(checkout/file) != sha:
                raise RuntimeError('Compatibility patch source differs: '+name+'/'+file)


def axiom_reports(log):
    text = log.read_text()
    if re.search(r'error:|sorryAx|declaration uses .sorry.', text):
        raise RuntimeError('Rejected Lean diagnostics: '+str(log))
    result = {name: [] for name in re.findall(
        r"'([^']+)' does not depend on any axioms", text)}
    for theorem, raw in re.findall(r"'([^']+)' depends on axioms:\s*\[([^]]*)\]", text, re.S):
        axioms = {x.strip() for x in raw.split(',') if x.strip()}
        if not axioms <= ALLOWED_AXIOMS:
            raise RuntimeError('Unexpected axioms for '+theorem+': '+repr(axioms))
        result[theorem] = sorted(axioms)
    return result


def strip_comments_and_strings(source):
    out=[];i=0;depth=0;quoted=False;escaped=False
    while i<len(source):
        pair=source[i:i+2];char=source[i]
        if depth:
            if pair=='/-':depth+=1;i+=2;continue
            if pair=='-/':depth-=1;i+=2;continue
            out.append('\n' if char=='\n' else ' ')
        elif quoted:
            out.append('\n' if char=='\n' else ' ')
            if escaped:escaped=False
            elif char=='\\':escaped=True
            elif char=='"':quoted=False
        elif pair=='/-':depth=1;i+=2;continue
        elif pair=='--':
            end=source.find('\n',i)
            if end<0:break
            i=end;continue
        else:
            if char=='"':quoted=True;out.append(' ')
            else:out.append(char)
        i+=1
    if depth:raise RuntimeError('Unterminated Lean comment')
    return ''.join(out)


def replay_signature_audit(lean, foundation, stage, logs, roots, compiled, env):
    """Kernel-check final signatures against explicitly qualified external functions."""
    source = stage/'FinalSignatureAudit.lean'
    source.write_text(SIGNATURE_AUDIT_SOURCE)
    imported = audit_dependencies(lean, source, foundation, stage, roots, compiled, env)
    log = logs/'FinalSignatureAudit.log'
    run([str(lean), '-R', str(stage), *FLAGS,
         '-o', str(stage/'FinalSignatureAudit.olean'), str(source)], foundation, log, env)
    reports = axiom_reports(log)
    for theorem in SIGNATURE_AUDIT_THEOREMS:
        if theorem not in reports:
            raise RuntimeError('Missing final signature axiom report: '+theorem)
    return {'status':'PASS',
            'scope':'Strict kernel replay of the explicit cubic root, boundary formula and decimal bracket, and Hecke, Dirichlet and root-namespace Riemann-zeta nonvanishing signatures.',
            'source_sha256':digest(source), 'source':str(source),
            'imported_artifacts':imported, 'axioms':reports}, reports


def main():
    # Disallow ambient search-path overrides in both build modes.
    os.environ.pop('LEAN_PATH', None)
    os.environ.pop('LEAN_SRC_PATH', None)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--foundation', type=Path,
                        help='Reuse pinned external packages from an existing checkout; no Git fetch.')
    parser.add_argument('--build-dir', type=Path,
                        help='Directory for extracted dependencies, oleans, logs and result.json.')
    args = parser.parse_args()
    archive = HERE/'foundations.tar.gz'
    if not archive.exists():
        raise SystemExit('Release assembly is not complete: foundations.tar.gz is missing.')
    with tarfile.open(archive) as tar:
        manifest = json.load(tar.extractfile('proof_manifest.json'))
    replay_order = manifest.get('replay_order', REPLAY_ORDER)
    if replay_order != REPLAY_ORDER or set(manifest['main_sources']) != {
            module+'.lean' for module in replay_order}:
        raise RuntimeError('Expected eight merged OAI sources and two manuscript sources.')
    manuscript = HERE.parent/'combine_v2-2.tex'
    if manuscript.exists() and digest(manuscript) != manifest['manuscript_sha256']:
        raise RuntimeError('Manuscript differs from the release verification target.')
    previous = set()
    for module in replay_order:
        name = module+'.lean'
        sha = manifest['main_sources'][name]
        if digest(HERE/name) != sha:
            raise RuntimeError('Main source differs from release manifest: '+name)
        code=strip_comments_and_strings((HERE/name).read_text())
        if re.search(r'\b(?:sorry|admit|sorryAx|native_decide)\b|^\s*(?:private\s+)?axiom\s',code,re.M):
            raise RuntimeError('Unproved or extra-trust declaration in '+name)
        for imported in source_imports(code):
            if imported == 'OAI' or imported.startswith('OAI.'):
                raise RuntimeError('Original unmerged OAI import in '+name+': '+imported)
            if imported not in previous and imported not in manifest['external_imports']:
                raise RuntimeError('Unrecorded or out-of-order import in '+name+': '+imported)
        previous.add(module)
    build = (args.build_dir or Path(tempfile.gettempdir())/
             ('combine-v2-2-lean-'+digest(archive)[:16])).resolve()
    if build == HERE or HERE in build.parents:
        raise RuntimeError('Keep generated output outside the upload folder.')
    build.mkdir(parents=True, exist_ok=True)
    logs = build/'replay-logs'; logs.mkdir(exist_ok=True)
    result_path = build/'result.json'
    if result_path.exists():
        result_path.unlink()
    extracted = build/'foundation'; extracted.mkdir(exist_ok=True)
    with tarfile.open(archive) as tar:
        for item in tar.getmembers():
            target = (extracted/item.name).resolve()
            if not item.isfile() or extracted not in target.parents:
                raise RuntimeError('Unsafe archive member: '+item.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            data = tar.extractfile(item).read()
            if not target.exists() or target.read_bytes() != data:
                target.write_bytes(data)
    for name, sha in manifest['foundation_sources'].items():
        if digest(extracted/name) != sha:
            raise RuntimeError('Foundation archive mismatch: '+name)
    foundation = args.foundation.resolve() if args.foundation else extracted
    dependencies = json.loads((extracted/'lake-manifest.json').read_text())
    if args.foundation:
        for name, sha in manifest['reuse_foundation_configuration'].items():
            if digest(foundation/name) != sha:
                raise RuntimeError('Reused foundation configuration differs: '+name)
        for name, sha in manifest['foundation_sources'].items():
            if name == 'lean-toolchain':
                if digest(foundation/name) != sha:
                    raise RuntimeError('Existing foundation differs: '+name)
    else:
        prepare_packages(foundation, dependencies)
        validate_packages(foundation, dependencies, manifest['package_patch_sources'])
        targets = [m for m in manifest['external_imports']
                   if m.split('.')[0] not in {'Init','Lean','Std','Lake'}]
        if any(m == 'OAI' or m.startswith('OAI.') for m in targets):
            raise RuntimeError('Original OAI module listed as an external dependency.')
        if targets:
            run(['lake', 'build', *targets], foundation, logs/'external-build.log')
    validate_packages(foundation, dependencies, manifest['package_patch_sources'])
    # A fresh stage contains neither old proof artifacts nor original OAI modules.
    stage = Path(tempfile.mkdtemp(prefix='proofs-', dir=build)).resolve()
    lean, env, dependency_roots = isolated_lean(foundation, dependencies, stage)
    version = output([str(lean), '--version'], foundation, env)
    wanted = (extracted/'lean-toolchain').read_text().strip().rsplit(':v', 1)[-1]
    found = re.search(r'Lean \(version ([^,\s]+)', version)
    if not found or found.group(1) != wanted:
        raise RuntimeError('Executed Lean version differs from the pin: '+version)
    reports = {}
    imported_artifacts = {}
    compiled = []
    for module in replay_order:
        source = stage/(module+'.lean')
        shutil.copyfile(HERE/source.name, source)
        log = logs/(module+'.log')
        imported_artifacts[module] = audit_dependencies(
            lean, source, foundation, stage, dependency_roots, compiled, env)
        (logs/(module+'-dependencies.json')).write_text(
            json.dumps(imported_artifacts[module], indent=2)+'\n')
        run([str(lean), '-R', str(stage), *FLAGS,
             '-o', str(stage/(module+'.olean')), str(source)], foundation, log, env)
        reports.update(axiom_reports(log))
        if digest(source) != manifest['main_sources'][source.name]:
            raise RuntimeError('Staged source changed during replay: '+source.name)
        compiled.append(module)
    signature_audit, signature_reports = replay_signature_audit(
        lean, foundation, stage, logs, dependency_roots, compiled, env)
    reports.update(signature_reports)
    for theorem in manifest['expected_theorems']:
        if theorem not in reports:
            raise RuntimeError('Missing required axiom report: '+theorem)
    validate_packages(foundation, dependencies, manifest['package_patch_sources'])
    for name, sha in manifest['main_sources'].items():
        if digest(HERE/name) != sha:
            raise RuntimeError('Source changed during replay: '+name)
    result = {'status':'PASS', 'scope':manifest['verification_scope'],
              'strict_flags':FLAGS, 'lean_version':version,
              'foundation_mode':'existing pinned external packages' if args.foundation else 'archived configuration with external package build',
              'dependency_artifact_policy':'External package artifacts may be reused; all eight merged OAI sources and both manuscript sources are freshly replayed with trust=0; original OAI module caches are excluded',
              'replay_order':replay_order, 'proof_stage':str(stage),
              'final_signature_audit':signature_audit,
              'lean_search_path':env['LEAN_PATH'], 'imported_artifacts':imported_artifacts,
              'shared_package_directory':(foundation/dependencies['packagesDir']).is_symlink(),
              'archive_sha256':digest(archive), 'checker_sha256':digest(HERE/'check.py'),
              'main_source_sha256':manifest['main_sources'],
              'manuscript_sha256':manifest['manuscript_sha256'],
              'axioms':reports, 'logs':str(logs)}
    result_path.write_text(json.dumps(result, indent=2)+'\n')
    print('PASS. Replay evidence:', result_path, flush=True)


if __name__ == '__main__':
    main()
