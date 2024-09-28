# appdupe
a cli tool to duplicate iOS apps "correctly"

## requirements
python v3.8 or later, the `zip` command, and [ldid](https://github.com/ProcursusTeam/ldid) installed globally. installing [pyzule](https://github.com/asdfzxcvbn/pyzule) is an easy way to get this taken care of.

windows is not supported. use wsl.

## usage
```shell
$ python appdupe.py -h
usage: appdupe.py [-h] -i input -o output [-s seed] [-b id]

a cli tool to duplicate ios apps

options:
  -h, --help  show this help message and exit
  -i input    ipa to duplicate
  -o output   duplicated ipa to create
  -s seed     a "seed" to derive the app id from (any string of your choosing)
  -b id       bundle id to use (see README)
```

## notes
you can use `-s` to ensure multiple apps share the same data container. an example where this can be useful can be [found in the code](https://github.com/asdfzxcvbn/appdupe/blob/d6711fde846ea9c9be3d133b2b82299fa3675d04/appdupe.py#L45).

this is really messy. i made this without caring about quality so there's probably some bugs.. who cares though, it works, doesn't it?

~~also, there might be some remaining shared app containers due to app extensions. you can use [pyzule](https://github.com/asdfzxcvbn/pyzule) to remove app extensions, change the app display name, and modify the app further.~~

appdupe now forcibly removes app extensions since keeping them causes issues.

## updating duped apps
let's think of this example: you need to duplicate discord, so you run this command:

```shell
$ python appdupe.py -i ~/Discord-v217.0.ipa -o ~/DiscordDupe
[?] ipa file extension not detected, appending manually
[*] using seed: "7c54c5db-d6c3-41f7-a5ab-c21d87e3e4e2" (save this!)
[*] will use bundle id: fyi.zxcvbn.appdupe.700603c620 (save this!)
[*] will use team id: 1429A9E38A
[*] done, remember to remove app extensions (if u wanna)
```

everything works fine! but what if you wanted to update the duped discord? starting in v1.1 you can use -s and -b to achieve this. simply remember to save the command's output (like appdupe tells you to) then run:

```shell
# "700603c620" was the last part of the bundle id given to us last time
$ python appdupe.py -i ~/Discord-v218.0.ipa -o ~/DiscordDupeUpdated -s "7c54c5db-d6c3-41f7-a5ab-c21d87e3e4e2" -b 700603c620
[?] ipa file extension not detected, appending manually
[*] using seed: "7c54c5db-d6c3-41f7-a5ab-c21d87e3e4e2" (save this!)
[*] will use bundle id: fyi.zxcvbn.appdupe.700603c620 (save this!)
[*] will use team id: 1429A9E38A
[*] done, remember to remove app extensions (if u wanna)
```

then you can install the updated ipa normally, and you'll keep all your data.
