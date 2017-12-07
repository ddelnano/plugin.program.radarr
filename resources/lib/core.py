# -*- coding: utf-8 -*-
import sys
import requests
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import time

from resources.lib.radarr_api import RadarrAPI
from resources.lib.listing import add_entries, parameters_string_to_dict
from resources.lib._json import write_json, read_json, get_appended_path,\
     dir_db, dir_movies

addonID = "plugin.program.radarr"
addon = xbmcaddon.Addon(id=addonID)
fanart = ''
pluginhandle = int(sys.argv[1])
loglevel = 1
log_msg = addonID + ' - '
TRANSLATE = addon.getLocalizedString

base_url = addon.getSetting('base-url')
api_key = addon.getSetting('api-key')
addonicon = addon.getAddonInfo('path').decode('utf-8') + '/icon.png'
addonfanart = addon.getAddonInfo('path').decode('utf-8') + '/fanart.jpg'
xbmc.log("ICON " + str(addonicon))


vw_miss = False
if addon.getSetting('view-miss') == 'true': vw_miss = True

if not base_url.endswith('/'):
    base_url += '/'
host_url = base_url + 'api'

snr = RadarrAPI(host_url, api_key)


def root():
    mall_movies = {'name': TRANSLATE(30005), 'mode': 'getAllMovies', 'type': 'dir', 'images': {'thumb': addonicon, 'fanart': addonfanart}}
    madd_movie = {'name': TRANSLATE(30009), 'mode': 'addMovie', 'type': 'dir', 'images': {'thumb': addonicon, 'fanart': addonfanart}}
    msearch_missing = {'name': TRANSLATE(30010), 'mode': 'searchMissing', 'type': 'dir', 'images': {'thumb': addonicon, 'fanart': addonfanart}}
    mget_queue = {'name': TRANSLATE(30011), 'mode': 'getQueue', 'type': 'dir', 'images': {'thumb': addonicon, 'fanart': addonfanart}}
    main = [mall_movies, madd_movie, msearch_missing, mget_queue]
    add_entries(main)
    xbmcplugin.endOfDirectory(pluginhandle)


def add_movie(term=None):
    dialog = xbmcgui.Dialog()
    term = dialog.input('Add Movie', type=xbmcgui.INPUT_ALPHANUM)
    # if user cancels, return
    if not term:
        return -1
    # show lookup
    shows = []
    monitored = ''
    data = snr.lookup_movie(term)
    for show in data:
        shows.append(show['title'])
    if not shows:
        # NOTHING FOUND NOTIFICATION
        dialog.notification('Sonarr', 'No match was found for the movie "%s"' % term, addonicon, 5000)
        return -1
    # open dialog for choosing show
    dialog = xbmcgui.Dialog()
    ret = dialog.select(TRANSLATE(30210), shows)
    if ret == -1:
        return -1
    xbmc.log('RET', level=0)
    # open dialog for choosing quality
    quality_profile_id = list_quality_profiles()
    if quality_profile_id == -1:
        return -1
    tmdbId = data[ret]['tmdbId']
    title = data[ret]['title']
    year = data[ret]['year']
    titleSlug = data[ret]['titleSlug']
    images = data[ret]['images']
    data = {
        'title': title,
        'year': year,
        'qualityProfileId': quality_profile_id,
        'titleSlug': titleSlug,
        'tmdbId': tmdbId,
        'images': images,
        'rootFolderPath': snr.get_root_folder()[0]['path'],
        # 'titleSlug': '',
        # 'seasons': [],
        'addOptions': {
             'ignoreEpisodesWithFile': 'false',
             'ignoreEpisodesWithoutFiles': 'false',
             'searchForMovie': 'true'
        }
    }
    xbmc.log("DATASENT " + str(data))
    snr.add_movie(data)
    dialog.notification('Radarr', 'Added to watchlist: "%s"' % title, addonicon, 5000)
#    time.sleep(15)
#    search_missing()



def search_missing():
    data = {
        'name': 'missingMoviesSearch',
        'filterKey': 'monitored',
        'filterValue': 'true'
    }
    snr.search_missing(data)






def list_quality_profiles():
    profiles = []
    data = snr.get_quality_profiles()
    for profile in data:
        profile_id = profile['id']
        profile_name = profile['name']
        profiles.append({'name': profile_name, 'id': profile_id})
    profiles_key_list = []
    for profile in profiles:
        profiles_key_list.append(profile['name'])
    dialog = xbmcgui.Dialog()
    ret = dialog.select(TRANSLATE(30211), profiles_key_list)
    if ret == -1:
        return -1
    id = profiles[ret]['id']
    return id


def list_movies(data):
    shows = []
    for show in data:
        name = show['title'].encode('utf-8')
        if vw_miss:
            down = str(show['downloaded'])
            if down == 'True':
                name += ' [COLOR FF3576F9]Downloaded[/COLOR] '
            else:
                name += ' [COLOR FFF7290A]Missing[/COLOR] '
        thumb = host_url + show['images'][-2]['url'] + '&apikey={}'.format(api_key)
        #banner = host_url + show['images'][1]['url'] + '&apikey={}'.format(api_key)
        fanart = host_url + show['images'][0]['url'] + '&apikey={}'.format(api_key)
        show_id = show['id']
        seasons = 'na'
        dir_show = get_appended_path(dir_movies, str(show_id))
        file = 'seasons.json'
        file_path = get_appended_path(dir_show, file)
        write_json(file_path, seasons)
        shows.append({'name': name, 'url': str(show_id), 'mode': 'getShow', 'type': 'dir',
                      'images': {'thumb': thumb, 'fanart': fanart}})
    add_entries(shows)
    xbmcplugin.endOfDirectory(pluginhandle)


def get_all_movies():
    data = snr.get_movies()
    ord_data = sorted(data, key=lambda k: k['title'])   # order titles alphabetically
    list_movies(ord_data)

def get_queue():
    data = snr.get_queue()
    shows = []
    for show in data:
        name = show['movie']['title']
        thumb = show['movie']['images'][0]['url']
        fanart = show['movie']['images'][1]['url']
        totalsize = show['size'] * 1e-9
        perc = 100 - (100 * float(show['sizeleft'])/float(show['size']))
        name += '      [COLOR FF3576F9]%s%%[/COLOR] ' % round(perc, 1)
        name += ' [COLOR FF3576F9]of  %sGB[/COLOR] ' % round(totalsize, 2)
        show_id = show['id']
        seasons = 'na'
        dir_show = get_appended_path(dir_movies, str(show_id))
        file = 'seasons.json'
        file_path = get_appended_path(dir_show, file)
        write_json(file_path, seasons)
        shows.append({'name': name, 'url': str(show_id), 'mode': 'getShow', 'type': 'dir',
                      'images': {'thumb': thumb, 'fanart': fanart}})
    add_entries(shows)
    xbmcplugin.endOfDirectory(pluginhandle)




params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')
name = params.get('name')

if type(url) == type(str()):
    url = str(url)


if mode == None:
    root()
if mode == 'getAllMovies':
    get_all_movies()
elif mode == 'getMovie':
    get_movie(url)
elif mode == 'addMovie':
    add_movie(url)
elif mode == 'searchMissing':
    search_missing()
elif mode == 'getQueue':
    get_queue()
