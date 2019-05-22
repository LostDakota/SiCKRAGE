#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
#  This file is part of SiCKRAGE.
#
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import convert_size, try_int, bs4_parser
from sickrage.providers import TorrentProvider


class ExtraTorrentProvider(TorrentProvider):
    def __init__(self):
        super(ExtraTorrentProvider, self).__init__("ExtraTorrent", 'https://extratorrent.si', False)

        self.urls.update({
            'search': '{base_url}/search/'.format(**self.urls)
        })

        self.minseed = None
        self.minleech = None

        self.cache = TVCache(self)

    def search(self, search_strings, age=0, show_id=None, episode_id=None, **kwargs):
        results = []

        if not self.login():
            return results

        # Search Params
        search_params = {
            'page': 1,
            's_cat': 8,
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)
                    search_params['search'] = search_string

                try:
                    while search_params['page'] < 11:
                        data = self.session.get(self.urls['search'], params=search_params).text
                        results += self.parse(data, mode)
                        search_params['page'] += 1
                except Exception:
                    sickrage.app.log.debug("No data returned from provider")

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        with bs4_parser(data) as html:
            torrent_table = html.find('table', class_='tl')
            torrent_rows = torrent_table.find_all('tr')

            # Continue only if at least one Release is found
            if len(torrent_rows) < 2:
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            for result in torrent_rows[2:]:
                cells = result('td')
                if len(cells) < 8:
                    continue

                try:
                    title = cells[2].find('a').get_text(strip=True)
                    download_url = cells[0].find_all('a')[1].get('href')
                    if not (title and download_url):
                        continue

                    seeders = try_int(cells[5].get_text(strip=True), 0)
                    leechers = try_int(cells[6].get_text(strip=True), 0)

                    torrent_size = cells[4].get_text()
                    size = convert_size(torrent_size, -1, ['B', 'KIB', 'MIB', 'GIB', 'TIB', 'PIB'])

                    results += [{
                        'title': title,
                        'link': download_url,
                        'size': size,
                        'seeders': seeders,
                        'leechers': leechers
                    }]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error('Failed parsing provider.')

        return results
