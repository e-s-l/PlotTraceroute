#########################
#
#   ▗  ▖ ▝              ▝▜      ▄▄▄▖                    ▗▄▄          ▗
#   ▝▖▗▘▗▄   ▄▖ ▗ ▗  ▄▖  ▐       ▐   ▖▄  ▄▖  ▄▖  ▄▖     ▐ ▝▌ ▄▖ ▗ ▗ ▗▟▄  ▄▖
#    ▌▐  ▐  ▐ ▝ ▐ ▐ ▝ ▐  ▐       ▐   ▛ ▘▝ ▐ ▐▘▝ ▐▘▐     ▐▄▄▘▐▘▜ ▐ ▐  ▐  ▐▘▐
#    ▚▞  ▐   ▀▚ ▐ ▐ ▗▀▜  ▐       ▐   ▌  ▗▀▜ ▐   ▐▀▀     ▐ ▝▖▐ ▐ ▐ ▐  ▐  ▐▀▀
#    ▐▌ ▗▟▄ ▝▄▞ ▝▄▜ ▝▄▜  ▝▄      ▐   ▌  ▝▄▜ ▝▙▞ ▝▙▞     ▐  ▘▝▙▛ ▝▄▜  ▝▄ ▝▙▞
#
#   Stupid simple plot of traceroute.
#   Get output, get IP, plot on basemap, get out.
#
#########################

import json
import logging
import re
import subprocess
import sys
from urllib.request import urlopen
import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.basemap import Basemap
from pyproj import Geod

from src.config import *

#########################
#
# TODO
#   map out to centre or something, or be cyclic at least
#
#########################

#########################
## LOGGER CONFIGURATION #
#########################

logfile = "test.log"
logger = logging.getLogger(__name__)

# format of the log messages
logfmt = logging.Formatter("%(asctime)s-%(levelname)s: %(message)s", "%Y%m%d%H%M%S")

# set the format & make output go to stdout & the logfile
logfile_handler = logging.FileHandler(logfile)
logfile_handler.setFormatter(logfmt)
logger.addHandler(logfile_handler)                      # to the file
logger.addHandler(logging.StreamHandler(sys.stdout))    # to standard out
logger.setLevel(logging.DEBUG)                          # set default level

################
#
################

class Hop:
    """

    """

    def __init__(self, num: int, ip: str, time: float):
        """

        :param num:
        :param ip:
        :param time:
        """

        logger.info("init hop")

        self.num = num
        self.ip = ip
        self.time = time
        self.coords = []

        if type(self.ip) == str:
            self.geolocate(self.ip)

    def geolocate(self, ip: str):
        """

        :param ip:
        :return:
        """

        if ip is not None:
            url = f'http://ipinfo.io/{ip}?token={api_token}'
            response = urlopen(url)
            data = json.load(response)
            try:
                if 'bogon' in data:
                    logger.info("Caught a bogon.")
                    self.set_coords(["", ""])
                else:
                    self.set_coords(data['loc'].split(','))
            except KeyError as e:
                logger.error(f"Geolocation error: {e}")

            print(self.coords)

    #########
    # setters

    def set_coords(self, coords: list) -> None:
        """

        :param coords:
        :return:
        """

        self.coords = coords

    #########
    # getters

    def get_num(self) -> int:
        return self.num

    def get_ip(self) -> str:
        return self.ip

    def get_time(self) -> float:
        return self.time

    def get_coords(self) -> list:
        return self.coords

################
#
################

class Map:

    def __init__(self, dest: str):
        """

        :param dest:
        """
        logger.info("init map")

        self.plt = None
        self.fig = None
        self.m = None
        self.pts = []
        self.geod = Geod(ellps="WGS84")

        self.dest = dest
        self.set_up()

    def set_up(self):
        """

        :return:
        """

        self.lon_min = -180
        self.lon_max = 180
        self.m = Basemap(llcrnrlon=self.lon_min, llcrnrlat=-90,
                         urcrnrlon=self.lon_max, urcrnrlat=90, projection='mill')

        self.fig = plt.figure(figsize=(12, 8))
        self.m.drawcoastlines(linewidth=1.25)
        self.m.fillcontinents(color='0.9')
        self.m.drawparallels(np.arange(-90, 90, 30), labels=[1, 1, 0, 0])
        self.m.drawmeridians(np.arange(0, 360, 60), labels=[0, 0, 0, 1])

    def show_map(self):
        """

        :return:
        """

        plt.title(f'traceroute to {self.dest}')
        plt.show()

    def plot_pts_v1(self, points: list):
        logger.info("plotting points")

        valid_points = [(lat, lon) for lat, lon in points if lat and lon]
        if not valid_points:
            logger.info("No valid points to plot.")
            return
        locations = [(float(lat), float(lon)) for lat, lon in valid_points]

        for i in range(len(locations) - 1):
            start = locations[i]
            end = locations[i + 1]

            x_start, y_start = self.m(start[1], start[0])
            x_end, y_end = self.m(end[1], end[0])
            print(f"{x_end} {y_end}")

            self.m.plot(x_start, y_start, 'bo', markersize=4)
            self.m.plot(x_end, y_end, 'bo', markersize=4)

            lonlats = self.geod.npts(start[1], start[0], end[1], end[0], 100)
            x, y = self.m([lon for lon, lat in lonlats], [lat for lon, lat in lonlats])
            self.m.plot(x, y, 'r--', linewidth=2)

    def plot_pts(self, points: list):
        """

        :param points:
        :return:
        """
        logger.debug("plotting points")

        valid_points = [(lat, lon) for lat, lon in points if lat and lon]

        if not valid_points:
            logger.info("No valid points to plot.")
            return

        locations = [(float(lat), float(lon)) for lat, lon in valid_points]

        for i in range(len(locations) - 1):
            start = locations[i]
            end = locations[i + 1]

            start_lat, start_lon = start
            end_lat, end_lon = end

            if abs(start_lon - end_lon) > self.lon_max:

                if start_lon > end_lon:

                    lonlats1 = self.geod.npts(start_lon, start_lat, self.lon_max,
                                              start_lat + (end_lat - start_lat) 
                                              * (self.lon_max - start_lon) / (
                                                      end_lon - start_lon), 100)
                    lonlats2 = self.geod.npts(-self.lon_min, end_lat + 
                    (start_lat - end_lat) * (360 + start_lon) / (
                            end_lon - start_lon), end_lon, end_lat, 100)
                else:
                    lonlats1 = self.geod.npts(start_lon, start_lat, 
                    self.lon_min, start_lat + (end_lat - start_lat) 
                                              * (start_lon + self.lon_max) / (
                                                      end_lon - start_lon), 100)

                    lonlats2 = self.geod.npts(self.lon_max,
                                              end_lat + (start_lat - end_lat) * (360 - end_lon) / (end_lon - start_lon),
                                              end_lon, end_lat, 100)

                x1, y1 = self.m([lon for lon, lat in lonlats1], 
                [lat for lon, lat in lonlats1])
                x2, y2 = self.m([lon for lon, lat in lonlats2],
                 [lat for lon, lat in lonlats2])

                self.m.plot(x1, y1, 'r--')
                self.m.plot(x2, y2, 'r--')

            else:
                lonlats = self.geod.npts(start_lon, start_lat,
                 end_lon, end_lat, 100)
                x, y = self.m([lon for lon, lat in lonlats],
                 [lat for lon, lat in lonlats])
                self.m.plot(x, y, 'r--')


    def add_hop(self, hop: Hop):
        """

        :param hop:
        :return:
        """

        coords = hop.get_coords()

        if coords and coords != ["", ""]:
            self.pts.append(coords)
        if len(self.pts) > 1:
            self.plot_pts(self.pts)

            plt.draw()
            plt.pause(0.1)

        logger.debug(f"adding hop, coords: {coords}")

################
#
################

def process_tr(tr_out: str) -> list:
    """

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


################
#
################

class VisualTraceRoute:
    """

    """

    def __init__(self, dest: str):
        """

        :param dest:
        """
        logger.debug("init vrt")

        self.dest = dest
        self.start()

    def start(self):
        """

        :return:
        """

        # init map
        m = Map(self.dest)

        # run tr
        logger.debug("starting traceroute")

        tracert = f"traceroute {self.dest} -n -q 1 -w 1"
        try:
            # open the process (better than run coz can pipe out stdout & stderr (treating as text))
            proc = subprocess.Popen(tracert, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while True:
                output = proc.stdout.readline()
                # check if finished (proc.poll will return an exit code)
                if output == '' and proc.poll() is not None:
                    break
                if output:
                    print(output)

                    ###############
                    # extract ips #
                    ###############

                    [num, ip, time] = process_tr(output)

                    if num != 0 and ip and time != 0:
                        logger.info(f"{num} {ip} {time} !!!")
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

################
# main
################

def runner(dest: str) -> None:
    """
    the main/runner function given the server to trace to

    :param dest:
    :return: None
    """

    logger.debug("running")

    vrt = VisualTraceRoute(dest)
