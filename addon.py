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
vw_aired = False
if addon.getSetting('view-moni') == 'true': vw_moni = True
if addon.getSetting('view-perc') == 'true': vw_perc = True
if addon.getSetting('view-total') == 'true': vw_total = True
if addon.getSetting('view-aired') == 'true': vw_aired = True

if not base_url.endswith('/'):
    base_url += '/'
host_url = base_url + 'api'

snr = SonarrAPI(host_url, api_key)


def root():
    addDir(get_translation(30005), '', 'getAllShows', '', '', '')
    addDir(get_translation(30009), '', 'addShow', '', '', '')


def add_show(term=None):
    xbmc.log('term')
    xbmc.log(str(term))
    if not term:
        kb = xbmc.Keyboard()
        kb.doModal()
        if kb.isConfirmed() and kb.getText():
            term = kb.getText()
    # if user cancels, return
    if not term:
        return -1
    # show lookup
    shows = []
    data = snr.lookup_series(term)
    for show in data:
        shows.append(show['title'])
    if not shows:
        # NOTHING FOUND NOTIFICATION
        return -1
    # open dialog for choosing show
    dialog = xbmcgui.Dialog()
    ret = dialog.select(get_translation(30210), shows)
    if ret == -1:
        return -1
    xbmc.log('RET', level=0)
    xbmc.log(str(ret))
    # open dialog for choosing quality
    quality_profile_id = list_quality_profiles()
    if quality_profile_id == -1:
        return -1
    tvdbId = data[ret]['tvdbId']
    title = data[ret]['title']
    #seasons = data['seasons']
    data = {
        'tvdbId': tvdbId,
        'title': title,
        'qualityProfileId': quality_profile_id,
        'rootFolderPath': snr.get_root_folder()[0]['path'],
        # 'titleSlug': '',
        # 'seasons': [],
        'addOptions': {
            'ignoreEpisodesWithFile': 'true',
            'ignoreEpisodesWithoutFiles': 'true'
        }
    }
    snr.add_series(data)


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
    ret = dialog.select(get_translation(30211), profiles_key_list)
    if ret == -1:
        return -1
    id = profiles[ret]['id']
    return id


def add_new_show():
    return True


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
    for season in data:
        name = get_season_name(season)
        season_id = season['seasonNumber']
        addDir(name, show_id, 'getSeason', '', '', '', '', season_id)


def list_season(show_id):
    season_id = xbmc.getInfoLabel("ListItem.Season")
    dir_show = get_appended_path(dir_shows, str(show_id))
    file_db = get_appended_path(dir_show, 'episodes.json')
    data = read_json(file_db)
    for episode in data:
        if episode['seasonNumber'] != int(season_id):
            continue
        else:
            name = get_episode_name(episode)
            addDir(name, '', '', '', '', '', '', '', '')


def get_episode_name(episode):
    name = str(episode['seasonNumber']) + 'x'
    name += str(episode['episodeNumber']).zfill(2)
    if episode['hasFile']:
        name += ' [COLOR FF3576F9]%s[/COLOR] ' % episode['title']
    else:
        name += ' [COLOR FFF7290A]%s[/COLOR] ' % episode['title']
    if vw_aired and 'airDate' in episode:
        name += (' [COLOR FF494545]%s[/COLOR]' % episode['airDate'])
    return name.encode('utf-8')


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
    # get episodes counter
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



def addDir(name, url, mode, iconimage, fanart, extra1, desc='', season='', date=''):
    u = sys.argv[0] + "?url=" + str(url) + "&mode=" + str(mode) + "&name=" + str(name)# + "&extra1=" + extra1
    ok = True
    item = xbmcgui.ListItem(name)
    if date != '':
        item.setInfo(type="video", infoLabels={"aired": date})
    if season != '':
        item.setInfo(type="video", infoLabels={"season": season})
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
    list_season(url)
elif mode == 'addShow':
    add_show(url)
else:
    root()

xbmcplugin.endOfDirectory(pluginhandle)
