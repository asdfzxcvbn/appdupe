# appdupe
a cli tool to duplicate iOS apps "correctly"

## requirements
python v3.8 or later, the `zip` command, and [ldid](https://github.com/ProcursusTeam/ldid) installed globally. installing [pyzule](https://github.com/asdfzxcvbn/pyzule) is an easy way to get this taken care of.

windows is not supported. use wsl.

## usage
```shell
$ python appdupe.py -h
usage: appdupe.py [-h] -i input -o output [-s seed]

a cli tool to duplicate ios apps

options:
  -h, --help  show this help message and exit
  -i input    ipa to duplicate
  -o output   duplicated ipa to create
  -s seed     a "seed" to derive the app id from (any string of your choosing -- will always produce same output)
```

## notes
you can use `-s` to ensure multiple apps share the same data container. an example where this can be useful can be [found in the code](https://github.com/asdfzxcvbn/appdupe/blob/d6711fde846ea9c9be3d133b2b82299fa3675d04/appdupe.py#L45).

this is really messy. i made this without caring about quality so there's probably some bugs.. who cares though, it works, doesn't it?

also, there might be some remaining shared app containers due to app extensions. you can use [pyzule](https://github.com/asdfzxcvbn/pyzule) to remove app extensions, change the app display name, and modify the app further.

don't change the bundle id though.. not sure if that would break anything due to changing `application-identifier`. you can try if you want and tell me if it works, just open an issue or dm me on telegram or something.
