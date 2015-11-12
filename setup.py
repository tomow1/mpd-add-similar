from distutils.core import setup

import os

def get_build():
    path = "./.build"
    
    if os.path.exists(path):
        fp = open(path, "r")
        build = eval(fp.read())
        if os.path.exists("./.increase_build"):
            build += 1
        fp.close()
    else:
        build = 1
    
    fp = open(path, "w")
    fp.write(str(build))
    fp.close()
    
    return unicode(build)

setup(
    name = "mpd-add-similar",
    version = "0.1." + get_build(),
    description = "Adds similar tracks to your MPD playlist",
    author = "Amr Hassan <amr.hassan@gmail.com>",
    author_email = "amr.hassan@gmail.com",
    license = "gpl",
    url = "https://launchpad.net/mpd-add-similar",
    scripts = ["mpd-add-similar"],
    py_modules = ["mpdaddsimilar"],
    #packages = [""],
    #data_files = [
    #    ("/usr/share/man/man1", ("scrobblethis.1.gz",)),
    #    ("/etc/xdg/scrobblethis", ("accounts.config",))
    #    ]
    )
    
