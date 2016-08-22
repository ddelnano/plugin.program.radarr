# -*- coding: utf-8 -*-
import requests
import xbmc, xbmcaddon, xbmcgui, xbmcplugin

from resources.lib.sonarr_api import SonarrAPI
from resources.lib._json import write_json, read_json, get_appended_path,\
    dir_db, dir_shows

addonID = "plugin.program.sonarr"
addon = xbmcaddon.Addon(id=addonID)
fanart = ''
pluginhandle = int(sys.argv[1])
loglevel = 1
log_msg = addonID + ' - '


base_url = addon.getSetting('base-url')
api_key = addon.getSetting('api-key')


vw_moni, vw_perc, vw_total = False, False, False
if addon.getSetting('view-moni') == 'true': vw_moni = True
if addon.getSetting('view-perc') == 'true': vw_perc = True
if addon.getSetting('view-total') == 'true': vw_total = True


# check if ends with '/'
host_url = base_url + '/api'


snr = SonarrAPI(host_url, api_key)



def root():
    addDir(get_translation(30005), '', 'getAllShows', '', '', '')


def list_shows(data):
    for show in data:
        name = show['title'].encode('utf-8')
        thumb = host_url + show['images'][2]['url'] + '&apikey={}'.format(api_key)
        banner = host_url + show['images'][1]['url'] + '&apikey={}'.format(api_key)
        fanart = host_url + show['images'][0]['url'] + '&apikey={}'.format(api_key)
        show_id = show['id']
        seasons = show['seasons']
        dir_show = get_appended_path(dir_shows, str(show_id))
        file = 'seasons.json'
        file_path = get_appended_path(dir_show, file)
        write_json(file_path, seasons)
        addDir(name, show_id, 'getShow', thumb, fanart, '')


def list_seasons(show_id):
    dir_show = get_appended_path(dir_shows, str(show_id))
    file_db = get_appended_path(dir_show, 'seasons.json')
    data = read_json(file_db)
    xbmc.log('DATA LIST SEASON')
    xbmc.log(str(data))
    for season in data:
        name = get_season_name(season)
        season_id = season['seasonNumber']
        #name = 'Season %s' % str(season_id).zfill(2)
        addDir(name, show_id, 'getSeason', '', '', '', '', season_id)


def list_season(show_id, season_id):
    dir_show = get_appended_path(dir_shows, str(show_id))
    file_db = get_appended_path(dir_show, 'episodes.json')
    data = read_json(file_db)
    for episode in data:
        if episode['seasonNumber'] != int(season_id):
            continue
        else:
            name = str(episode['episodeNumber']).zfill(2)
            name += ' ' + episode['title'].encode('utf-8')
            addDir(name, '', '', '', '', '')


def get_season_name(season):
    season_id = season['seasonNumber']
    name = get_translation(30020)
    name += str(season_id).zfill(2)
    # Get percentage
    if vw_perc:
        perc = int(season['statistics']['percentOfEpisodes'])
        if perc == 100:
            perc = '[COLOR FF3576F9]{}%[/COLOR]'.format(perc)  # blue
        elif 50 <= perc < 100:
            perc = '[COLOR FFFA7544]{}%[/COLOR]'.format(perc)  # yellow
        elif perc < 50:
            perc = '[COLOR FFF7290A]{}%[/COLOR]'.format(perc)  # red
        name += ' ' + str(perc)
    if vw_total:
        epi_count = str(season['statistics']['episodeCount'])
        epi_total_count = str(season['statistics']['totalEpisodeCount'])
        name += ' {}/{} '.format(epi_count, epi_total_count)
    # get monitor stats
    if vw_moni:
        xbmc.log('VW MONI TRUE')
        if season['monitored'] == 'false':
            name += '[COLOR FF494545]%s[/COLOR]' % get_translation(30025)
        else:
            name += '[COLOR FF494545]%s[/COLOR]' % get_translation(30026)
    else:
        xbmc.log('VW MONI FALSE')

    return name


def get_show(show_id):
    list_seasons(show_id)
    get_all_episodes(show_id)


def get_all_shows():
    data = snr.get_series()
    ord_data = sorted(data, key=lambda k: k['title'])   # order title alphabetically
    list_shows(ord_data)


def get_all_episodes(show_id):
    data = snr.get_episodes_by_series_id(show_id)
    dir_show = get_appended_path(dir_shows, str(show_id))
    file_db = get_appended_path(dir_show, 'episodes.json')
    write_json(file_db, data)



def addDir(name, url, mode, iconimage, fanart, extra1, desc='', season=''):
    u = sys.argv[0] + "?url=" + str(url) + "&mode=" + str(mode) + "&name=" + str(name)# + "&extra1=" + extra1
    if season != '':
        u += "&season=" + str(season)
    ok = True
    item = xbmcgui.ListItem(name)
    item.setInfo(type="video", infoLabels={"title": name})
    item.setArt({'thumb': iconimage, 'fanart': fanart})
    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=item, isFolder=True)


def get_translation(string_id):
    return addon.getLocalizedString(string_id)


def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')
name = params.get('name')
season = params.get('season')
if type(url) == type(str()):
    url = str(url)



if mode == 'getAllShows':
    get_all_shows()
elif mode == 'getShow':
    get_show(url)
elif mode == 'getSeason':
    list_season(url, season)
else:
    root()

xbmcplugin.endOfDirectory(pluginhandle)
