import os
import hashlib

from collections import namedtuple 

UGIT_DIR = ".ugit"

RefValue = namedtuple("RefValue", ["symbolic", "value"])

def init():
    os.mkdir(UGIT_DIR)
    os.makedirs(f'{UGIT_DIR}/objects')

def update_ref(ref, value, deref=True):
    ref = _get_ref_internal(ref, deref)[0]

    assert value.value
    if value.symbolic:
        value = f"ref: {value.value}"
    else:
        value = value.value

    ref_path = f"{UGIT_DIR}/{ref}"
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open (ref_path, 'w') as f:
        f.write (value)

def get_ref(ref, deref=True):
    return _get_ref_internal(ref, deref)[1]

def _get_ref_internal(ref, deref):
    ref_path = f"{UGIT_DIR}/{ref}"
    value = None
    if os.path.isfile(ref_path):
        with open (ref_path) as f:
            value = f.read ().strip ()

    symbolic = bool(value) and value.startswith("ref:")
    if symbolic:
        value = value.split(":", 1)[1].strip()
        if deref:
            return _get_ref_internal(value, deref=True)
    
    return ref, RefValue(symbolic=symbolic, value=value)

def iter_refs(prefix="",deref=True):
    refs = ["HEAD"]
    for root, _, filename in os.walk(f"{UGIT_DIR}/refs/"):
        root = os.path.relpath(root, UGIT_DIR).replace('\\', '/')
        refs.extend(f"{root}/{name}" for name in filename)

    for refname in refs:
        if not refname.startswith(prefix):
            continue
        yield refname, get_ref(refname, deref=deref)

def hash_object(data, type_= "blob"):
    obj = type_.encode() + b"\x00" + data
    oid = hashlib.sha1(obj).hexdigest() # oid - Object ID
    with open(f'{UGIT_DIR}/objects/{oid}', 'wb') as out:
        out.write(obj)
    return oid

def get_object(oid, expected="blob"):
    with open(f"{UGIT_DIR}/objects/{oid}", "rb") as f:
        obj = f.read()

    type_, _, content = obj.partition(b"\x00") # b"\x00" means a null byte represented by binary/bytes literal
    type_ = type_.decode()

    if expected is not None:
        assert type_ == expected, f"Expected {expected}, got {type_}"
    return content

