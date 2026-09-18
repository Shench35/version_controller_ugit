import argparse
import os
import sys
import subprocess
import textwrap

from ugit import data
from ugit import base

def main():
    args = parse_args()
    args.func(args)

def parse_args():
    parser = argparse.ArgumentParser()

    commands = parser.add_subparsers(dest="command")
    commands.required = True

    oid = base.get_oid

    init_parser = commands.add_parser("init")
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser("hash-object")
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument("file")

    cat_file_parser = commands.add_parser("cat-file")
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument("object", type=oid)

    write_tree_parser = commands.add_parser("write-tree")
    write_tree_parser.set_defaults(func=write_tree)

    read_tree_parser = commands.add_parser("read-tree")
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument("tree", type=oid)

    commit_parser = commands.add_parser("commit")
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument("-m", "--message", required=True)

    log_parser = commands.add_parser("log")
    log_parser.set_defaults(func=log)
    log_parser.add_argument("oid", default="@", type=oid, nargs="?")

    checkout_parser = commands.add_parser("checkout")
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument("commit")

    create_tag_parser = commands.add_parser("tag")
    create_tag_parser.set_defaults(func=create_tag)
    create_tag_parser.add_argument("name")
    create_tag_parser.add_argument("oid", default="@", type=oid, nargs="?")

    k_parser = commands.add_parser("k")
    k_parser.set_defaults(func=k)

    branch_parser = commands.add_parser("branch")
    branch_parser.set_defaults(func=branch)
    branch_parser.add_argument("name")
    branch_parser.add_argument("start_point", default="@", type=oid, nargs="?")

    status_parser = commands.add_parser("status")
    status_parser.set_defaults(func=status)

    return parser.parse_args()

def init(args):
    base.init()
    print(f'Initialized empty ugit repository in {os.getcwd()}/{data.UGIT_DIR}')

def hash_object(args):
    with open(args.file, "rb") as f:
        print(data.hash_object(f.read()))

def cat_file(args):
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected=None))

def write_tree(args):
    print(base.write_tree())

def read_tree(args):
    base.read_tree(args.tree)

def commit(args):
    print(base.commit(args.message))

def log(args):
        for oid in base.iter_commits_parents([args.oid]):
            commit = base.get_commit(oid)

            print(f"commit {oid}\n")
            print(textwrap.indent(commit.message, "    "))
            print(" ")

def checkout(args):
    base.checkout(args.commit)

def create_tag(args):
    base.create_tag(args.name, args.oid)

def branch(args):
    base.create_branch(args.name, args.start_point)
    print(f"Branch {args.name} created at {args.start_point[:10]}")

def k(args):
    dot = "digraph commits {\n"
    oids = set()
    for refname, ref in data.iter_refs(deref=False):
        dot += f'"{refname}" [shape=note]\n'
        dot += f'"{refname}" -> "{ref.value}"\n'
        if not ref.symbolic:
            oids.add(ref.value)

    for oid in base.iter_commits_parents(oids):
        commit = base.get_commit(oid)
        dot += f'"{oid}" [shape=box style=filled label="{oid[:10]}"]\n'
        if commit.parent:
            dot += f'"{oid}" -> "{commit.parent}"\n'

    dot += '}'
    print(dot)

    with subprocess.Popen(
        [r'C:\Program Files\Graphviz\bin\dot.exe', '-Tpng', '-o', 'graph.png'],
        stdin=subprocess.PIPE
        ) as proc:
        proc.communicate(dot.encode())

        os.startfile('graph.png')

#------------------- ALTERNATIVE FOR "ugit k" -----------------------------------

# def k(args):
#     # 1. Group all the references (tags, branches, HEAD) by the commit they point to
#     refs_by_oid = {}
#     for refname, ref in data.iter_refs():
#         refs_by_oid.setdefault(ref, []).append(refname)
        
#     oids = set(refs_by_oid.keys())
    
#     # 2. Print the tree visually in the terminal
#     print("\n--- Commit Tree ---")
    
#     for oid in base.iter_commits_parents(oids):
#         commit = base.get_commit(oid)
        
#         # Gather any tags/branches pointing to this specific commit
#         refs = refs_by_oid.get(oid, [])
#         ref_str = f" \033[33m({', '.join(refs)})\033[0m" if refs else ""
        
#         # Print the commit node
#         print(f"* \033[31m{oid[:10]}\033[0m{ref_str}")
        
#         # Print the line down to the parent
#         if commit.parent:
#             print("  |")

def status(args):
    HEAD = base.get_oid("@")
    branch = base.get_branch_name()
    if branch:
        print(f"On branch {branch}")
    else:
        print(f"HEAD detached at {HEAD[:10]}")
        