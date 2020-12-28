import gettext

gettext.bindtextdomain('ddmd', localedir='locale')
gettext.textdomain('ddmd')
#translate = gettext.gettext
translate = lambda x: str(x)
