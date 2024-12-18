#########################
#
#   Stupid simple plot of traceroute.
#   Get output, get IP, plot on basemap, get out.
#
#########################

import json                                     #
import logging                                  #
import re                                       #
import subprocess
import sys
from urllib.request import urlopen
import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.basemap import Basemap
from pyproj import Geod

# 
from src.config import *

#########################
#
# TODO
#   map out to centre or something, or be cyclic at least
#   make os-agnostic, ie, run traceroute or tracert depending on *nix or windows
#   turn plot points into plots hops which calls plots points and plot arcs (if more than one hop)
#
#########################

#########################
## LOGGER CONFIGURATION #
#########################


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)                          # set default level



# format of the log messages
debug_fmt = logging.Formatter("%(asctime)s-%(levelname)s: %(message)s", "%Y%m%d%H%M%S")
info_fmt = logging.Formatter(" %(message)s")

log_info = "info.log"
info_handler =  logging.FileHandler(log_info, 'w')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(info_fmt)


log_debug = "debug.log"
debug_handler =  logging.FileHandler(log_debug)
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(debug_fmt)

# set the format & make output go to stdout & the logfile
logger.addHandler(info_handler)                         # to the file
logger.addHandler(debug_handler)                        # to the file
logger.addHandler(logging.StreamHandler(sys.stdout))    # to standard out

###########
### Hop ###
###########

class Hop:
    """
    One output of the traceroute, a hop between servers...
    Characterised by hop number (from source to destination), end ip, and time (also from source to destination).
    """

    def __init__(self, num: int, ip: str, time: float):
        """
        :param num: The count of the hop
        :param ip:  The end IPv4 of the hop
        :param time: The time from source to hop-end
        """

        logger.debug("initialising hop")

        self.num = num
        self.ip = ip
        self.time = time
        self.coords = []

        if type(self.ip) == str:
            self.geolocate(self.ip)

    def geolocate(self, ip: str):
        """
        Given an IPv4 address, use a common API to geolocate it.

        :param ip:
        :return:
        """

        if ip is not None:
            url = f'http://ipinfo.io/{ip}?token={api_token}'
            response = urlopen(url)
            data = json.load(response)
            try:
                if 'bogon' in data:
                    logger.info("caught a bogon")
                else:
                    self.set_coords(data['loc'].split(','))
            except KeyError | Exception as e:
                logger.error(f"geolocation error: {e}")

    ###########
    # setters #
    ###########

    def set_coords(self, coords: list) -> None:
        """
        :param coords: the list of lat & long to assign to the (end of the) hop
        """

        self.coords = coords

    ###########
    # getters #
    ###########

    def get_num(self) -> int:
        return self.num

    def get_ip(self) -> str:
        return self.ip

    def get_time(self) -> float:
        return self.time

    def get_coords(self) -> list:
        return self.coords

###############
### BaseMap ###
###############

class Map:
    """
    The basemap plot/graph to display the hops and joining arcs.
    """

    def __init__(self, dest: str):
        """
        :param dest:
        """

        logger.debug("initialising map")

        self.plt = None
        self.fig = None
        self.m = None
        self.hops = []
        self.g = Geod(ellps="WGS84")
        self.dest = dest
        self.plot_delay = 0.1

        # These ought to be first point +/- 180
        self.lon_min = -180
        self.lon_max = 180

        self.set_up()

    def set_up(self):
        """
        Construct the basemap.
        """

        self.m = Basemap(llcrnrlon=self.lon_min, llcrnrlat=-90,
                         urcrnrlon=self.lon_max, urcrnrlat=90, projection='mill')

        self.fig = plt.figure(figsize=(12, 8))
        self.m.drawcoastlines(linewidth=1.25)
        self.m.fillcontinents(color='0.9')
        self.m.drawparallels(np.arange(-90, 90, 30), labels=[1, 1, 0, 0])
        self.m.drawmeridians(np.arange(0, 360, 60), labels=[0, 0, 0, 1])

    def show_map(self):
        """
        Display the map.
        """

        plt.title(f'traceroute to {self.dest}')
        plt.show()


    def add_hop(self, hop: Hop):
        """

        :param hop:
        """

        if hop.get_coords() and hop.get_coords() != ["", ""]:
            self.hops.append(hop)

           # logger.debug(f"added hop to {coords}")

        self.plot_hops()

    def plot_hops(self):

        self.plot_hop_point()

        if len(self.hops) > 1:
            #
            self.plot_arcs()

        #
        plt.draw()
        plt.pause(self.plot_delay)

    def plot_hop_point(self):

        locations = get_valid_locations(self.hops)

        # plot the points
        for i in range(len(locations) - 1):

            start = locations[i]
            end = locations[i + 1]

            x_start, y_start = self.m(start[1], start[0])
            x_end, y_end = self.m(end[1], end[0])
            print(f"{x_end} {y_end}")

            self.m.plot(x_start, y_start, 'bo', markersize=4)
            self.m.plot(x_end, y_end, 'bo', markersize=4)

    def plot_arcs(self):

        locations = get_valid_locations(self.hops)

        for i in range(len(locations) - 1):
            start = locations[i]
            end = locations[i + 1]

            start_lat, start_lon = start
            end_lat, end_lon = end

            if abs(start_lon - end_lon) > self.lon_max:

                if start_lon > end_lon:

                    lonlats1 = self.g.npts(start_lon, start_lat, self.lon_max,
                                           start_lat + (end_lat - start_lat)
                                           * (self.lon_max - start_lon) / (
                                                   end_lon - start_lon), 100)
                    lonlats2 = self.g.npts(-self.lon_min, end_lat +
                                           (start_lat - end_lat) * (360 + start_lon) / (
                                                   end_lon - start_lon), end_lon, end_lat, 100)
                else:
                    lonlats1 = self.g.npts(start_lon, start_lat,
                                           self.lon_min, start_lat + (end_lat - start_lat)
                                           * (start_lon + self.lon_max) / (
                                                   end_lon - start_lon), 100)

                    lonlats2 = self.g.npts(self.lon_max,
                                           end_lat + (start_lat - end_lat) *
                                           (360 - end_lon) / (end_lon - start_lon),
                                           end_lon, end_lat, 100)

                x1, y1 = self.m([lon for lon, lat in lonlats1],
                                [lat for lon, lat in lonlats1])
                x2, y2 = self.m([lon for lon, lat in lonlats2],
                                [lat for lon, lat in lonlats2])

                self.m.plot(x1, y1, 'r--')
                self.m.plot(x2, y2, 'r--')

            else:
                lonlats = self.g.npts(start_lon, start_lat,
                                      end_lon, end_lat, 100)
                x, y = self.m([lon for lon, lat in lonlats],
                              [lat for lon, lat in lonlats])
                self.m.plot(x, y, 'r--')


###########
# utility #
###########

def get_valid_locations(hops: list) -> list:

    # the 3 following checks can probably be merged
    points = []

    for hop in hops:
        points.append(hop.get_coords())

    valid_points = [(lat, lon) for lat, lon in points if lat and lon]

    if not valid_points:
        logger.debug("no valid points to plot")
        return []

    return [(float(lat), float(lon)) for lat, lon in valid_points]


def process_tr(tr_out: str) -> list:
    """
    Process each line of the traceroute and return valid.

    :param tr_out:
    :return:
    """

    outp = tr_out.strip().split()
    if not outp[0].isdigit():
        return [0, "", 0.0]

    ipv4_pattern = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
    ip = ipv4_pattern.findall(outp[1])

    ms = outp[2] if len(outp) > 2 else "0"

    return [int(outp[0]), ip[0] if ip else "", float(ms) if ms else 0.0]


###############
### The App ###
###############

class VisualTraceRoute:
    """

    """

    def __init__(self, dest: str):
        """
        :param dest:
        """
        logger.debug("initialising vrt")

        self.dest = dest
        self.start()

    def start(self):
        """
        Start the traceroute and main process.
        """

        # init map
        m = Map(self.dest)

        # run tr
        logger.debug("starting traceroute")

        tracert = f"traceroute {self.dest} -n -q 1 -w 1"
        try:
            # open the process (better than run coz can pipe out stdout & stderr (treating as text))
            proc = subprocess.Popen(tracert, shell=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            while True:
                output = proc.stdout.readline()
                # check if finished (proc.poll will return an exit code)
                if output == '' and proc.poll() is not None:
                    break
                if output:
                    output = output.strip()

                    logger.info(output)

                    ##################
                    # process output #
                    ##################

                    [num, ip, time] = process_tr(output)

                    if num != 0 and ip and time != 0:
                        m.add_hop(Hop(num, ip, time))

            m.show_map()

            # get any stderr:
            stderr = proc.communicate()[1]
            if stderr:
                logger.error(stderr.strip())
        except subprocess.CalledProcessError as err:
            logger.error(f"Subprocess command error: {err.stderr}Return code: {err.returncode}")
        except Exception as e:
            logger.error(f"Exception: {e}")

############
### Main ###
############

def runner(dest: str) -> None:
    """
    The main/runner function given the server to trace to

    :param dest: The final server to aim for.
    """

    vrt = VisualTraceRoute(dest)
