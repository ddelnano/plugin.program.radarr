# -*- coding: utf-8 -*-
import requests
import xbmc, xbmcaddon, xbmcgui, xbmcplugin

from resources.lib.sonarr_api import SonarrAPI


addonID = "plugin.program.sonarr"
addon = xbmcaddon.Addon(id=addonID)
fanart = ''
pluginhandle = int(sys.argv[1])
loglevel = 1
log_msg = addonID + ' - '


base_url = addon.getSetting('base-url')
api_key = addon.getSetting('api-key')

# check if ends with '/'
host_url = base_url + '/api'


snr = SonarrAPI(host_url, api_key)



def root():
    addDir('TV Shows', '', 'getAllShows', '', '', '')



def list_shows(data):
    for show in data:
        name = show['title'].encode('utf-8')
        thumb = host_url + show['images'][2]['url'] + '&apikey={}'.format(api_key)
        banner = host_url + show['images'][1]['url'] + '&apikey={}'.format(api_key)
        fanart = host_url + show['images'][0]['url'] + '&apikey={}'.format(api_key)
        xbmc.log(thumb)
        xbmc.log(fanart)
        addDir(name, '', 'getShow', thumb, fanart, '')


def get_all_shows():
    data = snr.get_series()
    list_shows(data)



def addDir(name, url, mode, iconimage, fanart, extra1, desc=False):
    u = sys.argv[0] + "?url=" + str(url) + "&mode=" + str(mode) + "&name=" + str(name)
    ok = True
    item = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    item.setInfo(type="Video", infoLabels={"Title": name})
    item.setProperty('fanart_image', fanart)
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
if type(url) == type(str()):
    url = str(url)


if mode == 'getAllShows':
    get_all_shows()
else:
    root()

xbmcplugin.endOfDirectory(pluginhandle)
