#!/usr/bin/env python3
import os
import shutil
import argparse
import plistlib
import subprocess
from uuid import uuid4
from hashlib import sha256
from zipfile import ZipFile
from tempfile import TemporaryDirectory

parser = argparse.ArgumentParser(
    description="a cli tool to duplicate ios apps")
parser.add_argument("-i", metavar="input", required=True,
    help="ipa to duplicate")
parser.add_argument("-o", metavar="output", required=True,
    help="duplicated ipa to create")

# bundle id will be changed to `fyi.zxcvbn.appdupe.<BUNDLE>`
# <BUNDLE> will be derived from seed if specified, otherwise random
parser.add_argument("-s", metavar="seed",
    help="a \"seed\" to derive the app id from "
    "(any string of your choosing -- will always produce same output)")

args = parser.parse_args()

# thanks pyzule for source
if os.path.exists(args.o):
    overwrite = (input(f"[<] {args.o} already exists. overwrite? [Y/n] ")
                 .lower().strip())
    if overwrite in ("y", "yes", ""):
        del overwrite
    else:
        print("[>] quitting.")
        quit()

# no ipa checks this time. maybe use the tool correctly? :D
if args.s is None:
    args.s = str(uuid4())

# team identifiers are 10 chars, A-Z, and 0-9
HASHED_STR = sha256(args.s.encode()).hexdigest().upper()
TEAM_ID = HASHED_STR[-10:]

# bundle will be random every time, shared teamid will allow
# apps to communicate with each other (e.g. youtube, ytmusic, google docs)
BUNDLE = f"fyi.zxcvbn.appdupe.{uuid4().hex[:10]}"
BUNDLE_TI = f"fyi.zxcvbn.appdupe.{TEAM_ID}"

print(f"[*] using seed: \"{args.s}\"")
print(f"[*] will use team id: {TEAM_ID}")
print(f"[*] will use bundle id: {BUNDLE}")

# objectives (what we are setting):
# 1. application-identifier = "<TEAM_ID>.<BUNDLE>" (unique)
# 2. com.apple.developer.team-identifier = <TEAM_ID> (shared)
# 3. com.apple.security.application-groups = ["group.<BUNDLE_TI>"] (s)
# 4. keychain-access-groups = [BUNDLE_TI] (s)

with TemporaryDirectory() as tmpdir:
    with ZipFile(args.i) as zf:
        # step 1: get executable name
        for name in zf.namelist():
            if name.endswith(".app/Info.plist"):
                APP_NAME = name.split("/")[1]
                PLIST_PATH = name
                break
        else:
            exit("[!] unable to find Info.plist")

        with zf.open(PLIST_PATH) as pl:
            plist = plistlib.load(pl)
            EXEC_NAME = plist["CFBundleExecutable"]
            EXEC_PATH = f"{tmpdir}/{EXEC_NAME}"
            EXEC_IPATH = f"Payload/{APP_NAME}/{EXEC_NAME}"
            ENT_PATH = f"{tmpdir}/ent"
        
        # step 2: extract executable
        with zf.open(EXEC_IPATH) as r, \
                open(EXEC_PATH, "wb") as w:
            w.write(r.read())  # write to specific file, avoids Payload/*
    
    # step 3: obtain file entitlements
    ENT_PROC = subprocess.run(["ldid", "-e", EXEC_PATH], capture_output=True)
    try:
        ENT_PROC.check_returncode()
    except subprocess.CalledProcessError as err:
        exit(f"[!] error checking entitlements:\n{err.output.decode()}")
    entitlements = plistlib.loads(ENT_PROC.stdout)
    
    # step 4: modify everything lol
    plist["CFBundleIdentifier"] = BUNDLE
    entitlements["application-identifier"] = f"{TEAM_ID}.{BUNDLE}"
    entitlements["com.apple.developer.team-identifier"] = TEAM_ID
    entitlements["keychain-access-groups"] = [BUNDLE_TI]
    entitlements["com.apple.security.application-groups"] = [
        f"group.{BUNDLE_TI}"]
    
    # step 5: write entitlements back to executable
    with open(ENT_PATH, "wb") as f:
        plistlib.dump(entitlements, f)
    
    try:
        subprocess.run(
            ["ldid", f"-S{ENT_PATH}", EXEC_PATH],
            check=True, capture_output=True)
    except subprocess.CalledProcessError as err:
        exit(f"[!] error signing:\n{err.output.decode()}")

    # step 6: copy input to `<tmpdir>/<output.basename>`
    #         and replace executable
    OUTPUT = f"{tmpdir}/{os.path.basename(args.i)}"
    shutil.copyfile(args.i, OUTPUT)

    ## thanks quin:
    ## https://github.com/asdfzxcvbn/quin/blob/2487c2ab43b89a04401c25b5f542b9d305b154c0/quin.py#L72
    for key in (EXEC_IPATH, PLIST_PATH):
        subprocess.run(
            ["zip", "-d", OUTPUT, key], stdout=subprocess.DEVNULL)

    with ZipFile(OUTPUT, "a") as zf:
        zf.write(EXEC_PATH, EXEC_IPATH)
        with zf.open(PLIST_PATH, "w") as f:
            plistlib.dump(plist, f)
    
    shutil.move(OUTPUT, args.o)

print("[*] done, remember to remove app extensions (if u wanna)")
