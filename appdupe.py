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
# <BUNDLE> will be always be random, only teamid is derived from seed
parser.add_argument("-s", metavar="seed",
    help="a \"seed\" to derive the app id from "
    "(any string of your choosing)")

parser.add_argument("-b", metavar="id", help="bundle id to use (see README)")

args = parser.parse_args()

# thanks pyzule for source
if not args.o.endswith(".ipa"):
    print("[?] ipa file extension not detected, appending manually")
    args.o += ".ipa"
if os.path.exists(args.o):
    overwrite = (input(f"[<] {args.o} already exists. overwrite? [Y/n] ")
                 .lower().strip())
    if overwrite in ("y", "yes", ""):
        del overwrite
    else:
        quit("[>] quitting.")

# no ipa checks this time. maybe use the tool correctly? :D
if args.s is None:
    args.s = str(uuid4())

# team identifiers are 10 chars, A-Z, and 0-9
HASHED_STR = sha256(args.s.encode()).hexdigest().upper()
TEAM_ID = HASHED_STR[-10:]
BUNDLE_TI = f"fyi.zxcvbn.appdupe.{TEAM_ID}"

# bundle will be random every time (unless specified),
# shared teamid will allow apps to communicate with each other
# (e.g. youtube, ytmusic, google docs)
if args.b is None:
    BUNDLE = f"fyi.zxcvbn.appdupe.{uuid4().hex[:10]}"  # type: ignore
elif len(args.b) != 10:
    quit("[!] -b argument has invalid length (see README)")
elif any(c not in "0123456789abcdef" for c in args.b):
    quit("[!] -b argument is invalid (see README)")
else:
    BUNDLE = f"fyi.zxcvbn.appdupe.{args.b}"  # type: ignore

print(f"[*] using seed: \"{args.s}\" (save this!)")
print(f"[*] will use bundle id: {BUNDLE} (save this!)")
print(f"[*] will use team id: {TEAM_ID}")

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

    # some IPAs have no entitlements, so just use empty dict in this case
    try:
        entitlements = plistlib.loads(ENT_PROC.stdout)
    except Exception:
        entitlements = {}

    # step 4: modify everything lol
    plist["CFBundleIdentifier"] = BUNDLE
    for key in ["UISupportedDevices", "CFBundleURLTypes"]:
        if key in plist:
            del plist[key]

    entitlements["application-identifier"] = f"{TEAM_ID}.{BUNDLE}"
    entitlements["com.apple.developer.team-identifier"] = TEAM_ID
    entitlements["keychain-access-groups"] = [BUNDLE_TI]
    entitlements["com.apple.security.application-groups"] = [
        f"group.{BUNDLE_TI}"]

    # we don't want duped apps having associated applinks
    if "com.apple.developer.associated-domains" in entitlements:
        del entitlements["com.apple.developer.associated-domains"]

    # step 5: write entitlements back to executable
    with open(ENT_PATH, "wb") as f:
        plistlib.dump(entitlements, f)  # type: ignore

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
    # for key in (EXEC_IPATH, PLIST_PATH):
    #     subprocess.run(
    #         ["zip", "-d", OUTPUT, key], stdout=subprocess.DEVNULL)

    subprocess.run(
        [
            "zip", "-d", OUTPUT, EXEC_IPATH, PLIST_PATH,
            "Payload/*/PlugIns/*", "Payload/*/Extensions/*"  # see README
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    with ZipFile(OUTPUT, "a") as zf:
        zf.write(EXEC_PATH, EXEC_IPATH)
        with zf.open(PLIST_PATH, "w") as f:
            plistlib.dump(plist, f)

    shutil.move(OUTPUT, args.o)

print("[*] done, remember to remove app extensions (if u wanna)")

