
#
#░█▀█░█░░░█▀█░▀█▀░░░▀█▀░█▀▄░█▀█░█▀▀░█▀▀░█▀▄░█▀█░█░█░▀█▀░█▀▀
#░█▀▀░█░░░█░█░░█░░░░░█░░█▀▄░█▀█░█░░░█▀▀░█▀▄░█░█░█░█░░█░░█▀▀
#░▀░░░▀▀▀░▀▀▀░░▀░░░░░▀░░▀░▀░▀░▀░▀▀▀░▀▀▀░▀░▀░▀▀▀░▀▀▀░░▀░░▀▀▀
#

from src.TraceRouteMap import *

destination = "uchile.cl" #"docs-space.phys.utas.edu.au"

if __name__ == "__main__":

    if len(sys.argv) > 1:
        destination = sys.argv[1]

    sys.exit(runner(destination))
