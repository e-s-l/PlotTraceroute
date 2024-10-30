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

########################
#
# TODO
#   objectify the output into a hop w props: ip_ends, ms, number
#   first line of trace route is being counted but shouldnt be so pre check for formatting
#   map out to centre or something, or be cyclic at least
#

#########################
## LOGGER CONFIGURATION #
#########################

# the log output file, should be /var/log/something or /tmp/something
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

##########
## MAIN ##
##########

geod = Geod(ellps="WGS84")

def runner(dest: str) -> None:
    """
    the main/runner function given the server to trace to

    :param dest:
    :return: None
    """
    logger.info("in main")

    # trace_route to return an array of IPs
    ip_array = trace_route(dest)
    logger.info(ip_array)

    # geolocate to convert IPs to coords
    ip_locations = geolocate(ip_array)
    logger.info(ip_locations)

    # show_map to plot coords and arcs
    show_map(ip_locations, dest)

def show_map(locations: list, dest: str) -> None:
    """

    :param locations:
    :param dest:
    :return:
    """


    m = Basemap(llcrnrlon=0, llcrnrlat=-80, urcrnrlon=360, urcrnrlat=80, projection='mill')
    fig = plt.figure(figsize=(8, 4.5))
    m.drawcoastlines(linewidth=1.25)
    m.fillcontinents(color='0.8')
    m.drawparallels(np.arange(-85,85,20),labels=[1,1,0,0])
    m.drawmeridians(np.arange(0,360,60),labels=[0,0,0,1])

    locations = [(float(lat), float(lon)) for lat, lon in locations]

    for i in range(len(locations) - 1):

        start = locations[i]
        end = locations[i + 1]

        x_start, y_start = m(start[1], start[0])
        x_end, y_end = m(end[1], end[0])
        print(f"{x_end} {y_end}")

        m.plot(x_start, y_start, 'bo', markersize=4)
        m.plot(x_end, y_end, 'bo', markersize=4)

        lonlats = geod.npts(start[1], start[0], end[1], end[0], 200)
        x, y = m([lon for lon, lat in lonlats], [lat for lon, lat in lonlats])

        m.plot(x, y, 'r-', linewidth=2)

    plt.title(f'traceroute to {dest}')
    plt.show()

def geolocate(ip_list: list) -> list:
    """

    :param ip_list:
    :return:
    """

    ip_locations = []

    for ips in ip_list:
        for ip in ips:
            if ip is not None:
                url = f'http://ipinfo.io/{ip}?token={api_token}'
                response = urlopen(url)
                data = json.load(response)

                try:
                    ip_locations.append(data['loc'].split(','))

                except Exception as e:
                    if data['bogon']:
                        logger.info("Caught a bogon.")
                    else:
                        logger.error(f"Exception: {e}")

    return ip_locations


def process_output(out: str) -> list:
    """

    :param out:
    :return:
    """

    # use regex as backup check but use known format of traceroute (tack flags) output

    ip = ""
    ipv4_pattern = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")

    outp = out.strip().split()

    num = outp[1]
    if type(num) is int:

        match = ipv4_pattern.findall(outp[2])
        if match:
            ip = match

        ms = outp[3]

        print (f"{num}, {ip}, {ms}")

    return ip

def trace_route(dest: str) -> list:
    """

    :param dest:
    :return:
    """

    route_ips = []

    tracert = f"traceroute {dest} -n -q 1 -w 1"

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
                ################
                # Extract IPS
                ################
                route_ips.append(process_output(output))

        # get any stderr:
        stderr = proc.communicate()[1]
        if stderr:
            logger.error(stderr.strip())

    except subprocess.CalledProcessError as err:
        logger.error(f"Subprocess command error: {err.stderr}Return code: {err.returncode}")
    except Exception as exc:
        logger.error(f"Subprocess command exception: {exc}")

    return route_ips